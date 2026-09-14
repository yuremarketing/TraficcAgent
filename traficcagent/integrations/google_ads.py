"""Cliente para o servidor MCP oficial do Google Ads (issue #6).

Sem GOOGLE_ADS_DEVELOPER_TOKEN e GOOGLE_ADS_CUSTOMER_ID configurados, o
cliente cai automaticamente em modo mock — devolve dados de campanha
determinísticos, suficientes para testar toda a lógica de #9 e #11 sem
depender de acesso real ao Google Ads.

O transporte oficial é opcional no import: o projeto continua executável em
modo mock, mas com credenciais e o pacote ``mcp`` abre uma sessão stdio ou
Streamable HTTP e chama a ferramenta oficial ``search``.
"""
from __future__ import annotations

from dataclasses import dataclass
import logging
import re
import time
from typing import Any, Protocol

from traficcagent.config import Settings, load_settings
from traficcagent.core.traffic_manager import CampanhaMetrics

# Query de leitura de campanhas usada por get_campanhas(). Mantida como
# constante para já documentar o GAQL que o backend real vai precisar rodar.
GAQL_CAMPANHAS_ATIVAS = """
SELECT
  campaign.name,
  metrics.cost_micros,
  metrics.conversions,
  segments.date
FROM campaign
WHERE campaign.status = 'ENABLED'
"""
LOGGER = logging.getLogger(__name__)


class GoogleAdsMCPError(RuntimeError):
    pass


class MCPTransport(Protocol):
    """Contrato mínimo do adaptador MCP real ou de teste."""

    def call_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        ...


class OfficialGoogleAdsMCPTransport:
    """Adaptador síncrono para o SDK oficial MCP (stdio ou HTTP)."""

    def __init__(self, settings: Settings):
        self.settings = settings

    def call_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        endpoint = (self.settings.google_ads_mcp_url or "").strip()
        if self.settings.google_ads_mcp_transport != "stdio" and not endpoint:
            raise GoogleAdsMCPError("GOOGLE_ADS_MCP_URL é obrigatório no transporte HTTP.")
        try:
            import asyncio
            from mcp import ClientSession, StdioServerParameters
            from mcp.client.stdio import stdio_client
            from mcp.client.streamable_http import streamable_http_client
        except ImportError as exc:
            raise GoogleAdsMCPError("Dependência MCP ausente; instale mcp>=1.2.0.") from exc

        target = (StdioServerParameters(command=self.settings.google_ads_mcp_command, args=[])
                  if self.settings.google_ads_mcp_transport == "stdio" else endpoint)
        if not target:
            raise GoogleAdsMCPError("GOOGLE_ADS_MCP_URL é obrigatório no transporte HTTP.")

        async def invoke():
            if self.settings.google_ads_mcp_transport == "stdio":
                async with stdio_client(target) as (read, write):
                    async with ClientSession(read, write) as session:
                        await session.initialize()
                        return await session.call_tool(name, arguments)
            else:
                async with streamable_http_client(endpoint) as (read, write, _):
                    async with ClientSession(read, write) as session:
                        await session.initialize()
                        return await session.call_tool(name, arguments)

        return asyncio.run(invoke())


@dataclass
class GoogleAdsMCPClient:
    settings: Settings
    transport: MCPTransport | None = None

    @classmethod
    def from_env(cls) -> "GoogleAdsMCPClient":
        return cls(settings=load_settings())

    @property
    def modo_mock(self) -> bool:
        return not self.settings.has_google_ads_credentials

    def run_gaql(self, query: str) -> list[dict]:
        if not query.strip():
            raise GoogleAdsMCPError("Query GAQL não pode ser vazia.")
        if not self.validar_query_gaql(query):
            raise GoogleAdsMCPError("Query GAQL inválida.")
        if self.modo_mock:
            LOGGER.info("Google Ads em modo mock; consulta não enviada.")
            return self._run_mock(query)
        LOGGER.info("Executando consulta GAQL via transporte MCP configurado.")
        return self._run_real(query)

    def get_campanhas_ativas(self) -> list[CampanhaMetrics]:
        linhas = self.run_gaql(GAQL_CAMPANHAS_ATIVAS)
        return [self._extrair_metrica_campanha(linha) for linha in linhas]

    @staticmethod
    def _extrair_metrica_campanha(linha: dict) -> CampanhaMetrics:
        nome = (
            linha.get("campaign_name")
            or linha.get("campaign.name")
            or (linha.get("campaign") or {}).get("name")
            or "Campanha sem nome"
        )
        conversoes_raw = (
            linha.get("conversoes")
            or linha.get("metrics.conversions")
            or (linha.get("metrics") or {}).get("conversions")
            or 0
        )
        try:
            conversoes = int(float(conversoes_raw))
        except (ValueError, TypeError):
            conversoes = 0

        if "custo_total" in linha:
            custo_total = float(linha["custo_total"])
        elif "metrics.cost_micros" in linha or (isinstance(linha.get("metrics"), dict) and "cost_micros" in linha["metrics"]):
            micros = float(linha.get("metrics.cost_micros") or linha["metrics"]["cost_micros"])
            custo_total = round(micros / 1_000_000.0, 2)
        elif "metrics.costMicros" in linha or (isinstance(linha.get("metrics"), dict) and "costMicros" in linha["metrics"]):
            micros = float(linha.get("metrics.costMicros") or linha["metrics"]["costMicros"])
            custo_total = round(micros / 1_000_000.0, 2)
        else:
            custo_total = 0.0

        if "dias_ativa" in linha:
            dias_ativa = int(linha["dias_ativa"])
        else:
            date_str = linha.get("segments.date") or (linha.get("segments") or {}).get("date")
            if date_str:
                try:
                    from datetime import date
                    dt = date.fromisoformat(str(date_str))
                    dias_ativa = max(1, (date.today() - dt).days)
                except Exception:
                    dias_ativa = 1
            else:
                dias_ativa = 1

        return CampanhaMetrics(
            nome=nome,
            dias_ativa=dias_ativa,
            custo_total=custo_total,
            conversoes=conversoes,
        )

    def _run_real(self, query: str) -> list[dict]:
        transport = self.transport or OfficialGoogleAdsMCPTransport(self.settings)
        tentativas = max(1, self.settings.google_ads_mcp_max_retries)
        for tentativa in range(tentativas):
            try:
                return self._call_and_normalize(transport, query)
            except Exception as exc:
                mensagem = str(exc).upper()
                recuperavel = any(chave in mensagem for chave in (
                    "429", "RATE", "TIMEOUT", "UNAVAILABLE", "RESOURCE_EXHAUSTED", "CONNECTION"
                ))
                if not recuperavel or tentativa == tentativas - 1:
                    raise GoogleAdsMCPError(
                        f"Falha ao executar ferramenta MCP do Google Ads: {exc}"
                    ) from exc
                LOGGER.warning("Falha transitória no MCP; reconectando (tentativa %s/%s).", tentativa + 1, tentativas)
                time.sleep(min(2 ** tentativa, 8))

        raise GoogleAdsMCPError("Falha inesperada no transporte MCP.")

    def _call_and_normalize(self, transport: MCPTransport, query: str) -> list[dict]:
        if self.settings.google_ads_mcp_tool == "search":
            argumentos = {
                "customer_id": self.settings.google_ads_customer_id,
                "fields": ["campaign.name", "metrics.cost_micros", "metrics.conversions", "segments.date"],
                "resource": "campaign",
                "conditions": ["campaign.status = 'ENABLED'"],
            }
        else:
            argumentos = {"query": query}
        resposta = transport.call_tool(self.settings.google_ads_mcp_tool, argumentos)
        return self._normalizar_resposta(resposta)

    @staticmethod
    def validar_query_gaql(query: str) -> bool:
        normalizada = re.sub(r"\s+", " ", query).strip().upper()
        return normalizada.startswith("SELECT ") and " FROM " in normalizada

    @staticmethod
    def _normalizar_resposta(resposta: Any) -> list[dict]:
        """Aceita lista direta ou payload MCP com content/structuredContent."""
        if isinstance(resposta, list):
            return resposta
        structured = getattr(resposta, "structured_content", None)
        if isinstance(structured, dict):
            resposta = structured
        elif isinstance(structured, list):
            return structured
        if isinstance(resposta, dict):
            if isinstance(resposta.get("structuredContent"), list):
                return resposta["structuredContent"]
            if isinstance(resposta.get("data"), list):
                return resposta["data"]
            content = resposta.get("content")
            if isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and isinstance(item.get("data"), list):
                        return item["data"]
        raise GoogleAdsMCPError(
            "Resposta MCP inválida: esperada uma lista de métricas de campanha."
        )

    def _run_mock(self, query: str) -> list[dict]:
        # Dataset fixo, só pra exercitar o pipeline ponta a ponta em dev/CI.
        return [
            {
                "campaign_name": "Fone Bluetooth XYZ",
                "dias_ativa": 5,
                "custo_total": 100.0,
                "conversoes": 4,
            },
            {
                "campaign_name": "Capinha Genérica",
                "dias_ativa": 3,
                "custo_total": 90.0,
                "conversoes": 0,
            },
        ]
