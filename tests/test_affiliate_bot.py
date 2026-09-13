import httpx
import pytest

from traficcagent.config import BusinessRules, Settings
from traficcagent.integrations.affiliate_bot import AffiliateBotClient, AffiliateBotError


def _settings(with_credentials: bool) -> Settings:
    return Settings(
        google_ads_developer_token=None,
        google_ads_customer_id=None,
        affiliate_bot_api_key="fake-key" if with_credentials else None,
        affiliate_bot_base_url="https://botdoafiliado.com/api/v1/",
        anthropic_api_key=None,
        rules=BusinessRules(),
    )


def test_modo_mock_sem_api_key():
    client = AffiliateBotClient(settings=_settings(with_credentials=False))
    assert client.modo_mock

    metadados = client.obter_metadados("prod-1")
    assert metadados.produto_id == "prod-1"
    assert metadados.comissao_pct == 12.0

    link = client.gerar_link_rastreavel("prod-1", "https://mercadolivre.com.br/x")
    assert link.url_rastreavel.startswith("https://meli.la/mock-")


def test_modo_real_usa_x_api_key_e_faz_parse_da_resposta(monkeypatch):
    client = AffiliateBotClient(settings=_settings(with_credentials=True))
    assert not client.modo_mock

    def fake_get(url, headers=None, timeout=None):
        assert headers["X-API-Key"] == "fake-key"
        assert url.endswith("/products/prod-1")
        request = httpx.Request("GET", url)
        return httpx.Response(
            200,
            json={"name": "Fone Real", "price": 150.0, "commission_pct": 8.0},
            request=request,
        )

    monkeypatch.setattr(httpx, "get", fake_get)
    metadados = client.obter_metadados("prod-1")
    assert metadados.nome == "Fone Real"
    assert metadados.preco == 150.0


def test_modo_real_propaga_erro_http_como_affiliate_bot_error(monkeypatch):
    client = AffiliateBotClient(settings=_settings(with_credentials=True))

    def fake_get(url, headers=None, timeout=None):
        request = httpx.Request("GET", url)
        return httpx.Response(500, json={"error": "boom"}, request=request)

    monkeypatch.setattr(httpx, "get", fake_get)
    with pytest.raises(AffiliateBotError):
        client.obter_metadados("prod-1")
