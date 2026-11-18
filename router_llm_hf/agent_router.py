"""agent_router.py — Decide a qué agente enviar la tarea basándose en el modo/rol.

FIX (MINIMAX 2E) — el sistema de ESPEJO (mirror) estaba declarado pero vacío:
ningún agente tenía `mirror_endpoint` y `route_task()` devolvía `None` para
los agentes offline, así que el espejo no existía de hecho. Además el registro
no lo consumía nadie: los agentes estaban "cableados" solo en el papel.

Ahora:
  · cada agente declara endpoint + espejo + ruta de chat,
  · `route_task()` cae al espejo cuando el endpoint principal no está activo,
  · hay helpers para el cableado con el chat y para listar los agentes.
"""
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)
REGISTRY_PATH = Path(__file__).parent / "AGENTS_REGISTRY.json"


def load_registry() -> Dict[str, Any]:
    if not REGISTRY_PATH.exists():
        return {"agents": {}}
    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def get_agent(agent_name: str) -> Optional[dict]:
    """Ficha de un agente del registro central (None si no existe)."""
    return load_registry().get("agents", {}).get(agent_name)


def route_task(agent_name: str, use_mirror: bool = False) -> Optional[str]:
    """Devuelve el endpoint correcto para el agente.

    Prioridad: endpoint principal (si está activo) → espejo (si lo hay).
    """
    agent = get_agent(agent_name)
    if not agent:
        logger.warning(f"Agente {agent_name} no encontrado en el registro.")
        return None

    mirror = agent.get("mirror_endpoint")
    if agent.get("status") == "active" and agent.get("endpoint"):
        if not use_mirror:
            return agent["endpoint"]
        return mirror or agent["endpoint"]

    if mirror:
        logger.info(f"Agente {agent_name} no activo: se usa el espejo ({mirror}).")
        return mirror

    logger.warning(f"Agente {agent_name} no está activo y no tiene espejo.")
    return None


def get_all_active_agents() -> list:
    registry = load_registry()
    return [
        name
        for name, data in registry.get("agents", {}).items()
        if data.get("status") == "active"
    ]


def get_agents_with_mirror() -> list:
    """Agentes que tienen espejo (los que el chat puede reflejar)."""
    registry = load_registry()
    return [
        name
        for name, data in registry.get("agents", {}).items()
        if data.get("mirror_endpoint")
    ]


def chat_endpoint_for(agent_name: str, base_url: str = "") -> Optional[str]:
    """Endpoint HTTP que el chat usa para ese agente.

    Si el agente declara `chat_path`, se devuelve base_url + chat_path; si no,
    se cae al endpoint principal.
    """
    agent = get_agent(agent_name)
    if not agent:
        return None
    path = agent.get("chat_path")
    if path:
        return f"{base_url.rstrip('/')}{path}" if base_url else path
    return route_task(agent_name)
