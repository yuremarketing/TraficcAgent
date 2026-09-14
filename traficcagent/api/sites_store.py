"""Armazenamento de sites do TraficcAgent.

Oferece repositório em memória com interface desacoplada, preparado para
que a Etapa 2 (Postgres / tabelas `usuarios` e `sites`) conecte a persistência
em banco relacional sem alterar os contratos dos endpoints.
"""
from __future__ import annotations

import threading
from typing import Any, Optional


DEFAULT_SITES: list[dict[str, Any]] = [
    {
        "id": 1,
        "nome": "Casa que Pensa",
        "nicho": "Casa inteligente",
        "responsavel": "Ana",
        "status": "Publicado",
        "user_id": "yure",
    },
    {
        "id": 2,
        "nome": "Café de Origem",
        "nicho": "Cafés especiais",
        "responsavel": "Bruno",
        "status": "Produção",
        "user_id": "philipy",
    },
    {
        "id": 3,
        "nome": "Escolha Pet",
        "nicho": "Cuidados para pets",
        "responsavel": "Carla",
        "status": "Revisão",
        "user_id": "yure",
    },
    {
        "id": 4,
        "nome": "Ferramenta Certa",
        "nicho": "Ferramentas domésticas",
        "responsavel": "Bruno",
        "status": "Pauta pronta",
        "user_id": "philipy",
    },
]


class SitesStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._sites: list[dict[str, Any]] = [dict(s) for s in DEFAULT_SITES]
        self._next_id = 5

    def list_sites(self, user_id: Optional[str] = None) -> list[dict[str, Any]]:
        with self._lock:
            if user_id:
                return [dict(s) for s in self._sites if s.get("user_id") == user_id]
            return [dict(s) for s in self._sites]

    def add_site(
        self,
        nome: str,
        nicho: str,
        responsavel: str = "Ana",
        status: str = "Planejamento",
        user_id: Optional[str] = None,
    ) -> dict[str, Any]:
        with self._lock:
            site = {
                "id": self._next_id,
                "nome": nome.strip(),
                "nicho": nicho.strip(),
                "responsavel": responsavel.strip(),
                "status": status.strip(),
                "user_id": user_id.strip() if user_id else None,
            }
            self._next_id += 1
            self._sites.insert(0, site)
            return dict(site)

    def get_site(self, site_id: int) -> Optional[dict[str, Any]]:
        with self._lock:
            for s in self._sites:
                if s["id"] == site_id:
                    return dict(s)
            return None

    def reset(self) -> None:
        with self._lock:
            self._sites = [dict(s) for s in DEFAULT_SITES]
            self._next_id = 5


# Instância singleton padrão para uso na API
store = SitesStore()
