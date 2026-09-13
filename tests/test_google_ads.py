import pytest

from traficcagent.config import Settings, BusinessRules
from traficcagent.integrations.google_ads import GoogleAdsMCPClient, GoogleAdsMCPError


def _settings(with_credentials: bool) -> Settings:
    return Settings(
        google_ads_developer_token="token" if with_credentials else None,
        google_ads_customer_id="123" if with_credentials else None,
        affiliate_bot_api_key=None,
        affiliate_bot_base_url="https://botdoafiliado.com/api/v1/",
        anthropic_api_key=None,
        rules=BusinessRules(),
    )


def test_modo_mock_sem_credenciais():
    client = GoogleAdsMCPClient(settings=_settings(with_credentials=False))
    assert client.modo_mock
    campanhas = client.get_campanhas_ativas()
    assert len(campanhas) == 2
    assert campanhas[0].nome == "Fone Bluetooth XYZ"
    assert campanhas[0].conversoes == 4


def test_modo_real_ainda_nao_implementado_mas_sinalizado():
    client = GoogleAdsMCPClient(settings=_settings(with_credentials=True))
    assert not client.modo_mock
    with pytest.raises(GoogleAdsMCPError):
        client.get_campanhas_ativas()
