"""Registro explícito de conectores del Router Inteligente Universal.

No contiene lógica de negocio ni planificación; solo resuelve adapters por clave.
"""
from __future__ import annotations

from red.conector_gitlab import ConectorGitLab
from red.conector_mcp_app import ConectorMCPApp
from red.conectores import (
    ConectorDB,
    ConectorGitHub,
    ConectorHuggingFace,
    ConectorHTTP,
    ConectorInterno,
    ConectorMCP,
    ConectorMemoria,
    ConectorVPS,
    ConectorWebhook,
)

CONNECTOR_REGISTRY = {
    "http": ConectorHTTP,
    "mcp": ConectorMCP,
    "mcp_app": ConectorMCPApp,
    "github": ConectorGitHub,
    "huggingface": ConectorHuggingFace,
    "db": ConectorDB,
    "gitlab": ConectorGitLab,
    "vps": ConectorVPS,
    "memoria": ConectorMemoria,
    "interno": ConectorInterno,
    "webhook": ConectorWebhook,
}


def get_connector_class(kind: str):
    """Devuelve la clase registrada o falla cerrado para kinds desconocidos."""
    try:
        return CONNECTOR_REGISTRY[kind]
    except KeyError as exc:
        raise ValueError(f"conector_no_registrado:{kind}") from exc
