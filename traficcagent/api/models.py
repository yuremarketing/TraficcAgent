"""Modelos SQLAlchemy do TraficcAgent (usuários e sites)."""
from __future__ import annotations

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from traficcagent.db import Base


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    sites: Mapped[list["Site"]] = relationship(back_populates="dono", cascade="all, delete-orphan")


class Site(Base):
    __tablename__ = "sites"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(200), nullable=False)
    nicho: Mapped[str] = mapped_column(String(120), nullable=False)
    responsavel: Mapped[str] = mapped_column(String(80), nullable=False, default="Ana")
    status: Mapped[str] = mapped_column(String(60), nullable=False, default="Planejamento")
    user_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False, index=True)

    dono: Mapped["Usuario"] = relationship(back_populates="sites")
