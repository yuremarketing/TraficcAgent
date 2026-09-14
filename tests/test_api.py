"""Testes automatizados das rotas HTTP do TraficcAgent."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from traficcagent.api.app import create_app
from traficcagent.config import BusinessRules, Settings


def registrar_e_logar(client: TestClient, username: str, password: str = "senha123456") -> dict[str, str]:
    """Registra um usuário novo, loga, e devolve o header Authorization pronto."""
    client.post("/api/auth/register", json={"username": username, "password": password})
    login = client.post("/api/auth/login", json={"username": username, "password": password})
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


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


def test_sites_requer_autenticacao(client: TestClient) -> None:
    assert client.get("/api/sites").status_code == 401
    assert client.post("/api/sites", json={"nome": "X", "nicho": "Y"}).status_code == 401
    assert client.get("/api/sites/1").status_code == 401


def test_sites_list_por_usuario(client: TestClient) -> None:
    headers_yure = registrar_e_logar(client, "yure")
    headers_philipy = registrar_e_logar(client, "philipy")

    client.post("/api/sites", json={"nome": "Site do Yure", "nicho": "Casa"}, headers=headers_yure)
    client.post("/api/sites", json={"nome": "Site do Philipy", "nicho": "Pet"}, headers=headers_philipy)

    sites_yure = client.get("/api/sites", headers=headers_yure).json()
    assert len(sites_yure) == 1
    assert sites_yure[0]["nome"] == "Site do Yure"

    sites_philipy = client.get("/api/sites", headers=headers_philipy).json()
    assert len(sites_philipy) == 1
    assert sites_philipy[0]["nome"] == "Site do Philipy"


def test_sites_create_and_get(client: TestClient) -> None:
    headers = registrar_e_logar(client, "yure")
    novo = {
        "nome": "Meu Novo Site Afiliado",
        "nicho": "Saúde e Bem Estar",
        "responsavel": "Yure",
        "status": "Planejamento",
    }
    create_resp = client.post("/api/sites", json=novo, headers=headers)
    assert create_resp.status_code == 201
    created_data = create_resp.json()
    assert created_data["nome"] == "Meu Novo Site Afiliado"
    assert created_data["nicho"] == "Saúde e Bem Estar"
    site_id = created_data["id"]

    # Busca por ID
    get_resp = client.get(f"/api/sites/{site_id}", headers=headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == site_id
    assert get_resp.json()["user_id"] == created_data["user_id"]


def test_sites_get_not_found(client: TestClient) -> None:
    headers = registrar_e_logar(client, "yure")
    response = client.get("/api/sites/999999", headers=headers)
    assert response.status_code == 404
    assert "não encontrado" in response.json()["detail"]


def test_sites_create_validation_error(client: TestClient) -> None:
    headers = registrar_e_logar(client, "yure")
    response = client.post("/api/sites", json={"nome": "   ", "nicho": ""}, headers=headers)
    assert response.status_code == 422
