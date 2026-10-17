"""MCP por HTTP (Streamable HTTP, JSON-RPC 2.0) para conectar cualquier IA o modelo externo al Router.

Endpoint: POST <router>/mcp (tambien por Vercel: https://riu-jev-bridge.vercel.app/mcp). GET/DELETE -> 405 (sin stream SSE: cada
peticion se contesta con application/json, lo que el transporte Streamable HTTP permite). Sin sesion (stateless).
Auth: Authorization: Bearer <token MCP> (o X-MCP-Token). Token = env RIU_MCP_TOKEN o el secreto 'mcp/token' del plugin secretos
(se genera desde la ventana Claves). Sin token valido -> 401.
Ruta respetada: las herramientas entran al HARNESS (PluginHost.call) -> puente_chat / fichas_qwen / secretos / watchdog -> FICHA -> MODELO.
La memoria usa la fachada memoria_yaiwes (SQLite de verdad); guardar solo escribe bajo el scope chat-ui:mcp*.
"""
from __future__ import annotations

import json
import re
import time
import uuid
from typing import Any, Callable

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, Response

from .host import get_host

VERSIONES = ("2025-06-18", "2025-03-26", "2024-11-05")
SERVER = {"name": "riu-router", "title": "Router Inteligente Universal", "version": "0.1.0"}
SCOPE_MCP = "chat-ui:mcp"
CHAT_TOPE_S = 110.0
_SUB_RE = re.compile(r"[^A-Za-z0-9_:-]")

_deps: dict[str, Any] = {}  # tests: host, memory, verificar


def set_deps(**kw: Any) -> None:
    _deps.clear()
    _deps.update(kw)


def _host() -> Any:
    return _deps["host"] if "host" in _deps else get_host()


def _memory() -> Any:
    if "memory" in _deps:
        return _deps["memory"]
    from ..chat_mvp.memoria_loader import _memory as m
    return m()


def _token_ok(token: str | None) -> bool:
    if "verificar" in _deps:
        return bool(_deps["verificar"](token))
    try:
        from plugins.secretos.plugin import verificar_token_mcp
        return verificar_token_mcp(token)
    except Exception:  # noqa: BLE001 - sin plugin de secretos: solo RIU_MCP_TOKEN
        import hmac
        import os
        t = os.environ.get("RIU_MCP_TOKEN") or ""
        return bool(t and token and hmac.compare_digest(t.encode(), token.encode()))


# ---- herramientas ---------------------------------------------------------------------------------------------------
def _ok(host_reply: dict) -> Any:
    if host_reply.get("status") != "ok":
        raise RuntimeError(str(host_reply.get("reason") or host_reply.get("status")))
    return host_reply.get("result")


def t_chat(a: dict) -> dict:
    modelo, mensaje = str(a.get("modelo") or "").strip(), str(a.get("mensaje") or "").strip()
    if not modelo or not mensaje:
        raise ValueError("modelo y mensaje son obligatorios (usa listar_fichas)")
    host = _host()
    cuerpo: dict[str, Any] = {"model": modelo, "messages": [{"role": "user", "content": mensaje[:20000]}],
                              "max_tokens": max(256, min(int(a.get("max_tokens") or 1200), 8192)),
                              "sesion": "mcp-" + _SUB_RE.sub("", str(a.get("sesion") or "general"))[:50],
                              "request_id": str(a.get("request_id") or uuid.uuid4().hex)[:80], "gobernanza_activa": False}
    if isinstance(a.get("qwen"), dict):  # selector Qwen igual que el chat: extras -> puente_chat -> plugin fichas_qwen
        cuerpo.update(a["qwen"])
    t0 = time.monotonic()
    r = _ok(host.call("puente_chat", "chat_async", cuerpo, timeout_s=20)) or {}
    if r.get("error"):
        raise RuntimeError(str(r["error"]))
    pid = r.get("proceso_id")
    while pid and time.monotonic() - t0 < CHAT_TOPE_S:
        r = _ok(host.call("puente_chat", "resultado", {"proceso_id": pid, "espera": 8}, timeout_s=15)) or {}
        if r.get("estado") != "procesando":
            break
        time.sleep(0.25)
    if r.get("estado") == "procesando":
        return {"texto": "", "estado": "procesando", "proceso_id": pid, "nota": "sigue en el Router; vuelve a llamar con el mismo request_id"}
    if r.get("error"):
        raise RuntimeError(str(r.get("error")) + (": " + str(r.get("detalle"))[:200] if r.get("detalle") else ""))
    texto = ((r.get("choices") or [{}])[0].get("message") or {}).get("content") or ""
    return {"texto": texto, "modelo": modelo, "ms": int((time.monotonic() - t0) * 1000), "proceso_id": pid,
            "memoria_guardada": r.get("memoria_guardada")}


def t_listar_fichas(_a: dict) -> dict:
    host = _host()
    out: dict[str, Any] = {"modelos": [], "fichas_qwen": []}
    try:
        out["modelos"] = (_ok(host.call("puente_chat", "modelos")) or {}).get("modelos") or []
    except Exception as exc:  # noqa: BLE001
        out["modelos_error"] = str(exc)[:200]
    try:
        out["fichas_qwen"] = (_ok(host.call("fichas_qwen", "fichas")) or {}).get("fichas") or []
    except Exception as exc:  # noqa: BLE001
        out["fichas_qwen_error"] = str(exc)[:200]
    return out


def _scope(a: dict) -> str:
    sub = _SUB_RE.sub("", str(a.get("scope") or ""))[:40]
    return (SCOPE_MCP + (":" + sub if sub else ""))[:80]


def _scope_lectura(a: dict) -> str:
    s = str(a.get("scope") or "").strip()
    if s.startswith("chat-ui:") and len(s) <= 80 and not re.search(r"secretos", s):  # nunca el almacen de secretos
        return s
    return _scope(a)


def t_memoria_buscar(a: dict) -> dict:
    scope = _scope_lectura(a)
    k = max(1, min(int(a.get("k") or 10), 50))
    res = _memory().search(scope, str(a.get("consulta") or ""), k)
    filas = res.get("sqlite", []) if isinstance(res, dict) else (res or [])
    return {"scope": scope, "resultados": [{"clave": f.get("key"), "datos": f.get("data")} for f in filas[:k] if isinstance(f, dict)]}


def t_memoria_guardar(a: dict) -> dict:
    clave = str(a.get("clave") or "").strip()[:200]
    if not clave:
        raise ValueError("clave obligatoria")
    datos = a.get("datos")
    if len(json.dumps(datos, ensure_ascii=False, default=str)) > 200_000:
        raise ValueError("datos demasiado grandes (max 200 KB)")
    r = _memory().save(_scope(a), clave, datos)
    return {"guardado": True, "scope": _scope(a), "clave": clave, "id": (r or {}).get("id")}


def t_secretos_listar(_a: dict) -> dict:
    return _ok(_host().call("secretos", "listar")) or {}


def t_watchdog_estado(_a: dict) -> dict:
    return _ok(_host().call("watchdog", "status")) or {}


def _obj(props: dict, req: list[str]) -> dict:
    return {"type": "object", "properties": props, "required": req, "additionalProperties": False}


TOOLS: dict[str, tuple[Callable[[dict], Any], dict]] = {
    "chat": (t_chat, {"description": "Pregunta a un modelo del Router por la ruta del chat (harness puente_chat -> ficha -> modelo). Devuelve el texto.",
                      "inputSchema": _obj({"modelo": {"type": "string", "description": "id de listar_fichas.modelos"},
                                           "mensaje": {"type": "string"}, "sesion": {"type": "string"},
                                           "max_tokens": {"type": "integer", "minimum": 256, "maximum": 8192, "description": "minimo 256 (Qwen razona)"},
                                           "request_id": {"type": "string", "description": "idempotente: repetir devuelve el mismo proceso"},
                                           "qwen": {"type": "object", "description": "extras del selector Qwen (igual que el chat)"}}, ["modelo", "mensaje"])}),
    "listar_fichas": (t_listar_fichas, {"description": "Modelos/fichas disponibles del Router (puente_chat y fichas_qwen).", "inputSchema": _obj({}, [])}),
    "memoria_buscar": (t_memoria_buscar, {"description": "Busca en la memoria del Router (SQLite memoria_yaiwes). scope: chat-ui:<algo> o subscope de chat-ui:mcp.",
                                          "inputSchema": _obj({"consulta": {"type": "string"}, "scope": {"type": "string"}, "k": {"type": "integer", "minimum": 1, "maximum": 50}}, ["consulta"])}),
    "memoria_guardar": (t_memoria_guardar, {"description": "Guarda un dato en la memoria del Router, siempre bajo chat-ui:mcp[:scope].",
                                            "inputSchema": _obj({"clave": {"type": "string"}, "datos": {}, "scope": {"type": "string"}}, ["clave", "datos"])}),
    "secretos_listar": (t_secretos_listar, {"description": "Nombres y mascaras de los secretos guardados (nunca el valor).", "inputSchema": _obj({}, [])}),
    "watchdog_estado": (t_watchdog_estado, {"description": "Estado del watchdog del Router (caidos, ultima ronda).", "inputSchema": _obj({}, [])}),
}


# ---- JSON-RPC ---------------------------------------------------------------------------------------------------------
def _err(mid: Any, code: int, msg: str) -> dict:
    return {"jsonrpc": "2.0", "id": mid, "error": {"code": code, "message": msg}}


def responder(msg: Any) -> dict | None:
    """Una peticion JSON-RPC -> respuesta (None para notificaciones y respuestas del cliente)."""
    if not isinstance(msg, dict) or msg.get("jsonrpc") != "2.0":
        return _err(None, -32600, "Invalid Request")
    if "method" not in msg:
        return None  # respuesta del cliente a algo nuestro: no pedimos nada, se ignora
    mid, method, params = msg.get("id"), msg.get("method"), msg.get("params") or {}
    if "id" not in msg:
        return None  # notificacion (notifications/initialized, cancelled, ...)
    if method == "initialize":
        pedida = str(params.get("protocolVersion") or "")
        return {"jsonrpc": "2.0", "id": mid, "result": {"protocolVersion": pedida if pedida in VERSIONES else VERSIONES[0],
                                                        "capabilities": {"tools": {"listChanged": False}}, "serverInfo": SERVER,
                                                        "instructions": "Router RIU: usa listar_fichas para ver modelos y chat para preguntar."}}
    if method == "ping":
        return {"jsonrpc": "2.0", "id": mid, "result": {}}
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": mid, "result": {"tools": [{"name": n, **meta} for n, (_f, meta) in TOOLS.items()]}}
    if method == "tools/call":
        name, args = params.get("name"), params.get("arguments") or {}
        if name not in TOOLS:
            return _err(mid, -32602, "Herramienta desconocida: %s" % name)
        if not isinstance(args, dict):
            return _err(mid, -32602, "arguments debe ser un objeto")
        try:
            out = TOOLS[name][0](args)
            texto = out.get("texto") if isinstance(out, dict) and isinstance(out.get("texto"), str) and out.get("texto") else json.dumps(out, ensure_ascii=False, default=str)
            return {"jsonrpc": "2.0", "id": mid, "result": {"content": [{"type": "text", "text": texto}], "structuredContent": out if isinstance(out, dict) else {"valor": out}, "isError": False}}
        except Exception as exc:  # noqa: BLE001 - error de herramienta = resultado con isError (spec MCP), nunca 500
            return {"jsonrpc": "2.0", "id": mid, "result": {"content": [{"type": "text", "text": "Error: %s" % str(exc)[:300]}], "isError": True}}
    if method in ("resources/list", "prompts/list"):
        return {"jsonrpc": "2.0", "id": mid, "result": {method.split("/")[0]: []}}
    return _err(mid, -32601, "Method not found: %s" % method)


def build_mcp_router() -> APIRouter:
    r = APIRouter()

    def _auth_ok(request: Request) -> bool:
        a = request.headers.get("authorization") or ""
        tok = a[7:].strip() if a.lower().startswith("bearer ") else (request.headers.get("x-mcp-token") or "").strip()
        return _token_ok(tok or None)

    @r.post("/mcp")
    async def mcp_post(request: Request) -> Response:
        if not _auth_ok(request):
            return JSONResponse({"error": "token MCP invalido o ausente"}, status_code=401, headers={"WWW-Authenticate": 'Bearer realm="riu-mcp"'})
        try:
            body = json.loads(await request.body() or b"null")
        except ValueError:
            return JSONResponse(_err(None, -32700, "Parse error"), status_code=400)
        from starlette.concurrency import run_in_threadpool  # las herramientas bloquean (chat hasta 110 s): fuera del event loop
        if isinstance(body, list):
            if not body:
                return JSONResponse(_err(None, -32600, "Invalid Request"), status_code=400)
            outs = [o for o in [await run_in_threadpool(responder, m) for m in body] if o is not None]
            return JSONResponse(outs) if outs else Response(status_code=202)
        out = await run_in_threadpool(responder, body)
        return JSONResponse(out) if out is not None else Response(status_code=202)

    @r.get("/mcp")
    def mcp_get() -> Response:
        return Response(status_code=405, headers={"Allow": "POST"})

    @r.delete("/mcp")
    def mcp_delete() -> Response:
        return Response(status_code=405, headers={"Allow": "POST"})

    return r
