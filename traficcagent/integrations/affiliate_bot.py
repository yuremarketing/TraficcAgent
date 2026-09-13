"""Cliente da API do Bot do Afiliado (issue #7).

Diferente do Google Ads (MCP), esta é uma API REST simples autenticada por
header `X-API-Key` — dá pra implementar a chamada real de verdade, só falta a
chave (BOT_AFILIADO_API_KEY). Sem a chave, o cliente cai em modo mock com
dados determinísticos para não travar o resto do pipeline em dev/CI.
"""
from __future__ import annotations

from dataclasses import dataclass

import httpx

from traficcagent.config import Settings, load_settings


class AffiliateBotError(RuntimeError):
    pass


@dataclass(frozen=True)
class MetadadosProduto:
    produto_id: str
    nome: str
    preco: float
    comissao_pct: float


@dataclass(frozen=True)
class LinkRastreavel:
    produto_id: str
    url_rastreavel: str


@dataclass
class AffiliateBotClient:
    settings: Settings
    timeout_s: float = 10.0

    @classmethod
    def from_env(cls) -> "AffiliateBotClient":
        return cls(settings=load_settings())

    @property
    def modo_mock(self) -> bool:
        return not self.settings.has_affiliate_bot_credentials

    def _headers(self) -> dict:
        return {"X-API-Key": self.settings.affiliate_bot_api_key or ""}

    def obter_metadados(self, produto_id: str) -> MetadadosProduto:
        if self.modo_mock:
            return self._mock_metadados(produto_id)

        url = f"{self.settings.affiliate_bot_base_url.rstrip('/')}/products/{produto_id}"
        try:
            resp = httpx.get(url, headers=self._headers(), timeout=self.timeout_s)
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            raise AffiliateBotError(f"Falha ao buscar metadados de {produto_id}: {exc}") from exc

        data = resp.json()
        return MetadadosProduto(
            produto_id=produto_id,
            nome=data["name"],
            preco=float(data["price"]),
            comissao_pct=float(data["commission_pct"]),
        )

    def gerar_link_rastreavel(self, produto_id: str, url_original: str) -> LinkRastreavel:
        if self.modo_mock:
            return self._mock_link(produto_id, url_original)

        url = f"{self.settings.affiliate_bot_base_url.rstrip('/')}/links"
        try:
            resp = httpx.post(
                url,
                headers=self._headers(),
                json={"product_id": produto_id, "url": url_original},
                timeout=self.timeout_s,
            )
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            raise AffiliateBotError(f"Falha ao gerar link para {produto_id}: {exc}") from exc

        data = resp.json()
        return LinkRastreavel(produto_id=produto_id, url_rastreavel=data["tracked_url"])

    def _mock_metadados(self, produto_id: str) -> MetadadosProduto:
        return MetadadosProduto(
            produto_id=produto_id,
            nome=f"Produto mock {produto_id}",
            preco=100.0,
            comissao_pct=12.0,
        )

    def _mock_link(self, produto_id: str, url_original: str) -> LinkRastreavel:
        return LinkRastreavel(
            produto_id=produto_id,
            url_rastreavel=f"https://meli.la/mock-{produto_id}",
        )
