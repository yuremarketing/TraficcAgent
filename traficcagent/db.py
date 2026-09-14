"""Camada de banco de dados do TraficcAgent (SQLAlchemy).

Usa Postgres em produção via `DATABASE_URL` (bate com o `docker-compose.yml`
— veja `.env.example`). Sem essa variável, cai em SQLite local, suficiente
pra desenvolvimento e testes sem precisar do container do Postgres rodando.
"""
from __future__ import annotations

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import StaticPool

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./traficcagent.db")

_connect_args: dict = {}
_engine_kwargs: dict = {}
if DATABASE_URL.startswith("sqlite"):
    _connect_args = {"check_same_thread": False}
    if ":memory:" in DATABASE_URL:
        # Sem StaticPool, cada conexão sqlite em memória vira um banco novo
        # e vazio — os testes perderiam os dados entre uma query e outra.
        _engine_kwargs["poolclass"] = StaticPool

engine = create_engine(DATABASE_URL, connect_args=_connect_args, **_engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def init_db() -> None:
    """Cria as tabelas que ainda não existem. Idempotente."""
    from traficcagent.api import models  # noqa: F401 — garante que os modelos registrem no Base

    Base.metadata.create_all(bind=engine)


def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
