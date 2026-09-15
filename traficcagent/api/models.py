"""Modelos SQLAlchemy do TraficcAgent (usuários e sites)."""
from __future__ import annotations

from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from traficcagent.db import Base


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    sites: Mapped[list["Site"]] = relationship(back_populates="dono", cascade="all, delete-orphan")


class Tenant(Base):
    """Agente/site isolado administrado pelo Core."""
    __tablename__ = "tenants"
    __table_args__ = (UniqueConstraint("domain", name="uq_tenants_domain"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    domain: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    niche: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[str] = mapped_column(String(60), nullable=False, default="active")

    sites: Mapped[list["Site"]] = relationship(back_populates="tenant")


class TenantMember(Base):
    __tablename__ = "tenant_members"
    __table_args__ = (UniqueConstraint("tenant_id", "user_id", name="uq_tenant_member"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(40), nullable=False, default="operator")
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="active")


class Site(Base):
    __tablename__ = "sites"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(200), nullable=False)
    nicho: Mapped[str] = mapped_column(String(120), nullable=False)
    responsavel: Mapped[str] = mapped_column(String(80), nullable=False, default="Ana")
    status: Mapped[str] = mapped_column(String(60), nullable=False, default="Planejamento")
    user_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False, index=True)
    tenant_id: Mapped[int | None] = mapped_column(ForeignKey("tenants.id"), nullable=True, index=True)

    dono: Mapped["Usuario"] = relationship(back_populates="sites")
    tenant: Mapped["Tenant | None"] = relationship(back_populates="sites")


class WorkItem(Base):
    """Registro persistente dos ambientes operacionais do MVD.

    Um modelo único mantém a primeira versão do fluxo simples e auditável;
    `kind` separa link, pauta, lote, campanha e evento sem misturar donos.
    """

    __tablename__ = "work_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    kind: Mapped[str] = mapped_column(String(40), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    status: Mapped[str] = mapped_column(String(60), nullable=False, default="Planejamento")
    details: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    user_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False, index=True)


class ProdutoRegistro(Base):
    __tablename__ = "produtos"
    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False, index=True)
    nome: Mapped[str] = mapped_column(String(200), nullable=False)
    preco: Mapped[float] = mapped_column(nullable=False, default=0)
    comissao_pct: Mapped[float] = mapped_column(nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(60), nullable=False, default="Planejamento")


class LinkAfiliado(Base):
    __tablename__ = "links_afiliados"
    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False, index=True)
    produto_id: Mapped[int] = mapped_column(ForeignKey("produtos.id"), nullable=False, index=True)
    site_id: Mapped[int] = mapped_column(ForeignKey("sites.id"), nullable=False, index=True)
    rede: Mapped[str] = mapped_column(String(100), nullable=False)
    url: Mapped[str] = mapped_column(String(1000), nullable=False)
    status: Mapped[str] = mapped_column(String(60), nullable=False, default="Ativo")


class ReviewRegistro(Base):
    __tablename__ = "reviews"
    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False, index=True)
    produto_id: Mapped[int] = mapped_column(ForeignKey("produtos.id"), nullable=False, index=True)
    site_id: Mapped[int] = mapped_column(ForeignKey("sites.id"), nullable=False, index=True)
    titulo: Mapped[str] = mapped_column(String(240), nullable=False)
    status: Mapped[str] = mapped_column(String(60), nullable=False, default="Pauta")
    conteudo: Mapped[str] = mapped_column(Text, nullable=False, default="")


class CampanhaRegistro(Base):
    __tablename__ = "campanhas_registros"
    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False, index=True)
    produto_id: Mapped[int] = mapped_column(ForeignKey("produtos.id"), nullable=False, index=True)
    site_id: Mapped[int] = mapped_column(ForeignKey("sites.id"), nullable=False, index=True)
    review_id: Mapped[int] = mapped_column(ForeignKey("reviews.id"), nullable=False, index=True)
    nome: Mapped[str] = mapped_column(String(200), nullable=False)
    orcamento: Mapped[float] = mapped_column(nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(60), nullable=False, default="Planejamento")


class MetricaCampanha(Base):
    __tablename__ = "metricas_campanhas"
    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    campanha_id: Mapped[int] = mapped_column(ForeignKey("campanhas_registros.id"), nullable=False, index=True)
    cliques: Mapped[int] = mapped_column(nullable=False, default=0)
    conversoes: Mapped[int] = mapped_column(nullable=False, default=0)
    custo: Mapped[float] = mapped_column(nullable=False, default=0)
    comissao: Mapped[float] = mapped_column(nullable=False, default=0)
    roi: Mapped[float] = mapped_column(nullable=False, default=0)


class EventoOperacao(Base):
    """Trilha de auditoria comum a todas as áreas do Core."""
    __tablename__ = "eventos_operacao"
    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False, index=True)
    entidade: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    entidade_id: Mapped[int] = mapped_column(nullable=False, index=True)
    acao: Mapped[str] = mapped_column(String(60), nullable=False)
    etapa_anterior: Mapped[str | None] = mapped_column(String(60), nullable=True)
    etapa_nova: Mapped[str | None] = mapped_column(String(60), nullable=True)
    detalhes: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
