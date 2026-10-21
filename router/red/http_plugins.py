"""Cliente HTTP delgado entre edificios: POST {RIU_ROUTER_URL}/plugins/<id>/call/<accion>.

El edificio 1 (router/fichas) NO importa codigo de plugins/ (edificio 2): llama por aqui.
Env: RIU_ROUTER_URL (base, p.ej. http://127.0.0.1:7860), RIU_API_KEY (cabecera X-API-Key).
"""
from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from typing import Any

_ID = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


def llamar(plugin: str, accion: str, payload: dict | None = None, timeout: float = 120.0) -> Any:
    """Devuelve el `result` del host si status=ok; si no, {'error': motivo, 'status': ...}."""
    base = (os.environ.get("RIU_ROUTER_URL", "").strip() or "http://127.0.0.1:" + os.environ.get("PORT", "7860")).rstrip("/")
    if not base:
        return {"error": "RIU_ROUTER_URL no definida", "status": "degraded"}
    if not (_ID.match(str(plugin)) and _ID.match(str(accion))):
        return {"error": "plugin/accion invalidos", "status": "degraded"}
    headers = {"Content-Type": "application/json"}
    key = os.environ.get("RIU_API_KEY") or os.environ.get("RIU_PUBLIC_CHAT_KEY", "")
    if key:
        headers["X-API-Key"] = key
    req = urllib.request.Request(f"{base}/plugins/{plugin}/call/{accion}", data=json.dumps(payload or {}).encode(), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            out = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        motivo = ""
        try:
            cuerpo = json.loads(exc.read().decode("utf-8", "replace") or "{}")
            if isinstance(cuerpo, dict):
                motivo = str(cuerpo.get("reason") or cuerpo.get("detail") or "")[:200]
        except Exception:  # noqa: BLE001
            motivo = ""
        return {"error": f"HTTP {exc.code}" + (f": {motivo}" if motivo else ""), "status": "degraded"}
    except (OSError, ValueError) as exc:
        return {"error": type(exc).__name__, "status": "degraded"}
    if isinstance(out, dict) and out.get("status") == "ok":
        return out.get("result")
    return {"error": str((out or {}).get("reason") or "fallo"), "status": str((out or {}).get("status") or "degraded")}
