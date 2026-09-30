"""connectivity: reporte ok/degraded/off por transporte (FastAPI, HTTP saliente, MCP). No inventa clientes.

Acciones: status (solo configuracion, sin red; es la accion de salud) y check (sondea).
FastAPI: GET <RIU_SELF_URL o http://127.0.0.1:$PORT(7860)><fastapi_health_path>. ok=200, degraded=otra respuesta/error, off=sin conexion.
HTTP saliente: allowlist de hosts en config.json (override RIU_HTTP_ALLOWLIST=a,b); vacia -> off. Se sondea cada host (HEAD https).
MCP: solo si hay cliente configurado (RIU_MCP_URL, o RIU_MCP_CONFIG / .mcp.json existente); si no -> off.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

HERE = Path(__file__).resolve().parent
APP_ROOT = HERE.parents[1]
PROBE_TIMEOUT = 3.0


def _config() -> dict[str, Any]:
    try:
        cfg = json.loads((HERE / "config.json").read_text(encoding="utf-8"))
        return cfg if isinstance(cfg, dict) else {}
    except (OSError, ValueError):
        return {}


def allowlist() -> list[str]:
    env = os.getenv("RIU_HTTP_ALLOWLIST")
    raw = env.split(",") if env is not None else (_config().get("http_allowlist") or [])
    return [h.strip().lower() for h in raw if isinstance(h, str) and h.strip()]


def allowed(url: str) -> bool:
    host = (urlparse(url).hostname or "").lower()
    return bool(host) and host in allowlist()


def _self_url() -> str:
    return (os.getenv("RIU_SELF_URL") or f"http://127.0.0.1:{os.getenv('PORT') or 7860}").rstrip("/")


def _mcp_source() -> str | None:
    if (os.getenv("RIU_MCP_URL") or "").strip():
        return "url"
    for cand in (os.getenv("RIU_MCP_CONFIG"), str(APP_ROOT / ".mcp.json"), str(Path.cwd() / ".mcp.json")):
        if cand and Path(cand).is_file():
            return "config:" + Path(cand).name
    return None


def _get(url: str, method: str = "GET") -> tuple[int | None, str | None]:
    req = urllib.request.Request(url, method=method)
    try:
        with urllib.request.urlopen(req, timeout=PROBE_TIMEOUT) as r:  # noqa: S310
            return r.status, None
    except urllib.error.HTTPError as exc:
        return exc.code, None
    except Exception as exc:
        return None, type(exc).__name__


def _fastapi() -> dict[str, Any]:
    url = _self_url() + str(_config().get("fastapi_health_path") or "/health")
    code, err = _get(url)
    if code == 200:
        return {"status": "ok", "url": url}
    if code is not None:
        return {"status": "degraded", "url": url, "reason": f"HTTP {code}"}
    return {"status": "off", "url": url, "reason": err}


def _http() -> dict[str, Any]:
    hosts = allowlist()
    if not hosts:
        return {"status": "off", "reason": "allowlist vacia: HTTP saliente no permitido", "allowlist": []}
    with ThreadPoolExecutor(max_workers=min(8, len(hosts))) as pool:
        probes = list(pool.map(lambda h: (h, *_get(f"https://{h}/", "HEAD")), hosts))
    detail = {h: (code if code is not None else err) for h, code, err in probes}
    up = sum(1 for _, code, _ in probes if code is not None)
    status = "ok" if up == len(hosts) else ("degraded" if up else "off")
    return {"status": status, "allowlist": hosts, "hosts": detail}


def _mcp() -> dict[str, Any]:
    src = _mcp_source()
    if src is None:
        return {"status": "off", "reason": "no hay cliente MCP configurado"}
    if src == "url":
        url = os.environ["RIU_MCP_URL"].strip()
        code, err = _get(url)
        if code is not None:
            return {"status": "ok" if code < 500 else "degraded", "source": src, "http": code}
        return {"status": "degraded", "source": src, "reason": err}
    return {"status": "degraded", "source": src, "reason": "cliente configurado pero su conexion no se verifica aqui"}


def _ssh() -> dict[str, Any]:
    try:  # transporte opcional: plugin ssh_bridge (sin red, solo configuracion)
        from plugins.ssh_bridge import plugin as _sb
        return _sb.status()
    except Exception as exc:
        return {"status": "off", "reason": "ssh_bridge no disponible: " + type(exc).__name__}


def _overall(parts: dict[str, dict[str, Any]]) -> str:
    states = [p["status"] for p in parts.values()]
    if all(s == "off" for s in states):
        return "off"
    return "ok" if all(s in ("ok", "off") for s in states) else "degraded"


def handle(action: str, payload: dict[str, Any] | None) -> dict[str, Any]:
    if action == "status":  # sin red: rapida, es la accion de salud del host
        return {"status": "ok", "config": {"fastapi_url": _self_url(), "http_allowlist": allowlist(), "mcp_configurado": _mcp_source() is not None}}
    if action != "check":
        return {"status": "degraded", "reason": "accion desconocida"}
    parts = {"fastapi": _fastapi(), "http": _http(), "mcp": _mcp(), "ssh": _ssh()}
    return {"status": _overall(parts), "transports": parts}
