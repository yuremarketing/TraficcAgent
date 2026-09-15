"""Aplicação FastAPI para o TraficcAgent.

Expõe endpoints REST e de healthcheck requeridos pelo Cloud Run e pela
operação distribuída:
- GET /healthz: liveness probe do Cloud Run (porta 8080)
- GET /api/status: status do serviço e modo das integrações (real vs mock)
- GET /api/campanhas: métricas de campanhas ativas via Google Ads MCP
- GET /api/produtos: catálogo avaliado com regras financeiras de margem
- POST /api/produtos/avaliar: avaliação de produto pontual
- POST /api/auth/register, /api/auth/login: cadastro e sessão (issue #27)
- GET/POST /api/sites, GET /api/sites/{site_id}: exigem sessão válida
  (Authorization: Bearer <token>) e só enxergam/afetam sites do próprio
  usuário autenticado — nunca um user_id vindo do cliente (issue #28)
"""
from __future__ import annotations

import logging
import json
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from traficcagent.api import sites_store
from traficcagent.api.auth import create_session, get_current_user, hash_password, verify_password
from traficcagent.api.models import CampanhaRegistro, EventoOperacao, LinkAfiliado, ProdutoRegistro, ReviewRegistro, Site, Tenant, TenantMember, Usuario, WorkItem
from traficcagent.api.schemas import (
    CampanhaResponse,
    HealthResponse,
    LoginRequest,
    ProdutoAvaliacaoResponse,
    ProdutoInput,
    SiteCreate,
    SiteResponse,
    SiteUpdate,
    StatusResponse,
    TokenResponse,
    TenantResponse,
    CoreContextResponse,
    OperationEventCreate,
    OperationEventResponse,
    UsuarioCreate,
    UsuarioResponse,
    WorkItemCreate,
    WorkItemUpdate,
    WorkItemResponse,
)
from traficcagent.config import Settings, load_settings
from traficcagent.core.financial_engine import Produto, avaliar_produto
from traficcagent.core.traffic_manager import avaliar_campanha
from traficcagent.db import get_db, init_db
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
        allow_origins=list(app_settings.cors_origins),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Armazena settings no app state para injeção / testes
    app.state.settings = app_settings
    init_db()

    @app.post(
        "/api/auth/register",
        response_model=UsuarioResponse,
        status_code=status.HTTP_201_CREATED,
        tags=["Auth"],
    )
    def register(payload: UsuarioCreate, db: Session = Depends(get_db)) -> UsuarioResponse:
        existente = db.query(Usuario).filter(Usuario.username == payload.username).first()
        if existente:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Nome de usuário já existe.",
            )
        usuario = Usuario(username=payload.username, password_hash=hash_password(payload.password))
        db.add(usuario)
        db.commit()
        db.refresh(usuario)
        return UsuarioResponse(id=usuario.id, username=usuario.username)

    @app.post("/api/auth/login", response_model=TokenResponse, tags=["Auth"])
    def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
        usuario = db.query(Usuario).filter(Usuario.username == payload.username).first()
        if not usuario or not verify_password(payload.password, usuario.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuário ou senha inválidos.",
            )
        token = create_session(usuario.id)
        return TokenResponse(access_token=token)

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

    @app.get("/api/tenants", response_model=list[TenantResponse], tags=["Tenants"])
    def list_authorized_tenants(
        current_user: Usuario = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> list[TenantResponse]:
        """Lista somente os sites/agentes aos quais a sessão pertence."""
        rows = (
            db.query(Tenant, TenantMember.role)
            .join(TenantMember, TenantMember.tenant_id == Tenant.id)
            .filter(TenantMember.user_id == current_user.id, TenantMember.status == "active")
            .order_by(Tenant.id.desc())
            .all()
        )
        return [TenantResponse(id=t.id, dominio=t.domain, nome=t.name, nicho=t.niche, status=t.status, papel=role) for t, role in rows]

    @app.get("/api/tenants/{tenant_id}", response_model=TenantResponse, tags=["Tenants"])
    def get_authorized_tenant(
        tenant_id: int,
        current_user: Usuario = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> TenantResponse:
        """Resolve o agente ativo sem revelar tenants de terceiros."""
        row = (
            db.query(Tenant, TenantMember.role)
            .join(TenantMember, TenantMember.tenant_id == Tenant.id)
            .filter(Tenant.id == tenant_id, TenantMember.user_id == current_user.id, TenantMember.status == "active")
            .first()
        )
        if row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant não encontrado.")
        tenant, role = row
        return TenantResponse(id=tenant.id, dominio=tenant.domain, nome=tenant.name, nicho=tenant.niche, status=tenant.status, papel=role)

    @app.get("/api/context", response_model=CoreContextResponse, tags=["Core"])
    def get_core_context(
        current_user: Usuario = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> CoreContextResponse:
        """Contrato compartilhado pelo Core e por todas as abas operacionais."""
        rows = (
            db.query(Tenant, TenantMember.role)
            .join(TenantMember, TenantMember.tenant_id == Tenant.id)
            .filter(TenantMember.user_id == current_user.id, TenantMember.status == "active")
            .order_by(Tenant.id.desc())
            .all()
        )
        tenants = [TenantResponse(id=t.id, dominio=t.domain, nome=t.name, nicho=t.niche, status=t.status, papel=role) for t, role in rows]
        return CoreContextResponse(usuario_id=current_user.id, username=current_user.username, tenants=tenants)

    @app.get("/api/operacao/resumo", tags=["Operação"])
    def operation_summary(tenant_id: int, dimensao: str = "Site", ambiente: str = "Operação", current_user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
        """Resumo compartilhado para Market Maker, Site, Nicho e Produto."""
        member = db.query(TenantMember).filter(TenantMember.tenant_id == tenant_id, TenantMember.user_id == current_user.id, TenantMember.status == "active").first()
        if member is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant não encontrado.")
        allowed = {"Market Maker", "Site", "Nicho", "Produto"}
        if dimensao not in allowed:
            raise HTTPException(status_code=422, detail="Dimensão inválida.")
        ambientes = {"Operação", "Finanças", "Conteúdo", "Tráfego", "Auditoria", "Configuração"}
        if ambiente not in ambientes:
            raise HTTPException(status_code=422, detail="Ambiente inválido.")
        return {"tenant_id": tenant_id, "dimensao": dimensao, "ambiente": ambiente, "filtro_aplicado": dimensao + " / " + ambiente, "sites": db.query(Site).filter(Site.tenant_id == tenant_id).count(), "produtos": db.query(ProdutoRegistro).filter(ProdutoRegistro.tenant_id == tenant_id).count(), "links": db.query(LinkAfiliado).filter(LinkAfiliado.tenant_id == tenant_id).count(), "reviews": db.query(ReviewRegistro).filter(ReviewRegistro.tenant_id == tenant_id).count(), "campanhas": db.query(CampanhaRegistro).filter(CampanhaRegistro.tenant_id == tenant_id).count(), "modo": "manual/mock"}

    @app.get("/api/operacao/catalogo", tags=["Operação"])
    def operation_catalog(tenant_id: int, tipo: str = "site", current_user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
        member = db.query(TenantMember).filter(TenantMember.tenant_id == tenant_id, TenantMember.user_id == current_user.id, TenantMember.status == "active").first()
        if member is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant não encontrado.")
        tables = {"site": Site, "produto": ProdutoRegistro, "link": LinkAfiliado, "review": ReviewRegistro, "campanha": CampanhaRegistro}
        model = tables.get(tipo.lower())
        if model is None:
            raise HTTPException(status_code=422, detail="Tipo de catálogo inválido.")
        rows = db.query(model).filter(model.tenant_id == tenant_id).limit(200).all()
        return {"tenant_id": tenant_id, "tipo": tipo.lower(), "items": [{"id": x.id, "status": getattr(x, "status", None), "nome": getattr(x, "nome", None) or getattr(x, "titulo", None) or getattr(x, "rede", None)} for x in rows]}

    @app.post("/api/operacao/eventos", response_model=OperationEventResponse, status_code=status.HTTP_201_CREATED, tags=["Auditoria"])
    def create_operation_event(payload: OperationEventCreate, current_user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)) -> OperationEventResponse:
        member = db.query(TenantMember).filter(TenantMember.tenant_id == payload.tenant_id, TenantMember.user_id == current_user.id, TenantMember.status == "active").first()
        if member is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant não encontrado.")
        event = EventoOperacao(tenant_id=payload.tenant_id, user_id=current_user.id, entidade=payload.entidade.strip(), entidade_id=payload.entidade_id, acao=payload.acao.strip(), etapa_anterior=payload.etapa_anterior, etapa_nova=payload.etapa_nova, detalhes=json.dumps(payload.detalhes, ensure_ascii=False))
        db.add(event); db.commit(); db.refresh(event)
        return OperationEventResponse(id=event.id, user_id=event.user_id, tenant_id=event.tenant_id, entidade=event.entidade, entidade_id=event.entidade_id, acao=event.acao, etapa_anterior=event.etapa_anterior, etapa_nova=event.etapa_nova, detalhes=payload.detalhes)

    @app.get("/api/operacao/eventos", response_model=list[OperationEventResponse], tags=["Auditoria"])
    def list_operation_events(tenant_id: int, current_user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)) -> list[OperationEventResponse]:
        member = db.query(TenantMember).filter(TenantMember.tenant_id == tenant_id, TenantMember.user_id == current_user.id, TenantMember.status == "active").first()
        if member is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant não encontrado.")
        events = db.query(EventoOperacao).filter(EventoOperacao.tenant_id == tenant_id).order_by(EventoOperacao.id.desc()).limit(100).all()
        return [OperationEventResponse(id=e.id, user_id=e.user_id, tenant_id=e.tenant_id, entidade=e.entidade, entidade_id=e.entidade_id, acao=e.acao, etapa_anterior=e.etapa_anterior, etapa_nova=e.etapa_nova, detalhes=json.loads(e.detalhes or "{}")) for e in events]

    @app.get("/api/sites", response_model=list[SiteResponse], tags=["Sites"])
    def list_sites(
        current_user: Usuario = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> list[SiteResponse]:
        sites = sites_store.list_sites(db, owner_id=current_user.id)
        return [SiteResponse(id=s.id, nome=s.nome, nicho=s.nicho, responsavel=s.responsavel, status=s.status, user_id=s.user_id) for s in sites]

    @app.post(
        "/api/sites",
        response_model=SiteResponse,
        status_code=status.HTTP_201_CREATED,
        tags=["Sites"],
    )
    def create_site(
        payload: SiteCreate,
        current_user: Usuario = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> SiteResponse:
        nome = payload.nome.strip()
        nicho = payload.nicho.strip()
        if not nome or not nicho:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Nome e nicho são obrigatórios e não podem ser vazios.",
            )

        novo_site = sites_store.add_site(
            db,
            owner_id=current_user.id,
            nome=nome,
            nicho=nicho,
            responsavel=payload.responsavel,
            status=payload.status,
            dominio=payload.dominio,
        )
        return SiteResponse(
            id=novo_site.id,
            nome=novo_site.nome,
            nicho=novo_site.nicho,
            responsavel=novo_site.responsavel,
            status=novo_site.status,
            user_id=novo_site.user_id,
            tenant_id=novo_site.tenant_id,
            dominio=novo_site.tenant.domain if novo_site.tenant else None,
        )

    @app.get("/api/sites/{site_id}", response_model=SiteResponse, tags=["Sites"])
    def get_site(
        site_id: int,
        current_user: Usuario = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> SiteResponse:
        site = sites_store.get_site_for_owner(db, site_id=site_id, owner_id=current_user.id)
        if not site:
            # Mesma resposta pra "não existe" e "existe mas não é seu" —
            # de propósito, pra não vazar a existência de sites de terceiros.
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Site com ID {site_id} não encontrado.",
            )
        return SiteResponse(
            id=site.id,
            nome=site.nome,
            nicho=site.nicho,
            responsavel=site.responsavel,
            status=site.status,
            user_id=site.user_id,
        )

    @app.patch("/api/sites/{site_id}", response_model=SiteResponse, tags=["Sites"])
    def update_site(
        site_id: int,
        payload: SiteUpdate,
        current_user: Usuario = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> SiteResponse:
        site = sites_store.update_site_status(
            db, site_id=site_id, owner_id=current_user.id, status=payload.status
        )
        if not site:
            # Mesma regra anti-IDOR do GET: não existe e "existe mas não é
            # seu" respondem igual.
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Site com ID {site_id} não encontrado.",
            )
        return SiteResponse(
            id=site.id,
            nome=site.nome,
            nicho=site.nicho,
            responsavel=site.responsavel,
            status=site.status,
            user_id=site.user_id,
        )

    @app.get("/api/work-items", response_model=list[WorkItemResponse], tags=["Operação"])
    def list_work_items(
        kind: Optional[str] = None,
        current_user: Usuario = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> list[WorkItemResponse]:
        query = db.query(WorkItem).filter(WorkItem.user_id == current_user.id)
        if kind:
            query = query.filter(WorkItem.kind == kind)
        return [WorkItemResponse(id=x.id, kind=x.kind, title=x.title, status=x.status,
                                 details=json.loads(x.details or "{}"), user_id=x.user_id)
                for x in query.order_by(WorkItem.id.desc()).all()]

    @app.post("/api/work-items", response_model=WorkItemResponse, status_code=status.HTTP_201_CREATED, tags=["Operação"])
    def create_work_item(payload: WorkItemCreate, current_user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)) -> WorkItemResponse:
        item = WorkItem(kind=payload.kind.strip(), title=payload.title.strip(), status=payload.status.strip(),
                        details=json.dumps(payload.details), user_id=current_user.id)
        db.add(item); db.commit(); db.refresh(item)
        return WorkItemResponse(id=item.id, kind=item.kind, title=item.title, status=item.status,
                                details=payload.details, user_id=item.user_id)

    @app.patch("/api/work-items/{item_id}", response_model=WorkItemResponse, tags=["Operação"])
    def update_work_item(item_id: int, payload: WorkItemUpdate, current_user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)) -> WorkItemResponse:
        item = db.query(WorkItem).filter(WorkItem.id == item_id, WorkItem.user_id == current_user.id).first()
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registro não encontrado.")
        if payload.title is not None: item.title = payload.title.strip()
        if payload.status is not None: item.status = payload.status.strip()
        if payload.details is not None: item.details = json.dumps(payload.details)
        db.commit(); db.refresh(item)
        return WorkItemResponse(id=item.id, kind=item.kind, title=item.title, status=item.status,
                                details=json.loads(item.details or "{}"), user_id=item.user_id)

    return app


# Instância global padrão
app = create_app()
