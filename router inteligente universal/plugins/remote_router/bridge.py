"""HTTP bridge plugin for one external Router.

Configure only environment variables; no code changes are needed:
RIU_REMOTE_ROUTER_URL=https://...
RIU_REMOTE_ROUTER_API_KEY=...
RIU_REMOTE_ROUTER_INVOKE_PATH=/chat/send
RIU_REMOTE_ROUTER_MODELS_PATH=/chat/models
"""
from __future__ import annotations

import os
from typing import Any

import httpx


def _base_url() -> str:
    return os.getenv("RIU_REMOTE_ROUTER_URL", "").strip().rstrip("/")


def _headers() -> dict[str, str]:
    key = os.getenv("RIU_REMOTE_ROUTER_API_KEY", "").strip()
    if not key:
        return {}
    header = os.getenv("RIU_REMOTE_ROUTER_AUTH_HEADER", "X-API-Key").strip() or "X-API-Key"
    prefix = os.getenv("RIU_REMOTE_ROUTER_AUTH_PREFIX", "")
    return {header: prefix + key}


def _path(name: str, default: str) -> str:
    value = os.getenv(name, default).strip()
    return value if value.startswith("/") else "/" + value


def handle(action: str, payload: dict[str, Any]) -> dict[str, Any]:
    base = _base_url()
    if not base:
        return {"status": "degraded", "reason": "RIU_REMOTE_ROUTER_URL no configurado"}

    timeout = float(os.getenv("RIU_REMOTE_ROUTER_TIMEOUT_S", "60"))
    try:
        with httpx.Client(timeout=timeout, headers=_headers()) as client:
            if action == "status":
                r = client.get(base + _path("RIU_REMOTE_ROUTER_HEALTH_PATH", "/health"))
            elif action == "models":
                r = client.get(base + _path("RIU_REMOTE_ROUTER_MODELS_PATH", "/chat/models"))
            elif action == "invoke":
                r = client.post(
                    base + _path("RIU_REMOTE_ROUTER_INVOKE_PATH", "/chat/send"),
                    json=payload or {},
                )
            else:
                return {"status": "degraded", "reason": f"accion no soportada: {action}"}

        if r.status_code >= 400:
            return {
                "status": "degraded",
                "http_status": r.status_code,
                "reason": r.text[:500],
            }
        try:
            body: Any = r.json()
        except ValueError:
            body = {"text": r.text}
        return {"status": "ok", "http_status": r.status_code, "result": body}
    except Exception as exc:
        return {"status": "degraded", "reason": f"{type(exc).__name__}: {str(exc)[:300]}"}
