"""Autenticação de sessão simples do TraficcAgent (issue #27).

Sem OAuth/SSO nesta rodada — login por usuário/senha, sessão por token
opaco guardado em memória do processo (reiniciar o servidor desloga todo
mundo; é uma limitação conhecida, não um bug — persistência de sessão
fica pra uma rodada futura).
"""
from __future__ import annotations

import secrets
from typing import Optional

import bcrypt
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from traficcagent.api.models import Usuario
from traficcagent.db import get_db


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


# token opaco -> id do usuário. Estado do processo, não do banco.
_SESSIONS: dict[str, int] = {}


def create_session(user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    _SESSIONS[token] = user_id
    return token


def reset_sessions() -> None:
    """Uso exclusivo de testes, pra isolar sessões entre casos."""
    _SESSIONS.clear()


def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
) -> Usuario:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Autenticação necessária (Authorization: Bearer <token>).",
        )
    token = authorization[len("Bearer "):]
    user_id = _SESSIONS.get(token)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sessão inválida ou expirada.",
        )
    usuario = db.get(Usuario, user_id)
    if usuario is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário da sessão não existe mais.",
        )
    return usuario
