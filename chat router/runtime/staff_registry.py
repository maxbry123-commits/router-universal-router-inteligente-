"""Lectura del registro de staff (staff.yaml) y rutas compartidas del runtime del chat."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

RUNTIME = Path(__file__).resolve().parent
REPO = RUNTIME.parents[1]
STAFF_YAML = RUNTIME / "staff.yaml"
STAFF_DIR = REPO / "router inteligente universal" / "agents-yaiwes" / "staff"
EVIDENCIA = REPO / "chat router" / "EVIDENCIA"


def registro() -> dict[str, Any]:
    return yaml.safe_load(STAFF_YAML.read_text(encoding="utf-8"))


def miembros() -> list[dict[str, Any]]:
    return registro()["miembros"]


def miembro(agent_id: str) -> dict[str, Any]:
    for m in miembros():
        if m["id"] == agent_id:
            return m
    raise KeyError(f"agente desconocido: {agent_id}")


def cadena() -> list[str]:
    return registro()["cadena_de_trabajo"]
