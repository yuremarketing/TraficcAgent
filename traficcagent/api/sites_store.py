"""Persistência de sites do TraficcAgent (Postgres/SQLite via SQLAlchemy).

Toda operação exige `owner_id` — não existe leitura ou escrita de site sem
saber de quem é (issue #28: ownership/anti-IDOR). Nunca confie num user_id
vindo do cliente; ele sempre deve vir de `auth.get_current_user`.
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from traficcagent.api.models import Site, Tenant, TenantMember


def list_sites(db: Session, owner_id: int) -> list[Site]:
    return (
        db.query(Site)
        .filter(Site.user_id == owner_id)
        .order_by(Site.id.desc())
        .all()
    )


def add_site(
    db: Session,
    owner_id: int,
    nome: str,
    nicho: str,
    responsavel: str = "Ana",
    status: str = "Planejamento",
    dominio: Optional[str] = None,
) -> Site:
    domain = (dominio or f"{nome.strip().lower().replace(' ', '-')}.local").strip().lower()
    tenant = Tenant(domain=domain, name=nome.strip(), niche=nicho.strip())
    db.add(tenant)
    db.flush()
    db.add(TenantMember(tenant_id=tenant.id, user_id=owner_id, role="owner"))
    site = Site(
        nome=nome.strip(),
        nicho=nicho.strip(),
        responsavel=responsavel.strip(),
        status=status.strip(),
        user_id=owner_id,
        tenant_id=tenant.id,
    )
    db.add(site)
    db.commit()
    db.refresh(site)
    return site


def update_site_status(db: Session, site_id: int, owner_id: int, status: str) -> Optional[Site]:
    """Atualiza o status só se o site pertencer a owner_id — None em
    qualquer outro caso (mesma regra anti-IDOR de get_site_for_owner)."""
    site = get_site_for_owner(db, site_id=site_id, owner_id=owner_id)
    if site is None:
        return None
    site.status = status.strip()
    db.commit()
    db.refresh(site)
    return site


def get_site_for_owner(db: Session, site_id: int, owner_id: int) -> Optional[Site]:
    """Retorna o site só se pertencer a owner_id — None em qualquer outro
    caso (não existe, ou existe mas é de outro usuário). De propósito
    indistinguível: devolver 404 num caso e 403 no outro vaza a existência
    de recursos de terceiros (a mesma classe de bug do achado #28)."""
    return (
        db.query(Site)
        .filter(Site.id == site_id, Site.user_id == owner_id)
        .first()
    )
