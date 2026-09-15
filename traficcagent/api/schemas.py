"""Schemas Pydantic para as rotas da API HTTP do TraficcAgent."""
from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "ok"
    service: str = "traficcagent"


class IntegrationStatus(BaseModel):
    mode: str
    configured: bool


class StatusResponse(BaseModel):
    service: str = "traficcagent"
    status: str = "online"
    integrations: dict[str, Any]


class CampanhaResponse(BaseModel):
    nome: str
    dias_ativa: int
    custo_total: float
    conversoes: int
    cpa: Optional[float] = None
    status_decisao: Optional[str] = None
    motivo_decisao: Optional[str] = None


class ProdutoInput(BaseModel):
    nome: str = Field(..., min_length=1, description="Nome do produto")
    preco: float = Field(..., ge=0, description="Preço em reais")
    comissao_pct: float = Field(..., ge=0, description="Percentual de comissão")


class ProdutoAvaliacaoResponse(BaseModel):
    nome: str
    preco: float
    comissao_pct: float
    lucro_liquido: float
    decisao: str
    motivo: str
    aceito: bool


class SiteCreate(BaseModel):
    nome: str = Field(..., min_length=1, description="Nome do site")
    nicho: str = Field(..., min_length=1, description="Nicho do site")
    responsavel: str = Field("Ana", description="Dev/sócio responsável")
    status: str = Field("Planejamento", description="Status na esteira")
    dominio: Optional[str] = Field(None, max_length=255, description="Domínio canônico do agente")
    # Sem user_id aqui de propósito: o dono é sempre o usuário autenticado
    # da sessão (Authorization: Bearer <token>), nunca um valor vindo do
    # cliente — era exatamente essa brecha que permitia IDOR antes (#28).


class SiteUpdate(BaseModel):
    status: str = Field(..., min_length=1, description="Novo status do site")


class SiteResponse(BaseModel):
    id: int
    nome: str
    nicho: str
    responsavel: str
    status: str
    user_id: int


class UsuarioCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=80)
    password: str = Field(..., min_length=6, description="Mínimo 6 caracteres")


class UsuarioResponse(BaseModel):
    id: int
    username: str


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class WorkItemCreate(BaseModel):
    kind: str = Field(..., min_length=1, max_length=40)
    title: str = Field(..., min_length=1, max_length=240)
    status: str = Field("Planejamento", min_length=1, max_length=60)
    details: dict[str, Any] = Field(default_factory=dict)


class WorkItemUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=240)
    status: Optional[str] = Field(None, min_length=1, max_length=60)
    details: Optional[dict[str, Any]] = None


class WorkItemResponse(BaseModel):
    id: int
    kind: str
    title: str
    status: str
    details: dict[str, Any]
    user_id: int
    tenant_id: Optional[int] = None
    dominio: Optional[str] = None


class TenantResponse(BaseModel):
    id: int
    dominio: str
    nome: str
    nicho: str
    status: str
    papel: str


class CoreContextResponse(BaseModel):
    usuario_id: int
    username: str
    tenants: list[TenantResponse]


class OperationEventCreate(BaseModel):
    tenant_id: int
    entidade: str = Field(..., min_length=1, max_length=60)
    entidade_id: int
    acao: str = Field(..., min_length=1, max_length=60)
    etapa_anterior: Optional[str] = None
    etapa_nova: Optional[str] = None
    detalhes: dict[str, Any] = Field(default_factory=dict)


class OperationEventResponse(OperationEventCreate):
    id: int
    user_id: int
