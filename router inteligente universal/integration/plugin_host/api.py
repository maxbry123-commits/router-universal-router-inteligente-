"""Plugin Host HTTP surface: GET /plugins, POST /plugins/{id}/enable and /disable, plus the gate that switches the chat routes off.

Auth: the same dependency as the other Router endpoints (X-API-Key or Bearer, chat_mvp.router._auth). The chat gate is passed to
include_router(dependencies=...) so no chat file changes; with the chat plugin off, the chat routes answer 503 "plugin chat apagado".
The gate fails open: if the host cannot be read, the chat keeps working.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from ..chat_mvp.router import _auth
from .host import get_host

CHAT_ID = "chat"


async def chat_gate() -> None:
    """503 "plugin chat apagado" while the chat plugin is switched off. Only an in-memory dict lookup (short lock), so it is safe on the event loop."""
    try:
        closed = not get_host().gate_open(CHAT_ID)
    except Exception:  # a broken host must never block the chat
        closed = False
    if closed:
        raise HTTPException(status_code=503, detail="plugin chat apagado")


def chat_gate_dependencies() -> list[Any]:
    """The dependencies to pass to include_router for every chat router. Also creates the host now (reads plugins/ once) instead of on the first chat request."""
    get_host()
    return [Depends(chat_gate)]


def _toggle(plugin_id: str, enabled: bool) -> dict[str, Any]:
    host = get_host()
    record = host.set_enabled(plugin_id, enabled)
    if record is None:
        raise HTTPException(status_code=404, detail="plugin desconocido")
    return {"plugin": record, "state": host.state_info()}


def build_plugin_router() -> APIRouter:
    r = APIRouter()

    @r.get("/plugins")
    def list_plugins(_owner: str = Depends(_auth)) -> dict[str, Any]:
        """Every plugin with status and health (the health action of each plugin runs in-process through the host's call() wrapper)."""
        host = get_host()
        out = []
        for plugin_id in [rec["id"] for rec in host.list_plugins()]:
            health = host.health(plugin_id)  # runs first: it can change status / last_call_ms / last_error, which are read right after
            out.append({**(host.get(plugin_id) or {"id": plugin_id}), "health": health})
        return {"plugins": out, "validator": host.validator_name, "state": host.state_info(), "load_error": host.load_error}

    @r.post("/plugins/{plugin_id}/enable")
    def enable(plugin_id: str, _owner: str = Depends(_auth)) -> dict[str, Any]:
        return _toggle(plugin_id, True)

    @r.post("/plugins/{plugin_id}/disable")
    def disable(plugin_id: str, _owner: str = Depends(_auth)) -> dict[str, Any]:
        return _toggle(plugin_id, False)

    return r
