"""Cliente HTTP del edificio 2 hacia el plugin `router_api` del edificio 1 (nunca importa integration.chat_mvp).

POST {RIU_ROUTER_URL}/plugins/<id>/call/<accion>, cabecera X-API-Key de RIU_API_KEY.
"""
from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request
from typing import Any

_ID = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


def llamar(plugin: str, accion: str, payload: dict | None = None, timeout: float = 120.0) -> Any:
    """Devuelve el `result` del host si status=ok; si no, {'error': motivo, 'status': 'degraded'}."""
    base = (os.environ.get("RIU_ROUTER_URL", "").strip() or "http://127.0.0.1:" + os.environ.get("PORT", "7860")).rstrip("/")
    if not base:
        return {"error": "RIU_ROUTER_URL no definida", "status": "degraded"}
    if not (_ID.match(str(plugin)) and _ID.match(str(accion))):
        return {"error": "plugin/accion invalidos", "status": "degraded"}
    headers = {"Content-Type": "application/json"}
    key = os.environ.get("RIU_API_KEY") or os.environ.get("RIU_PUBLIC_CHAT_KEY", "")
    if key:
        headers["X-API-Key"] = key
    req = urllib.request.Request(f"{base}{'/' + accion if plugin == 'router_mvp' and accion in ('chat', 'almacen') else '/plugins/' + plugin + '/call/' + accion}", data=json.dumps(payload or {}, default=str).encode(), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            out = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        return {"error": f"HTTP {exc.code}", "status": "degraded"}  # inv. 9: solo el codigo, sin reason/detail del servidor
    except (OSError, ValueError) as exc:
        return {"error": type(exc).__name__, "status": "degraded"}
    if isinstance(out, dict) and (out.get("status") == "ok" or (plugin == "router_mvp" and accion in ("chat", "almacen"))):
        return out if plugin == "router_mvp" else out.get("result")
    return {"error": str((out or {}).get("reason") or "fallo"), "status": str((out or {}).get("status") or "degraded")}


def _api(accion: str, payload: dict, timeout: float = 120.0) -> dict:
    r = llamar("router_api", accion, payload, timeout)
    if not isinstance(r, dict) or r.get("status") != "ok":
        raise RuntimeError("router_api.%s: %s" % (accion, (r or {}).get("error") or (r or {}).get("reason") or "fallo"))
    return r


class _Sqlite:
    def save(self, *a, **k):
        return _api("memoria", {"op": "sqlite_save", "args": list(a), "kwargs": k})["valor"]

    def load(self, *a, **k):
        return _api("memoria", {"op": "sqlite_load", "args": list(a), "kwargs": k})["valor"]

    def health(self, *a, **k):
        return _api("memoria", {"op": "sqlite_health", "args": list(a), "kwargs": k})["valor"]


class MemoriaRemota:
    """Misma superficie que memoria_loader._memory() (save/load/search/sqlite.*), por HTTP."""

    sqlite = _Sqlite()

    def save(self, *a, **k):
        return _api("memoria", {"op": "save", "args": list(a), "kwargs": k})["valor"]

    def load(self, *a, **k):
        return _api("memoria", {"op": "load", "args": list(a), "kwargs": k})["valor"]

    def search(self, *a, **k):
        return _api("memoria", {"op": "search", "args": list(a), "kwargs": k})["valor"]


_MEM = MemoriaRemota()


def memory() -> MemoriaRemota:
    return _MEM


def env_keys(proveedor: str) -> list:
    return list(_api("env_keys", {"proveedor": proveedor})["claves"])


def base_url(proveedor: str) -> str:
    return _api("base_url", {"proveedor": proveedor})["url"]


def provider_keys(proveedor: str) -> list:
    r = llamar("router_api", "provider_keys", {"proveedor": proveedor})
    nivel = None
    if isinstance(r, dict) and not r.get("error"):
        sub = r.get("result") if isinstance(r.get("result"), dict) else {}
        if r.get("status") == "ok" and "claves" in r:
            nivel = r
        elif sub.get("status") == "ok":
            nivel = sub
        elif r.get("status") == "ok":
            nivel = r
    if nivel is None:
        err = (r.get("error") or r.get("reason") or "fallo") if isinstance(r, dict) else type(r).__name__
        print("PROVIDER_KEYS_FALLO proveedor=%s error=%s" % (proveedor, str(err)[:200]), file=sys.stderr)  # nunca la clave
        return []
    return list(nivel.get("claves") or [])


def chat(proveedor: str, modelo: str, mensajes: list, max_tokens: int, tope: int) -> dict:
    _tope = float(tope) if tope is not None else 120.0
    return _api("chat", {"proveedor": proveedor, "modelo": modelo, "mensajes": mensajes, "max_tokens": max_tokens, "tope": tope}, timeout=max(120.0, _tope + 15))["respuesta"]
