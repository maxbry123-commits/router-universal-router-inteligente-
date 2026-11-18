"""Adaptador Excalidraw (componente autorizado: github.com/excalidraw/excalidraw).

Fichero: adapters/excalidraw.py  (1 componente = 1 fichero, FAIL_CLOSED)
Servidor esperado: API local de Excalidraw en http://localhost:3010
  - ping        -> GET  /api/v1/health
  - render      -> POST /api/v1/elements
  - from_mermaid-> POST /api/v1/convert
Sin API key, sin secretos (solo URL local, configurable por variable de entorno).

Contrato: ping()/render()/from_mermaid() devuelven SIEMPRE dict, nunca lanzan.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any, Dict, Optional

TOOL_ID = "excalidraw"
TOOL_NAME = "Excalidraw"
SOURCE_REPO = "github.com/excalidraw/excalidraw"
DEFAULT_BASE_URL = "http://localhost:3010"
PING_COMMAND = "curl -s http://localhost:3010/api/v1/health"
TIMEOUT = 10


def _base_url() -> str:
    return (os.environ.get("EXCALIDRAW_URL") or DEFAULT_BASE_URL).rstrip("/")


def _request(method: str, path: str, body: Optional[dict] = None) -> Dict[str, Any]:
    """Llamada HTTP con urllib. NUNCA lanza; devuelve dict con status/error."""
    url = f"{_base_url()}{path}"
    data = None
    headers = {"Accept": "application/json"}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            raw = response.read().decode("utf-8", errors="replace")
            status = getattr(response, "status", 200)
    except urllib.error.HTTPError as exc:
        raw = ""
        try:
            raw = exc.read().decode("utf-8", errors="replace")
        except Exception:
            raw = ""
        return {
            "ok": False,
            "http_status": int(exc.code),
            "status_code": int(exc.code),
            "body": raw[:1000],
            "error": f"HTTP {exc.code} en {method} {url}: {raw[:200]}",
            "connection_error": False,
        }
    except urllib.error.URLError as exc:
        return {
            "ok": False,
            "http_status": None,
            "status_code": None,
            "body": "",
            "error": f"conexion fallida {method} {url}: {exc.reason}",
            "connection_error": True,
        }
    except Exception as exc:  # pragma: no cover - defensivo
        return {
            "ok": False,
            "http_status": None,
            "status_code": None,
            "body": "",
            "error": f"{type(exc).__name__} en {method} {url}: {exc}",
            "connection_error": True,
        }

    parsed: Any = raw
    if raw:
        try:
            parsed = json.loads(raw)
        except Exception:
            parsed = raw
    return {
        "ok": 200 <= int(status) < 300,
        "http_status": int(status),
        "status_code": int(status),
        "body": parsed,
        "error": None if 200 <= int(status) < 300 else f"HTTP {status} en {method} {url}",
        "connection_error": False,
    }


def ping() -> Dict[str, Any]:
    """Comprueba el servidor local de Excalidraw. NUNCA lanza."""
    try:
        res = _request("GET", "/api/v1/health")
        if not res["ok"]:
            return {
                "tool": TOOL_ID,
                "status": "OMITIDO",
                "reason": res["error"],
                "ping_command": PING_COMMAND,
                "version": None,
                "source_repo": SOURCE_REPO,
                "base_url": _base_url(),
            }
        body = res.get("body")
        version = None
        if isinstance(body, dict):
            for key in ("version", "appVersion", "commit"):
                if body.get(key):
                    version = str(body[key])
                    break
        return {
            "tool": TOOL_ID,
            "status": "OK",
            "reason": None,
            "version": version,
            "ping_command": PING_COMMAND,
            "base_url": _base_url(),
            "source_repo": SOURCE_REPO,
        }
    except Exception as exc:  # pragma: no cover - defensivo
        return {
            "tool": TOOL_ID,
            "status": "OMITIDO",
            "reason": f"{type(exc).__name__}: {exc}",
            "ping_command": PING_COMMAND,
            "version": None,
            "source_repo": SOURCE_REPO,
            "base_url": _base_url(),
        }


def render(payload: Any) -> Dict[str, Any]:
    """Convierte elementos Excalidraw en un diagrama (POST /api/v1/elements).

    payload: dict {"elements": [...], "appState": {...}, "files": {...}}
             o directamente una lista de elementos.
    Devuelve SIEMPRE dict: {"ok","tool","elements","error"}.
    """
    try:
        if payload is None:
            body: Dict[str, Any] = {"elements": []}
        elif isinstance(payload, list):
            body = {"elements": payload}
        elif isinstance(payload, dict):
            body = dict(payload)
            body.setdefault("elements", [])
        else:
            return {
                "ok": False,
                "tool": TOOL_ID,
                "error": "payload invalido: se esperaba dict o lista de elementos",
                "elements": None,
            }

        res = _request("POST", "/api/v1/elements", body)
        if not res["ok"]:
            return {
                "ok": False,
                "tool": TOOL_ID,
                "error": res["error"],
                "elements": None,
            }
        elements = res.get("body")
        if isinstance(elements, dict):
            elements = elements.get("elements", elements)
        return {
            "ok": True,
            "tool": TOOL_ID,
            "error": None,
            "elements": elements,
        }
    except Exception as exc:  # pragma: no cover - defensivo
        return {
            "ok": False,
            "tool": TOOL_ID,
            "error": f"{type(exc).__name__}: {exc}",
            "elements": None,
        }


def from_mermaid(code: Any) -> Dict[str, Any]:
    """Convierte codigo mermaid a elementos Excalidraw (POST /api/v1/convert).

    code: str con el diagrama mermaid.
    Devuelve SIEMPRE dict: {"ok","tool","elements","error"}.
    """
    try:
        if not isinstance(code, str) or not code.strip():
            return {
                "ok": False,
                "tool": TOOL_ID,
                "error": "codigo mermaid vacio o de tipo invalido",
                "elements": None,
            }
        res = _request("POST", "/api/v1/convert", {"code": code})
        if not res["ok"]:
            return {
                "ok": False,
                "tool": TOOL_ID,
                "error": res["error"],
                "elements": None,
            }
        elements = res.get("body")
        if isinstance(elements, dict):
            elements = elements.get("elements", elements)
        return {
            "ok": True,
            "tool": TOOL_ID,
            "error": None,
            "elements": elements,
        }
    except Exception as exc:  # pragma: no cover - defensivo
        return {
            "ok": False,
            "tool": TOOL_ID,
            "error": f"{type(exc).__name__}: {exc}",
            "elements": None,
        }
