"""agent_router.py — Decide a qué agente enviar la tarea basándose en el modo/rol.

FIX (MINIMAX 2E) — el sistema de ESPEJO (mirror) estaba declarado pero vacío:
ningún agente tenía `mirror_endpoint` y `route_task()` devolvía `None` para
los agentes offline, así que el espejo no existía de hecho. Además el registro
no lo consumía nadie: los agentes estaban "cableados" solo en el papel.

FIX (MINIMAX 2F) — el registro ahora tiene 6 agentes (se añaden ruflo y
rowboat, las dos raices reales del workspace), cada uno con interruptor
ON/OFF real, memoria e historial propios, y las 3 raices del workspace
declaradas para el auto-pull.

Orden de decision:
  1. El agente existe en el registro.
  2. El interruptor ON/OFF esta en ON (estado persistido > registro).
  3. Endpoint principal si el agente esta activo; espejo como respaldo.
"""
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

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


def is_enabled(agent_name: str, registry: Optional[Dict[str, Any]] = None) -> bool:
    """Interruptor real del agente (estado persistido > valor del registro)."""
    try:
        from router_llm_hf.agent_state import is_enabled as _state_enabled
        return bool(_state_enabled(agent_name, registry if registry is not None else load_registry()))
    except Exception as exc:  # fail-closed: sin estado => apagado
        logger.warning(f"estado de {agent_name} no legible ({exc}); se trata como OFF")
        return False


def set_agent_enabled(agent_name: str, enabled: bool, reason: str = "") -> Dict[str, Any]:
    """Enciende/apaga un agente de forma persistente."""
    if not get_agent(agent_name):
        raise KeyError(f"agente desconocido: {agent_name}")
    from router_llm_hf.agent_state import set_enabled as _set
    return _set(agent_name, enabled, reason)


def route_task(agent_name: str, use_mirror: bool = False) -> Optional[str]:
    """Devuelve el endpoint correcto para el agente.

    Prioridad: interruptor ON/OFF -> endpoint principal (si está activo) ->
    espejo (si lo hay). Un agente apagado NO se enruta (None).
    """
    registry = load_registry()
    agent = registry.get("agents", {}).get(agent_name)
    if not agent:
        logger.warning(f"Agente {agent_name} no encontrado en el registro.")
        return None

    if not is_enabled(agent_name, registry):
        logger.info(f"Agente {agent_name} esta OFF: no se enruta.")
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


def get_all_active_agents() -> List[str]:
    """Agentes con interruptor ON (encendidos de verdad)."""
    registry = load_registry()
    return [
        name
        for name in registry.get("agents", {}).keys()
        if is_enabled(name, registry)
    ]


def get_agents_with_mirror() -> List[str]:
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


def list_agents() -> Dict[str, Any]:
    """Inventario vivo de agentes: registro + interruptor + memoria + historial.

    Es lo que consume el selector del chat (nada hardcodeado en el frontend).
    """
    registry = load_registry()
    agents: Dict[str, Any] = {}
    for name, cfg in (registry.get("agents") or {}).items():
        agent_state: Dict[str, Any] = {}
        try:
            from router_llm_hf import agent_state as st
            agent_state = {
                "enabled": st.is_enabled(name, registry),
                "history_count": st.history_count(name),
                "memory_keys": sorted(st.memory_keys(name)),
            }
        except Exception as exc:
            agent_state = {"enabled": False, "history_count": 0, "memory_keys": [], "error": str(exc)}
        agents[name] = {
            "type": cfg.get("type"),
            "status": cfg.get("status"),
            "declared_enabled": bool(cfg.get("enabled", str(cfg.get("status", "active")).lower() == "active")),
            "enabled": bool(agent_state.get("enabled")),
            "endpoint": cfg.get("endpoint"),
            "mirror_endpoint": cfg.get("mirror_endpoint"),
            "chat_path": cfg.get("chat_path"),
            "module": cfg.get("module"),
            "root": cfg.get("root"),
            "role": cfg.get("role"),
            "tools": cfg.get("tools") or [],
            "history_count": agent_state.get("history_count", 0),
            "memory_keys": agent_state.get("memory_keys", []),
            "memory": cfg.get("memory"),
            "verificacion": cfg.get("verificacion"),
        }
    return {
        "ok": True,
        "version": registry.get("version"),
        "base_url": registry.get("base_url"),
        "agents": agents,
        "roots": registry.get("roots") or {},
        "policy": registry.get("policy") or {},
    }
