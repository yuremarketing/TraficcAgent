"""Aplicação FastAPI para o TraficcAgent.

Expõe endpoints REST e de healthcheck requeridos pelo Cloud Run e pela
operação distribuída:
- GET /healthz: liveness probe do Cloud Run (porta 8080)
- GET /api/status: status do serviço e modo das integrações (real vs mock)
- GET /api/campanhas: métricas de campanhas ativas via Google Ads MCP
- GET /api/produtos: catálogo avaliado com regras financeiras de margem
- POST /api/produtos/avaliar: avaliação de produto pontual
- GET /api/sites: listagem de sites com suporte a user_id
- POST /api/sites: cadastro de novo site
- GET /api/sites/{site_id}: detalhe de um site
"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import FastAPI, HTTPException, Header, Query, status
from fastapi.middleware.cors import CORSMiddleware

from traficcagent.api.schemas import (
    CampanhaResponse,
    HealthResponse,
    ProdutoAvaliacaoResponse,
    ProdutoInput,
    SiteCreate,
    SiteResponse,
    StatusResponse,
)
from traficcagent.api.sites_store import store
from traficcagent.config import Settings, load_settings
from traficcagent.core.financial_engine import Produto, avaliar_produto
from traficcagent.core.traffic_manager import avaliar_campanha
from traficcagent.integrations.google_ads import GoogleAdsMCPClient, GoogleAdsMCPError

LOGGER = logging.getLogger(__name__)


def create_app(settings: Optional[Settings] = None) -> FastAPI:
    app_settings = settings or load_settings()

    app = FastAPI(
        title="TraficcAgent API",
        version="1.0.0",
        description="Servidor HTTP do TraficcAgent — Motor de Tráfego e Afiliados",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Armazena settings no app state para injeção / testes
    app.state.settings = app_settings

    @app.get("/healthz", response_model=HealthResponse, tags=["Health"])
    def healthcheck() -> HealthResponse:
        return HealthResponse(status="ok", service="traficcagent")

    @app.get("/api/status", response_model=StatusResponse, tags=["Status"])
    def get_status() -> StatusResponse:
        current_settings: Settings = getattr(app.state, "settings", load_settings())
        return StatusResponse(
            service="traficcagent",
            status="online",
            integrations={
                "google_ads": {
                    "mode": "real" if current_settings.has_google_ads_credentials else "mock",
                    "configured": current_settings.has_google_ads_credentials,
                    "transport": current_settings.google_ads_mcp_transport,
                },
                "affiliate_bot": {
                    "mode": "real" if current_settings.has_affiliate_bot_credentials else "mock",
                    "configured": current_settings.has_affiliate_bot_credentials,
                    "base_url": current_settings.affiliate_bot_base_url,
                },
                "llm": {
                    "mode": "real" if current_settings.has_llm_credentials else "mock",
                    "configured": current_settings.has_llm_credentials,
                },
            },
        )

    @app.get("/api/campanhas", response_model=list[CampanhaResponse], tags=["Campanhas"])
    def list_campanhas() -> list[CampanhaResponse]:
        current_settings: Settings = getattr(app.state, "settings", load_settings())
        client = GoogleAdsMCPClient(current_settings)
        try:
            campanhas = client.get_campanhas_ativas()
        except GoogleAdsMCPError as exc:
            LOGGER.error("Erro ao obter campanhas do Google Ads MCP: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Falha na comunicação com o servidor MCP: {exc}",
            ) from exc

        resultado: list[CampanhaResponse] = []
        for c in campanhas:
            decisao = avaliar_campanha(c, current_settings.rules)
            resultado.append(
                CampanhaResponse(
                    nome=c.nome,
                    dias_ativa=c.dias_ativa,
                    custo_total=c.custo_total,
                    conversoes=c.conversoes,
                    cpa=c.cpa,
                    status_decisao=decisao.status.value,
                    motivo_decisao=decisao.motivo,
                )
            )
        return resultado

    @app.get("/api/produtos", response_model=list[ProdutoAvaliacaoResponse], tags=["Produtos"])
    def list_produtos_padrao() -> list[ProdutoAvaliacaoResponse]:
        """Retorna catálogo de produtos de referência avaliados contra as regras financeiras."""
        current_settings: Settings = getattr(app.state, "settings", load_settings())
        produtos_exemplo = [
            Produto("Robô Aspirador Roomba", 2499.00, 12.0),
            Produto("Moedor de Café Automático", 380.00, 8.0),
            Produto("Cafeteira Prensa Francesa", 120.00, 15.0),
            Produto("Comedouro Inteligente Pet", 450.00, 10.0),
            Produto("Furadeira de Impacto 750W", 299.00, 6.0),
        ]
        res: list[ProdutoAvaliacaoResponse] = []
        for p in produtos_exemplo:
            av = avaliar_produto(p, current_settings.rules)
            res.append(
                ProdutoAvaliacaoResponse(
                    nome=p.nome,
                    preco=p.preco,
                    comissao_pct=p.comissao_pct,
                    lucro_liquido=p.lucro_liquido,
                    decisao=av.decisao.value,
                    motivo=av.motivo,
                    aceito=av.decisao.aceito,
                )
            )
        return res

    @app.post(
        "/api/produtos/avaliar",
        response_model=ProdutoAvaliacaoResponse,
        tags=["Produtos"],
    )
    def avaliar_produto_endpoint(payload: ProdutoInput) -> ProdutoAvaliacaoResponse:
        current_settings: Settings = getattr(app.state, "settings", load_settings())
        try:
            p = Produto(
                nome=payload.nome,
                preco=payload.preco,
                comissao_pct=payload.comissao_pct,
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(exc),
            ) from exc

        av = avaliar_produto(p, current_settings.rules)
        return ProdutoAvaliacaoResponse(
            nome=p.nome,
            preco=p.preco,
            comissao_pct=p.comissao_pct,
            lucro_liquido=p.lucro_liquido,
            decisao=av.decisao.value,
            motivo=av.motivo,
            aceito=av.decisao.aceito,
        )

    @app.get("/api/sites", response_model=list[SiteResponse], tags=["Sites"])
    def list_sites(
        user_id: Optional[str] = Query(None, description="Filtrar por proprietário"),
        x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    ) -> list[SiteResponse]:
        filtro_user = user_id or x_user_id
        sites = store.list_sites(filtro_user)
        return [SiteResponse(**s) for s in sites]

    @app.post(
        "/api/sites",
        response_model=SiteResponse,
        status_code=status.HTTP_201_CREATED,
        tags=["Sites"],
    )
    def create_site(
        payload: SiteCreate,
        x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    ) -> SiteResponse:
        nome = payload.nome.strip()
        nicho = payload.nicho.strip()
        if not nome or not nicho:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Nome e nicho são obrigatórios e não podem ser vazios.",
            )

        dono = payload.user_id or x_user_id
        novo_site = store.add_site(
            nome=nome,
            nicho=nicho,
            responsavel=payload.responsavel,
            status=payload.status,
            user_id=dono,
        )
        return SiteResponse(**novo_site)

    @app.get("/api/sites/{site_id}", response_model=SiteResponse, tags=["Sites"])
    def get_site(site_id: int) -> SiteResponse:
        site = store.get_site(site_id)
        if not site:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Site com ID {site_id} não encontrado.",
            )
        return SiteResponse(**site)

    return app


# Instância global padrão
app = create_app()
