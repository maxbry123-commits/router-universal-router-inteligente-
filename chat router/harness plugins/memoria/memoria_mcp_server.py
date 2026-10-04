"""MCP server (stdio) = memory/storage plugin for the DeepSeek Harness (@deepseek-ai/dsh-mcp-client).

Ruta unica: Harness -> este MCP -> Router (/memoria/*, /chat/storage*) -> HF Storage Bucket (permanente).
El Router guarda en SQLite, sincroniza solo al bucket (autosync) y al arrancar vacio restaura del bucket.
Env: RIU_ROUTER_URL (default http://127.0.0.1:8000), RIU_API_KEY (clave de agente del Router).
"""
from __future__ import annotations

import os
from typing import Any

import httpx

try:
    from mcp.server.mcpserver import MCPServer as FastMCP  # mcp 2.x
except ImportError:  # mcp 1.x
    from mcp.server.fastmcp import FastMCP

mcp = FastMCP("memoria")


def _call(method: str, path: str, **kw: Any) -> Any:
    base = os.environ.get("RIU_ROUTER_URL", "http://127.0.0.1:8000").rstrip("/")
    try:
        r = httpx.request(method, base + path, headers={"x-api-key": os.environ.get("RIU_API_KEY", "")}, timeout=60, **kw)
        body = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
        return body if r.status_code < 400 else {"status": "GAP", "http": r.status_code, "detail": body.get("detail")}
    except Exception as exc:  # noqa: BLE001
        return {"status": "GAP", "reason": type(exc).__name__}


@mcp.tool()
def memoria_health() -> Any:
    """Estado de los adaptadores de memoria del Router."""
    return _call("GET", "/memoria/health")


@mcp.tool()
def memoria_save(scope: str, key: str, data: Any) -> Any:
    """Guarda un dato en la memoria del Router."""
    return _call("POST", "/memoria/save", json={"scope": scope, "key": key, "data": data})


@mcp.tool()
def memoria_load(scope: str, key: str) -> Any:
    """Lee los datos guardados con scope+key."""
    return _call("GET", "/memoria/load", params={"scope": scope, "key": key})


@mcp.tool()
def memoria_search(scope: str, query: str, k: int = 10) -> Any:
    """Busca en la memoria (SQLite + grafo)."""
    return _call("GET", "/memoria/search", params={"scope": scope, "query": query, "k": k})


@mcp.tool()
def almacenamiento_estado() -> Any:
    """Estado del almacenamiento del Router y del bucket HF permanente."""
    return _call("GET", "/chat/storage")


@mcp.tool()
def almacenamiento_sync() -> Any:
    """Fuerza copia inmediata del almacenamiento del Router al bucket HF."""
    return _call("POST", "/chat/storage/sync")


# --- Orquestador determinista (CLI-Anything harness en chat router/memoria/agent-harness). Sin LLM. ---
import json as _json
import subprocess as _sp
import sys as _sys
from pathlib import Path as _Path

_HARNESS = _Path(__file__).resolve().parents[2] / 'memoria' / 'agent-harness'


def _orq(*args: str) -> Any:
    env = {**os.environ, 'PYTHONPATH': str(_HARNESS)}
    try:
        r = _sp.run([_sys.executable, '-m', 'cli_anything.memoria', '--json', *args], capture_output=True, text=True, timeout=60, env=env)
        return _json.loads(r.stdout) if r.stdout.strip() else {'status': 'GAP', 'stderr': r.stderr[-200:]}
    except Exception as exc:  # noqa: BLE001
        return {'status': 'GAP', 'reason': type(exc).__name__}


@mcp.tool()
def orquestador_estado() -> Any:
    """Estado (CONNECTED o GAP) de cada motor del pool de memoria y almacenamiento. Determinista, sin LLM."""
    return _orq('motores', 'estado')


@mcp.tool()
def orquestador_guardar(scope: str, key: str, data: dict) -> Any:
    """Guarda data en todos los motores conectados que permiten escribir."""
    return _orq('memoria', 'guardar', scope, key, _json.dumps(data))


@mcp.tool()
def orquestador_cargar(scope: str, key: str) -> Any:
    """Lee (scope, key) del primer motor, por prioridad fija, que lo tenga."""
    return _orq('memoria', 'cargar', scope, key)


@mcp.tool()
def orquestador_buscar(scope: str, query: str, k: int = 10) -> Any:
    """Busca en todos los motores y fusiona el resultado sin repetidos."""
    return _orq('memoria', 'buscar', scope, query, '--k', str(k))


if __name__ == "__main__":
    mcp.run(transport="stdio")
