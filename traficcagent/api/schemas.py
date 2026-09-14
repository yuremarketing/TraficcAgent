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
    user_id: Optional[str] = Field(None, description="Identificador do usuário / proprietário")


class SiteResponse(BaseModel):
    id: int
    nome: str
    nicho: str
    responsavel: str
    status: str
    user_id: Optional[str] = None
