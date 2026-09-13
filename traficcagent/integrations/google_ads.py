"""Cliente para o servidor MCP do Google Ads (issue #6).

Sem GOOGLE_ADS_DEVELOPER_TOKEN e GOOGLE_ADS_CUSTOMER_ID configurados, o
cliente cai automaticamente em modo mock — devolve dados de campanha
determinísticos, suficientes para testar toda a lógica de #9 e #11 sem
depender de acesso real ao Google Ads.

TODO (bloqueado por credencial, ver issue #6): implementar `_run_real`
usando o pacote `mcp` para abrir uma sessão de stdio/SSE com o servidor
`googleads/google-ads-mcp` e executar a query GAQL de fato. A assinatura
pública (`GoogleAdsMCPClient.run_gaql`) já está estável — só o backend muda.
"""
from __future__ import annotations

from dataclasses import dataclass
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


class GoogleAdsMCPError(RuntimeError):
    pass


class MCPTransport(Protocol):
    """Contrato mínimo do adaptador MCP real ou de teste."""

    def call_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        ...


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
        if self.modo_mock:
            return self._run_mock(query)
        return self._run_real(query)

    def get_campanhas_ativas(self) -> list[CampanhaMetrics]:
        linhas = self.run_gaql(GAQL_CAMPANHAS_ATIVAS)
        return [
            CampanhaMetrics(
                nome=linha["campaign_name"],
                dias_ativa=linha["dias_ativa"],
                custo_total=linha["custo_total"],
                conversoes=linha["conversoes"],
            )
            for linha in linhas
        ]

    def _run_real(self, query: str) -> list[dict]:
        if self.transport is None:
            raise GoogleAdsMCPError(
                "Transporte MCP não configurado. Injete um adaptador "
                "googleads/google-ads-mcp para executar o modo real."
            )
        try:
            resposta = self.transport.call_tool(
                "google_ads_run_gaql",
                {"query": query},
            )
        except Exception as exc:
            raise GoogleAdsMCPError(
                f"Falha ao executar ferramenta MCP do Google Ads: {exc}"
            ) from exc
        return self._normalizar_resposta(resposta)

    @staticmethod
    def _normalizar_resposta(resposta: Any) -> list[dict]:
        """Aceita lista direta ou payload MCP com content/structuredContent."""
        if isinstance(resposta, list):
            return resposta
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
