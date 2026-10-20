"""Servidor MCP JSON-RPC (streamable-HTTP). Nucleo puro (handle_http) + montaje FastAPI opcional.
Auth: Authorization: Bearer / X-API-Key; ?key= solo por compatibilidad con conectores; nunca se registra."""
from __future__ import annotations
import hmac
import json

from . import config, tools

try:  # Request a nivel de modulo: con `from __future__ import annotations` FastAPI resuelve la anotacion aqui
    from fastapi import Request
except Exception:  # noqa: BLE001
    Request = None

VERSION = "2.0.0"


def _resp(i, result=None, error=None):
    m = {"jsonrpc": "2.0", "id": i}
    if error:
        m["error"] = {"code": -32000, "message": config.redactar(str(error))}
    else:
        m["result"] = result
    return m


def autorizado(headers: dict, query: dict) -> bool:
    esperada = config.llave_mcp()
    if not esperada:
        return False  # sin llave configurada: cerrado
    h = {k.lower(): v for k, v in (headers or {}).items()}
    cand = h.get("x-api-key") or (h.get("authorization", "")[7:] if h.get("authorization", "").lower().startswith("bearer ") else "") or (query or {}).get("key", "")
    return hmac.compare_digest(str(cand).encode(), esperada.encode())


def procesar(req: dict):
    met, i = req.get("method"), req.get("id")
    if met in ("notifications/initialized", "notifications/cancelled"):
        return None
    if met == "initialize":
        return _resp(i, {"protocolVersion": (req.get("params") or {}).get("protocolVersion", "2025-03-26"),
                         "capabilities": {"tools": {}}, "serverInfo": {"name": "riu-router-github", "version": VERSION}})
    if met == "ping":
        return _resp(i, {})
    if met == "tools/list":
        return _resp(i, {"tools": [{"name": n, "description": "[%s] %s" % (perm, desc), "inputSchema": sch}
                                   for n, (_f, perm, desc, sch) in tools.TOOLS.items()]})
    if met == "tools/call":
        p = req.get("params") or {}
        t = tools.TOOLS.get(p.get("name"))
        if not t:
            return _resp(i, error="tool desconocida: %s" % p.get("name"))
        try:
            out = t[0](p.get("arguments") or {})
        except Exception as x:  # noqa: BLE001
            out = {"ok": False, "error": "EXCEPCION", "detalle": str(x)[:300]}
        out = config.redactar(out)
        return _resp(i, {"content": [{"type": "text", "text": json.dumps(out, ensure_ascii=False)}], "isError": not out.get("ok", False)})
    return _resp(i, error="metodo no soportado: %s" % met) if i is not None else None


def handle_http(cuerpo, headers: dict, query: dict):
    """Devuelve (status_http, json_o_None)."""
    if not autorizado(headers, query):
        return 401, {"jsonrpc": "2.0", "id": None, "error": {"code": -32001, "message": "no autorizado"}}
    reqs = cuerpo if isinstance(cuerpo, list) else [cuerpo]
    if not all(isinstance(r, dict) for r in reqs):
        return 400, {"jsonrpc": "2.0", "id": None, "error": {"code": -32600, "message": "peticion invalida"}}
    res = [r for r in (procesar(r) for r in reqs) if r is not None]
    if not res:
        return 202, None
    return 200, (res if isinstance(cuerpo, list) else res[0])


def build_mcp_router():
    """Reemplazo de integration/chat_mvp/mcp_route.build_mcp_router (mismo nombre, mismo /mcp)."""
    from fastapi import APIRouter
    from fastapi.responses import JSONResponse
    r = APIRouter()

    @r.post("/mcp")
    async def mcp_post(request: Request):
        try:
            cuerpo = await request.json()
        except Exception:  # noqa: BLE001
            return JSONResponse({"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "JSON invalido"}}, status_code=400)
        st, out = handle_http(cuerpo, dict(request.headers), dict(request.query_params))
        return JSONResponse(out, status_code=st)

    @r.get("/mcp")
    async def mcp_info():
        return JSONResponse({"ok": True, "servidor": "riu-router-github", "version": VERSION})

    return r
