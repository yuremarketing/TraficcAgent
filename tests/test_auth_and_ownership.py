"""Testes de autenticação (#27) e ownership/anti-IDOR (#28)."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from traficcagent.api.app import create_app
from traficcagent.config import BusinessRules, Settings


@pytest.fixture
def client() -> TestClient:
    settings = Settings(
        google_ads_developer_token=None,
        google_ads_customer_id=None,
        affiliate_bot_api_key=None,
        affiliate_bot_base_url="https://botdoafiliado.com/api/v1/",
        anthropic_api_key=None,
        rules=BusinessRules(comissao_minima_pct=10.0, alto_ticket_lucro_min=40.0, alto_ticket_lucro_max=50.0),
    )
    return TestClient(create_app(settings))


def logar(client: TestClient, username: str, password: str = "senha123456") -> dict[str, str]:
    client.post("/api/auth/register", json={"username": username, "password": password})
    login = client.post("/api/auth/login", json={"username": username, "password": password})
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_registro_e_login() -> None:
    settings = Settings(
        google_ads_developer_token=None, google_ads_customer_id=None, affiliate_bot_api_key=None,
        affiliate_bot_base_url="https://botdoafiliado.com/api/v1/", anthropic_api_key=None,
        rules=BusinessRules(comissao_minima_pct=10.0, alto_ticket_lucro_min=40.0, alto_ticket_lucro_max=50.0),
    )
    client = TestClient(create_app(settings))

    resp = client.post("/api/auth/register", json={"username": "novo_user", "password": "senha123456"})
    assert resp.status_code == 201
    assert resp.json()["username"] == "novo_user"
    assert "password" not in resp.json() and "password_hash" not in resp.json()

    login = client.post("/api/auth/login", json={"username": "novo_user", "password": "senha123456"})
    assert login.status_code == 200
    assert login.json()["token_type"] == "bearer"
    assert len(login.json()["access_token"]) > 20


def test_registro_username_duplicado(client: TestClient) -> None:
    client.post("/api/auth/register", json={"username": "duplicado", "password": "senha123456"})
    resp = client.post("/api/auth/register", json={"username": "duplicado", "password": "outrasenha"})
    assert resp.status_code == 409


def test_login_senha_errada(client: TestClient) -> None:
    client.post("/api/auth/register", json={"username": "alguem", "password": "senha123456"})
    resp = client.post("/api/auth/login", json={"username": "alguem", "password": "senha_errada"})
    assert resp.status_code == 401


def test_login_usuario_inexistente(client: TestClient) -> None:
    resp = client.post("/api/auth/login", json={"username": "ninguem", "password": "senha123456"})
    assert resp.status_code == 401


def test_token_invalido_rejeitado(client: TestClient) -> None:
    resp = client.get("/api/sites", headers={"Authorization": "Bearer token-que-nao-existe"})
    assert resp.status_code == 401


def test_usuario_nao_acessa_lista_do_outro(client: TestClient) -> None:
    yure = logar(client, "yure_iso")
    philipy = logar(client, "philipy_iso")

    client.post("/api/sites", json={"nome": "Site Sigiloso do Philipy", "nicho": "Financeiro"}, headers=philipy)

    sites_yure = client.get("/api/sites", headers=yure).json()
    assert all(s["nome"] != "Site Sigiloso do Philipy" for s in sites_yure)
    assert len(sites_yure) == 0


def test_usuario_nao_acessa_site_do_outro_por_id_direto(client: TestClient) -> None:
    """O núcleo do anti-IDOR (#28): mesmo sabendo o ID exato do recurso de
    outro usuário, não dá pra acessar — nem por acaso, nem de propósito."""
    yure = logar(client, "yure_idor")
    philipy = logar(client, "philipy_idor")

    criado = client.post(
        "/api/sites", json={"nome": "Site do Philipy", "nicho": "Pet"}, headers=philipy
    ).json()
    site_id = criado["id"]

    # O dono acessa normalmente.
    assert client.get(f"/api/sites/{site_id}", headers=philipy).status_code == 200

    # O Yure, mesmo sabendo o ID exato, não acessa — e o formato da resposta
    # é o mesmo de um ID inexistente (a única diferença é o número que o
    # próprio requisitante informou na URL, não algo que ele não soubesse).
    resp_outro = client.get(f"/api/sites/{site_id}", headers=yure)
    resp_inexistente = client.get("/api/sites/999999", headers=yure)
    assert resp_outro.status_code == 404 == resp_inexistente.status_code
    assert "não encontrado" in resp_outro.json()["detail"]


def test_patch_status_dono_funciona(client: TestClient) -> None:
    dono = logar(client, "dono_patch")
    criado = client.post("/api/sites", json={"nome": "Site", "nicho": "X"}, headers=dono).json()

    resp = client.patch(f"/api/sites/{criado['id']}", json={"status": "Arquivado"}, headers=dono)
    assert resp.status_code == 200
    assert resp.json()["status"] == "Arquivado"


def test_patch_status_outro_usuario_nao_consegue(client: TestClient) -> None:
    """Mesmo padrão anti-IDOR do GET: usuário B não arquiva site do usuário A."""
    dono = logar(client, "dono_patch2")
    outro = logar(client, "outro_patch2")
    criado = client.post("/api/sites", json={"nome": "Site Sigiloso", "nicho": "X"}, headers=dono).json()

    resp = client.patch(f"/api/sites/{criado['id']}", json={"status": "Arquivado"}, headers=outro)
    assert resp.status_code == 404

    # Confirma que o status do dono não mudou.
    ainda_ativo = client.get(f"/api/sites/{criado['id']}", headers=dono).json()
    assert ainda_ativo["status"] != "Arquivado"


def test_work_item_nao_vaza_entre_usuarios_nem_por_id(client: TestClient) -> None:
    dono = logar(client, "dono_work_item")
    outro = logar(client, "outro_work_item")
    criado = client.post(
        "/api/work-items",
        json={"kind": "campanha", "title": "Campanha privada", "details": {"roi": 12}},
        headers=dono,
    )
    assert criado.status_code == 201
    item_id = criado.json()["id"]

    assert client.get("/api/work-items", headers=outro).json() == []
    assert client.patch(
        f"/api/work-items/{item_id}",
        json={"status": "Concluído"},
        headers=outro,
    ).status_code == 404
    assert client.get(f"/api/work-items/{item_id}", headers=outro).status_code == 405
