"""Testes automatizados das rotas HTTP do TraficcAgent."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from traficcagent.api.app import create_app
from traficcagent.api.sites_store import store
from traficcagent.config import BusinessRules, Settings


@pytest.fixture(autouse=True)
def reset_store():
    store.reset()
    yield
    store.reset()


@pytest.fixture
def client() -> TestClient:
    settings = Settings(
        google_ads_developer_token=None,
        google_ads_customer_id=None,
        affiliate_bot_api_key=None,
        affiliate_bot_base_url="https://botdoafiliado.com/api/v1/",
        anthropic_api_key=None,
        rules=BusinessRules(
            comissao_minima_pct=10.0,
            alto_ticket_lucro_min=40.0,
            alto_ticket_lucro_max=50.0,
        ),
    )
    app = create_app(settings)
    return TestClient(app)


def test_healthz(client: TestClient) -> None:
    response = client.get("/healthz")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "traficcagent"


def test_status_endpoint(client: TestClient) -> None:
    response = client.get("/api/status")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "traficcagent"
    assert data["status"] == "online"
    integrations = data["integrations"]
    assert "google_ads" in integrations
    assert "affiliate_bot" in integrations
    assert "llm" in integrations
    assert integrations["google_ads"]["mode"] == "mock"
    assert integrations["affiliate_bot"]["mode"] == "mock"
    assert integrations["llm"]["mode"] == "mock"


def test_campanhas_endpoint_mock(client: TestClient) -> None:
    response = client.get("/api/campanhas")
    assert response.status_code == 200
    campanhas = response.json()
    assert isinstance(campanhas, list)
    assert len(campanhas) > 0

    primeira = campanhas[0]
    assert "nome" in primeira
    assert "dias_ativa" in primeira
    assert "custo_total" in primeira
    assert "conversoes" in primeira
    assert "status_decisao" in primeira
    assert "motivo_decisao" in primeira
    assert primeira["custo_total"] >= 0


def test_produtos_padrao_endpoint(client: TestClient) -> None:
    response = client.get("/api/produtos")
    assert response.status_code == 200
    produtos = response.json()
    assert isinstance(produtos, list)
    assert len(produtos) > 0

    primeiro = produtos[0]
    assert "nome" in primeiro
    assert "preco" in primeiro
    assert "comissao_pct" in primeiro
    assert "lucro_liquido" in primeiro
    assert "decisao" in primeiro
    assert "aceito" in primeiro
    assert isinstance(primeiro["aceito"], bool)


def test_avaliar_produto_aceito(client: TestClient) -> None:
    payload = {"nome": "Curso Avançado", "preco": 200.0, "comissao_pct": 15.0}
    response = client.post("/api/produtos/avaliar", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["nome"] == "Curso Avançado"
    assert data["aceito"] is True
    assert data["lucro_liquido"] == 30.0


def test_avaliar_produto_rejeitado(client: TestClient) -> None:
    payload = {"nome": "Produto Baixa Margem", "preco": 50.0, "comissao_pct": 5.0}
    response = client.post("/api/produtos/avaliar", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["aceito"] is False
    assert data["decisao"] == "rejeitado"


def test_avaliar_produto_invalido(client: TestClient) -> None:
    payload = {"nome": "", "preco": -10.0, "comissao_pct": -5.0}
    response = client.post("/api/produtos/avaliar", json=payload)
    assert response.status_code == 422


def test_sites_list_and_filter(client: TestClient) -> None:
    # Listagem completa
    response = client.get("/api/sites")
    assert response.status_code == 200
    sites = response.json()
    assert len(sites) >= 4

    # Filtro por user_id query param
    resp_yure = client.get("/api/sites?user_id=yure")
    assert resp_yure.status_code == 200
    sites_yure = resp_yure.json()
    assert len(sites_yure) > 0
    assert all(s["user_id"] == "yure" for s in sites_yure)

    # Filtro por Header X-User-Id
    resp_philipy = client.get("/api/sites", headers={"X-User-Id": "philipy"})
    assert resp_philipy.status_code == 200
    sites_philipy = resp_philipy.json()
    assert len(sites_philipy) > 0
    assert all(s["user_id"] == "philipy" for s in sites_philipy)


def test_sites_create_and_get(client: TestClient) -> None:
    novo = {
        "nome": "Meu Novo Site Afiliado",
        "nicho": "Saúde e Bem Estar",
        "responsavel": "Yure",
        "status": "Planejamento",
        "user_id": "yure",
    }
    create_resp = client.post("/api/sites", json=novo)
    assert create_resp.status_code == 201
    created_data = create_resp.json()
    assert created_data["nome"] == "Meu Novo Site Afiliado"
    assert created_data["nicho"] == "Saúde e Bem Estar"
    assert created_data["user_id"] == "yure"
    site_id = created_data["id"]

    # Busca por ID
    get_resp = client.get(f"/api/sites/{site_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == site_id


def test_sites_get_not_found(client: TestClient) -> None:
    response = client.get("/api/sites/999999")
    assert response.status_code == 404
    assert "não encontrado" in response.json()["detail"]


def test_sites_create_validation_error(client: TestClient) -> None:
    response = client.post("/api/sites", json={"nome": "   ", "nicho": ""})
    assert response.status_code == 422
