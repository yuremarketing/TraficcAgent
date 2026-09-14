"""Cliente da API do Bot do Afiliado (issue #7).

Diferente do Google Ads (MCP), esta é uma API REST simples autenticada por
header `X-API-Key` — dá pra implementar a chamada real de verdade, só falta a
chave (BOT_AFILIADO_API_KEY). Sem a chave, o cliente cai em modo mock com
dados determinísticos para não travar o resto do pipeline em dev/CI.
"""
from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse

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

    def converter_links(self, urls: list[str]) -> list[LinkRastreavel]:
        """Converte links em lotes de no máximo 150 URLs.

        A resposta real do Bot do Afiliado pode variar por versão; por isso a
        validação é feita antes de expor o resultado ao restante do pipeline.
        """
        if not urls:
            return []
        resultados: list[LinkRastreavel] = []
        for inicio in range(0, len(urls), 150):
            lote = urls[inicio:inicio + 150]
            if self.modo_mock:
                resultados.extend(
                    self._mock_link(str(inicio + indice), url)
                    for indice, url in enumerate(lote)
                )
                continue
            endpoint = f"{self.settings.affiliate_bot_base_url.rstrip('/')}/convert-links"
            try:
                resp = httpx.post(endpoint, headers=self._headers(), json={"urls": lote}, timeout=self.timeout_s)
                resp.raise_for_status()
                dados = resp.json()
                itens = dados.get("links", dados) if isinstance(dados, dict) else dados
                if not isinstance(itens, list):
                    raise AffiliateBotError("Resposta de conversão inválida: esperado um lote de links.")
                for item in itens:
                    if not isinstance(item, dict) or not item.get("tracked_url"):
                        raise AffiliateBotError("Resposta de conversão inválida: link rastreável ausente.")
                    resultados.append(LinkRastreavel(
                        produto_id=str(item.get("product_id", "")),
                        url_rastreavel=self._validar_url(item["tracked_url"]),
                    ))
            except (httpx.HTTPError, ValueError) as exc:
                raise AffiliateBotError(f"Falha ao converter lote de links: {exc}") from exc
        return resultados

    @staticmethod
    def _validar_url(url: str) -> str:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise AffiliateBotError("Link rastreável retornado não é uma URL válida.")
        return url

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
