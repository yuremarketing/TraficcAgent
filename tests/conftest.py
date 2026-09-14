"""Fixtures compartilhadas dos testes de API: banco limpo e sessões
zeradas a cada teste, pra um teste nunca vazar usuário/site pro outro."""
import pytest

from traficcagent.api.auth import reset_sessions
from traficcagent.db import Base, engine


@pytest.fixture(autouse=True)
def banco_limpo():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    reset_sessions()
    yield
