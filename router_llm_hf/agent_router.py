"""agent_router.py — Decide a qué agente enviar la tarea basándose en el modo/rol."""
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)
REGISTRY_PATH = Path(__file__).parent / "AGENTS_REGISTRY.json"

def load_registry() -> Dict[str, Any]:
    if not REGISTRY_PATH.exists():
        return {"agents": {}}
    with open(REGISTRY_PATH, "r") as f:
        return json.load(f)

def route_task(agent_name: str, use_mirror: bool = False) -> Optional[str]:
    """Devuelve el endpoint correcto para el agente."""
    registry = load_registry()
    agent = registry.get("agents", {}).get(agent_name)
    
    if not agent:
        logger.warning(f"Agente {agent_name} no encontrado en el registro.")
        return None

    if agent["status"] != "active":
        logger.warning(f"Agente {agent_name} no está activo.")
        return None

    if use_mirror and agent.get("mirror_endpoint"):
        return agent["mirror_endpoint"]
    
    return agent["endpoint"]

def get_all_active_agents() -> list:
    registry = load_registry()
    return [name for name, data in registry.get("agents", {}).items() if data.get("status") == "active"]
