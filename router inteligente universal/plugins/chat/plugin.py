"""Chat plugin entry point for the Plugin Host: exposes the read-only /chat/router/status function, called in-process (no network, no HTTP).

Why: the host needs a health signal for the chat. The status function lives inside build_route_router() (a frozen chat file), so it is
looked up in that router's route table and called directly instead of being copied.
"""
from __future__ import annotations

from typing import Any, Callable

_status_fn: Callable[..., dict[str, Any]] | None = None


def _status() -> dict[str, Any]:
    """Return what GET /chat/router/status returns (the same function object, called without HTTP or auth)."""
    global _status_fn
    if _status_fn is None:
        from integration.chat_mvp.route_api import build_route_router

        found = [r.endpoint for r in build_route_router().routes if getattr(r, "path", "") == "/chat/router/status"]
        if not found:
            raise RuntimeError("no se encontro la ruta /chat/router/status")
        _status_fn = found[0]
    return _status_fn(_owner="plugin-host")


def handle(action: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """Entry point called by the host as handle(action, payload). Only "status" exists (it is also the ficha's allowed_actions)."""
    if action == "status":
        return _status()
    raise ValueError(f"accion desconocida: {action}")
