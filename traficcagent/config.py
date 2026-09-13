"""Configuração central do TraficcAgent, lida a partir de variáveis de ambiente.

Nenhum valor default aqui é um segredo real — tudo vem do ambiente (.env local
ou variáveis injetadas no Cloud Run). Quando uma credencial não está presente,
os clientes de integração (google_ads, affiliate_bot) operam em modo mock,
permitindo testar a lógica de negócio sem depender de acesso externo.
"""
from __future__ import annotations

import os
from dataclasses import dataclass


def _get_float(name: str, default: float) -> float:
    value = os.environ.get(name)
    return float(value) if value else default


@dataclass(frozen=True)
class BusinessRules:
    """Regras de negócio descritas no README / artefatos."""

    comissao_minima_pct: float = 10.0
    alto_ticket_lucro_min: float = 40.0
    alto_ticket_lucro_max: float = 50.0
    early_stop_dias: int = 3
    maturacao_dias: int = 14
    conteudo_llm_pct: float = 90.0


@dataclass(frozen=True)
class Settings:
    google_ads_developer_token: str | None
    google_ads_customer_id: str | None
    affiliate_bot_api_key: str | None
    affiliate_bot_base_url: str
    anthropic_api_key: str | None
    rules: BusinessRules
    google_ads_mcp_transport: str = "stdio"
    google_ads_mcp_url: str | None = None
    google_ads_mcp_command: str = "google-ads-mcp"
    google_ads_mcp_tool: str = "search"
    google_ads_mcp_max_retries: int = 3

    @property
    def has_google_ads_credentials(self) -> bool:
        return bool(self.google_ads_developer_token and self.google_ads_customer_id)

    @property
    def has_affiliate_bot_credentials(self) -> bool:
        return bool(self.affiliate_bot_api_key)

    @property
    def has_llm_credentials(self) -> bool:
        return bool(self.anthropic_api_key)


def load_settings() -> Settings:
    return Settings(
        google_ads_developer_token=os.environ.get("GOOGLE_ADS_DEVELOPER_TOKEN"),
        google_ads_customer_id=os.environ.get("GOOGLE_ADS_CUSTOMER_ID"),
        affiliate_bot_api_key=os.environ.get("BOT_AFILIADO_API_KEY"),
        affiliate_bot_base_url=os.environ.get(
            "BOT_AFILIADO_BASE_URL", "https://botdoafiliado.com/api/v1/"
        ),
        anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY"),
        google_ads_mcp_transport=os.environ.get("GOOGLE_ADS_MCP_TRANSPORT", "stdio"),
        google_ads_mcp_url=os.environ.get("GOOGLE_ADS_MCP_URL"),
        google_ads_mcp_command=os.environ.get("GOOGLE_ADS_MCP_COMMAND", "google-ads-mcp"),
        google_ads_mcp_tool=os.environ.get("GOOGLE_ADS_MCP_TOOL", "search"),
        google_ads_mcp_max_retries=int(os.environ.get("GOOGLE_ADS_MCP_MAX_RETRIES", "3")),
        rules=BusinessRules(
            comissao_minima_pct=_get_float("COMISSAO_MINIMA_PCT", 10.0),
            alto_ticket_lucro_min=_get_float("ALTO_TICKET_LUCRO_MIN", 40.0),
            alto_ticket_lucro_max=_get_float("ALTO_TICKET_LUCRO_MAX", 50.0),
        ),
    )
