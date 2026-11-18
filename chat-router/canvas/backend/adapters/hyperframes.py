"""Adaptador HyperFrames (componente autorizado: heygen-com/hyperframes).

Fichero: adapters/hyperframes.py  (1 componente = 1 fichero, FAIL_CLOSED)
Servidor esperado: http://localhost:4000
  - ping   -> GET  /health  (fallback: CLI `hyperframes --version`)
  - render -> POST /render  {"html","duration","format":"mp4"}  -> video_url
Sin API key, sin secretos.

Contrato: ping()/render() devuelven SIEMPRE dict, nunca lanzan.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import urllib.error
import urllib.request
from typing import Any, Dict, Optional

TOOL_ID = "hyperframes"
TOOL_NAME = "HyperFrames"
SOURCE_REPO = "heygen-com/hyperframes"
DEFAULT_BASE_URL = "http://localhost:4000"
PING_COMMAND = "curl -s http://localhost:4000/health"
CLI = "hyperframes"
CLI_PING_COMMAND = "hyperframes --version"
TIMEOUT = 10
RENDER_TIMEOUT = 120


def _base_url() -> str:
    return (os.environ.get("HYPERFRAMES_URL") or DEFAULT_BASE_URL).rstrip("/")


def _request(method: str, path: str, body: Optional[dict] = None, timeout: int = TIMEOUT) -> Dict[str, Any]:
    """Llamada HTTP con urllib. NUNCA lanza; devuelve dict con status/error."""
    url = f"{_base_url()}{path}"
    data = None
    headers = {"Accept": "application/json"}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8", errors="replace")
            status = getattr(response, "status", 200)
    except urllib.error.HTTPError as exc:
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
    ok = 200 <= int(status) < 300
    return {
        "ok": ok,
        "http_status": int(status),
        "status_code": int(status),
        "body": parsed,
        "error": None if ok else f"HTTP {status} en {method} {url}",
        "connection_error": False,
    }


def _cli_version() -> Dict[str, Any]:
    """Fallback CLI: `hyperframes --version`."""
    exe = shutil.which(CLI)
    if not exe:
        return {
            "ok": False,
            "version": None,
            "error": f"CLI '{CLI}' no encontrado en PATH",
        }
    try:
        proc = subprocess.run(
            [exe, "--version"],
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
    except FileNotFoundError as exc:
        return {"ok": False, "version": None, "error": f"FileNotFoundError: {exc}"}
    except subprocess.TimeoutExpired:
        return {"ok": False, "version": None, "error": "TimeoutExpired: exceeded 20s"}
    except Exception as exc:  # pragma: no cover - defensivo
        return {"ok": False, "version": None, "error": f"{type(exc).__name__}: {exc}"}
    if proc.returncode != 0:
        return {
            "ok": False,
            "version": None,
            "error": f"'{CLI} --version' devolvio rc={proc.returncode}: {(proc.stderr or '').strip()[:300]}",
        }
    raw = (proc.stdout or proc.stderr or "").strip()
    return {"ok": True, "version": raw.splitlines()[-1].strip() if raw else None, "error": None}


def ping() -> Dict[str, Any]:
    """Comprueba el servidor HyperFrames; si no responde, prueba el CLI. NUNCA lanza."""
    try:
        res = _request("GET", "/health")
        if res["ok"]:
            body = res.get("body")
            version = None
            if isinstance(body, dict):
                for key in ("version", "appVersion"):
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
        cli = _cli_version()
        if cli["ok"]:
            return {
                "tool": TOOL_ID,
                "status": "OK",
                "reason": f"servidor no disponible, usando CLI: {res['error']}",
                "version": cli["version"],
                "ping_command": CLI_PING_COMMAND,
                "base_url": _base_url(),
                "source_repo": SOURCE_REPO,
            }
        return {
            "tool": TOOL_ID,
            "status": "OMITIDO",
            "reason": f"{res['error']} | CLI: {cli['error']}",
            "ping_command": PING_COMMAND,
            "version": None,
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
        }


def render(payload: Any) -> Dict[str, Any]:
    """Renderiza HTML a video mp4 (POST /render {html,duration,format:"mp4"}).

    payload: dict {"html": str, "duration": int|float, "format": "mp4", "fps": int}
    Devuelve SIEMPRE dict: {"ok","tool","video_url","error"}.
    """
    try:
        if not isinstance(payload, dict):
            return {
                "ok": False,
                "tool": TOOL_ID,
                "error": "payload invalido: se esperaba dict con claves 'html' y 'duration'",
                "video_url": None,
            }
        html = payload.get("html")
        if not isinstance(html, str) or not html.strip():
            return {
                "ok": False,
                "tool": TOOL_ID,
                "error": "payload invalido: falta 'html' no vacio",
                "video_url": None,
            }
        duration = payload.get("duration", 5)
        try:
            duration = float(duration)
        except (TypeError, ValueError):
            return {
                "ok": False,
                "tool": TOOL_ID,
                "error": f"payload invalido: 'duration' no numerico ({duration!r})",
                "video_url": None,
            }
        body = {
            "html": html,
            "duration": duration,
            "format": payload.get("format", "mp4"),
        }
        if payload.get("fps") is not None:
            body["fps"] = payload["fps"]

        res = _request("POST", "/render", body, timeout=RENDER_TIMEOUT)
        if not res["ok"]:
            return {
                "ok": False,
                "tool": TOOL_ID,
                "error": res["error"],
                "video_url": None,
            }
        payload_body = res.get("body")
        video_url = None
        if isinstance(payload_body, dict):
            for key in ("video_url", "videoUrl", "url", "video"):
                if payload_body.get(key):
                    video_url = payload_body[key]
                    break
        if not video_url:
            return {
                "ok": False,
                "tool": TOOL_ID,
                "error": f"respuesta 200 sin 'video_url': {str(payload_body)[:300]}",
                "video_url": None,
            }
        return {
            "ok": True,
            "tool": TOOL_ID,
            "error": None,
            "video_url": video_url,
            "raw": payload_body,
        }
    except Exception as exc:  # pragma: no cover - defensivo
        return {
            "ok": False,
            "tool": TOOL_ID,
            "error": f"{type(exc).__name__}: {exc}",
            "video_url": None,
        }
