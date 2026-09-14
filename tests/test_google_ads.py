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


def test_query_gaql_valida():
    assert GoogleAdsMCPClient.validar_query_gaql("SELECT campaign.name FROM campaign")
    assert not GoogleAdsMCPClient.validar_query_gaql("")
    assert not GoogleAdsMCPClient.validar_query_gaql("DELETE FROM campaign")


def test_modo_real_sem_sdk_sinaliza_erro_claro(monkeypatch):
    client = GoogleAdsMCPClient(settings=_settings(with_credentials=True))
    assert not client.modo_mock
    monkeypatch.setattr("traficcagent.integrations.google_ads.OfficialGoogleAdsMCPTransport.call_tool", lambda *_: (_ for _ in ()).throw(ImportError("mcp")))
    with pytest.raises(GoogleAdsMCPError):
        client.get_campanhas_ativas()


class FakeMCPTransport:
    def __init__(self):
        self.calls = []

    def call_tool(self, name, arguments):
        self.calls.append((name, arguments))
        return {"structuredContent": [{"campaign_name": "Campanha real", "dias_ativa": 2, "custo_total": 12.5, "conversoes": 1}]}


def test_modo_real_usa_transporte_injetado():
    transport = FakeMCPTransport()
    client = GoogleAdsMCPClient(settings=_settings(with_credentials=True), transport=transport)
    campanhas = client.get_campanhas_ativas()
    assert campanhas[0].nome == "Campanha real"
    assert transport.calls[0][0] == "search"
    assert transport.calls[0][1]["resource"] == "campaign"
    assert transport.calls[0][1]["customer_id"] == "123"


def test_modo_real_transport_error_eh_convertido():
    class BrokenTransport:
        def call_tool(self, name, arguments):
            raise TimeoutError("tempo excedido")

    client = GoogleAdsMCPClient(settings=_settings(True), transport=BrokenTransport())
    with pytest.raises(GoogleAdsMCPError, match="Falha ao executar"):
        client.run_gaql("SELECT campaign.name FROM campaign")


def test_modo_real_resposta_vazia_eh_valida():
    class EmptyTransport:
        def call_tool(self, name, arguments):
            return []

    client = GoogleAdsMCPClient(settings=_settings(True), transport=EmptyTransport())
    assert client.run_gaql("SELECT campaign.name FROM campaign") == []


def test_modo_real_multiplas_campanhas():
    class ManyTransport:
        def call_tool(self, name, arguments):
            return [{"campaign_name": "A"}, {"campaign_name": "B"}]

    client = GoogleAdsMCPClient(settings=_settings(True), transport=ManyTransport())
    assert len(client.run_gaql("SELECT campaign.name FROM campaign")) == 2


def test_modo_real_rejeita_resposta_mcp_invalida():
    class InvalidTransport:
        def call_tool(self, name, arguments):
            return {"content": [{"type": "text", "text": "erro"}]}

    client = GoogleAdsMCPClient(settings=_settings(with_credentials=True), transport=InvalidTransport())
    with pytest.raises(GoogleAdsMCPError, match="Resposta MCP inválida"):
        client.get_campanhas_ativas()


def test_retry_em_timeout_e_depois_sucesso(monkeypatch):
    class FlakyTransport:
        def __init__(self):
            self.calls = 0

        def call_tool(self, name, arguments):
            self.calls += 1
            if self.calls == 1:
                raise TimeoutError("timeout")
            return [{"campaign_name": "Recuperada"}]

    monkeypatch.setattr("traficcagent.integrations.google_ads.time.sleep", lambda _: None)
    transport = FlakyTransport()
    client = GoogleAdsMCPClient(settings=_settings(True), transport=transport)
    assert client.run_gaql("SELECT campaign.name FROM campaign")[0]["campaign_name"] == "Recuperada"
    assert transport.calls == 2


def test_rate_limit_esgota_tentativas(monkeypatch):
    class RateLimitedTransport:
        def call_tool(self, name, arguments):
            raise RuntimeError("429 rate limit")

    monkeypatch.setattr("traficcagent.integrations.google_ads.time.sleep", lambda _: None)
    settings = _settings(True)
    settings = Settings(**{**settings.__dict__, "google_ads_mcp_max_retries": 2})
    client = GoogleAdsMCPClient(settings=settings, transport=RateLimitedTransport())
    with pytest.raises(GoogleAdsMCPError, match="rate limit"):
        client.run_gaql("SELECT campaign.name FROM campaign")


def test_transporte_http_exige_url():
    settings = Settings(**{**_settings(True).__dict__, "google_ads_mcp_transport": "streamable-http"})
    client = GoogleAdsMCPClient(settings=settings)
    with pytest.raises(GoogleAdsMCPError, match="URL"):
        client.run_gaql("SELECT campaign.name FROM campaign")


def test_get_campanhas_ativas_com_payload_gaql_real():
    class GAQLRealTransport:
        def call_tool(self, name, arguments):
            return [
                {
                    "campaign.name": "Campanha Black Friday",
                    "metrics.cost_micros": 250_000_000,  # 250 BRL
                    "metrics.conversions": 15,
                    "segments.date": "2026-09-01",
                },
                {
                    "campaign": {"name": "Campanha Natal Aninhada"},
                    "metrics": {"cost_micros": 50_000_000, "conversions": 2},
                    "segments": {"date": "2026-09-10"},
                },
            ]

    client = GoogleAdsMCPClient(settings=_settings(True), transport=GAQLRealTransport())
    campanhas = client.get_campanhas_ativas()
    assert len(campanhas) == 2
    assert campanhas[0].nome == "Campanha Black Friday"
    assert campanhas[0].custo_total == 250.0
    assert campanhas[0].conversoes == 15
    assert campanhas[0].dias_ativa >= 1

    assert campanhas[1].nome == "Campanha Natal Aninhada"
    assert campanhas[1].custo_total == 50.0
    assert campanhas[1].conversoes == 2


def test_load_settings_max_retries_vazio(monkeypatch):
    from traficcagent.config import load_settings
    monkeypatch.setenv("GOOGLE_ADS_MCP_MAX_RETRIES", "")
    settings = load_settings()
    assert settings.google_ads_mcp_max_retries == 3
