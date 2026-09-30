"""deepseek_harness: wrapper removible de la regla Fables s8. Sin dependencia dura: sin URL -> degraded.

Acciones: status, invoke. Env: RIU_DEEPSEEK_HARNESS_URL (base), RIU_DEEPSEEK_HARNESS_API_KEY (opcional), RIU_DEEPSEEK_HARNESS_PATH (def /invoke).
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any


def _url() -> str:
    return (os.getenv("RIU_DEEPSEEK_HARNESS_URL") or "").strip().rstrip("/")


def _degraded(reason: str) -> dict[str, Any]:
    return {"status": "degraded", "reason": reason}


def handle(action: str, payload: dict[str, Any] | None) -> dict[str, Any]:
    payload = payload or {}
    base = _url()
    if action == "status":
        if not base:
            return _degraded("sin RIU_DEEPSEEK_HARNESS_URL: harness no configurado")
        return {"status": "ok", "configured": True, "url": base.split("?")[0]}
    if action != "invoke":
        return _degraded("accion desconocida")
    if not base:
        return _degraded("sin RIU_DEEPSEEK_HARNESS_URL: harness no configurado")
    path = os.getenv("RIU_DEEPSEEK_HARNESS_PATH") or "/invoke"
    headers = {"Content-Type": "application/json"}
    key = os.getenv("RIU_DEEPSEEK_HARNESS_API_KEY")
    if key:
        headers["Authorization"] = "Bearer " + key
    req = urllib.request.Request(base + path, data=json.dumps(payload).encode(), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:  # noqa: S310 (URL fijada por el operador via env)
            raw = resp.read(1_000_000).decode("utf-8", "replace")
            try:
                body: Any = json.loads(raw)
            except ValueError:
                body = raw
            return {"status": "ok", "http_status": resp.status, "response": body}
    except urllib.error.HTTPError as exc:
        return _degraded(f"harness respondio HTTP {exc.code}")
    except Exception as exc:
        return _degraded(f"harness inalcanzable: {type(exc).__name__}")
