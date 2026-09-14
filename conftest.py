"""Configuração compartilhada de testes.

Fixa DATABASE_URL num SQLite em memória ANTES de qualquer módulo do
traficcagent ser importado pelos testes — assim a suíte nunca toca no
Postgres real de produção, mesmo que DATABASE_URL esteja setado no
ambiente de quem está rodando os testes.
"""
import os

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
