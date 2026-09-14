"""Ponto de entrada do TraficcAgent.

Exibe o status das integrações no ambiente (smoke test) e inicia o servidor HTTP
FastAPI via uvicorn na porta configurada ($PORT, padrão 8080), atendendo aos
requisitos de execução contínua do Cloud Run e Docker.
"""
from __future__ import annotations

import os
import sys

import uvicorn

from traficcagent.config import load_settings


def print_banner() -> None:
    settings = load_settings()
    print("==================================================")
    print("       TraficcAgent — Servidor Operacional        ")
    print("==================================================")
    print(f"  Google Ads:        {'real' if settings.has_google_ads_credentials else 'mock'}")
    print(f"  Bot do Afiliado:   {'real' if settings.has_affiliate_bot_credentials else 'mock'}")
    print(f"  LLM (conteúdo):    {'real' if settings.has_llm_credentials else 'mock'}")
    print("==================================================")


def main() -> None:
    print_banner()

    if "--smoke-only" in sys.argv or os.environ.get("SMOKE_ONLY") == "1":
        print("Smoke test concluído com sucesso.")
        return

    port = int(os.environ.get("PORT", "8080"))
    host = os.environ.get("HOST", "0.0.0.0")
    print(f"Iniciando servidor HTTP em http://{host}:{port}...")
    uvicorn.run("traficcagent.api.app:app", host=host, port=port, log_level="info")


if __name__ == "__main__":
    main()
