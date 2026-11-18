"""MCP HTTP como APIRouter de FastAPI · /mcp · JSON-RPC 2.0 · yaiwes.node/v2

Fichero: backend/mcp_router.py
POR QUE ESTE FICHERO EXISTE (refutacion 1, corregida):
  El servidor anterior (backend/deploy/mcp_server.py) era un http.server de la
  stdlib en el puerto 8078, aparte del FastAPI de la API. En produccion eso son
  DOS procesos: HF Spaces arranca UNO, el CORS no se comparte y el ciclo de vida
  se duplica. Aqui el MCP vive dentro de la misma app FastAPI: un solo techo,
  una sola configuracion de CORS, un solo arranque.

LO QUE NO SE PIERDE (esta es la parte que la propuesta de refactor rompia):
  · las 7 tools SIGUEN ejecutando la logica real, no un stub {"status":"OK"}
  · allowlist POR VENTANA (w1/w2/w3) y rechazo -32601 fuera de allowlist
  · rechazo de credenciales en el payload (-32002)
  · limite de payload (413), validacion de origen (403), sesiones con id
  · los errores SIEMPRE en forma JSON-RPC valida (nunca {"detail": ...})

MEJORA REAL: las tools ya no hacen HTTP contra si mismas (el viejo
_render_diagram hacia POST a /render/diagram con un payload que NO cumplia el
contrato -> HTTP 422 y por tanto NUNCA renderizo nada). Ahora se llaman en
proceso al motor real y devuelven su resultado real (ok:false con causa si el
motor no esta instalado).

Rutas que expone este router (se montan sin prefijo en api.py):
  POST   /mcp             JSON-RPC 2.0 (initialize / tools/list / tools/call / ping)
  GET    /mcp/health      estado real del servidor MCP y de sus allowlists
  DELETE /mcp             cierra la sesion (Mcp-Session-Id)
  POST   /guide/match     motor de la guia vivo (match_action + parche quirurgico)
  GET    /guide/status    estado real de los modulos de la guia
"""

from __future__ import annotations

import json
import os
import sys
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

# --- importacion de hermanos (1 funcion = 1 fichero) ------------------------
BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import audio_engine  # noqa: E402
import canvas_engine  # noqa: E402

XRAY_DIR = BACKEND_DIR / "xray"
if str(XRAY_DIR) not in sys.path:
    sys.path.insert(0, str(XRAY_DIR))
import audit_runner  # noqa: E402

# El motor de deploy vive en backend/deploy/ (modulo propio, 1 funcion = 1 fichero).
DEPLOY_DIR = BACKEND_DIR / "deploy"
if str(DEPLOY_DIR) not in sys.path:
    sys.path.insert(0, str(DEPLOY_DIR))
import deploy_engine  # noqa: E402

CANVAS_ROOT = BACKEND_DIR.parent
FRONTEND_ROOT = CANVAS_ROOT / "frontend"
GUIDE_DIR = BACKEND_DIR / "guide"
if str(GUIDE_DIR) not in sys.path:
    sys.path.insert(0, str(GUIDE_DIR))

router = APIRouter()

PROTOCOL_VERSION = "2025-06-18"
SERVER_NAME = "yaiwes-canvas-mcp"
SERVER_VERSION = "1.1.0"

MAX_PAYLOAD_BYTES = int(os.environ.get("MCP_MAX_PAYLOAD_BYTES", 262144))
MAX_SESSIONS = int(os.environ.get("MCP_MAX_SESSIONS", 256))
DEFAULT_ALLOWED_ORIGINS = ",".join([
    "http://localhost:7860", "http://127.0.0.1:7860",
    "http://localhost:8089", "http://127.0.0.1:8089",
    "http://localhost:8078", "http://127.0.0.1:8078",
])

# --------------------------------------------------------------------------- #
# Allowlist POR VENTANA (distinta por ventana: es el aislamiento del sandbox)
# --------------------------------------------------------------------------- #
WINDOW_ALLOWLIST = {
    "w1": ["memory_profile", "memory_index"],
    "w2": ["render_diagram", "render_motion", "audio_explain"],
    "w3": ["xray_audit", "deploy_plan"],
}

WINDOW_NAMES = {
    "w1": "Ventana 1 · MIRROR",
    "w2": "Ventana 2 · DIFF + EDITOR QUIRURGICO",
    "w3": "Ventana 3 · DEPLOY",
}

TOOL_CATALOG = {
    "memory_profile": {
        "description": "Estado real del proyecto (ficheros presentes en el canvas). Resultado minimo.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    "memory_index": {
        "description": "Buscar en la documentacion del canvas. Devuelve rutas y lineas, no el corpus.",
        "inputSchema": {
            "type": "object",
            "properties": {"query": {"type": "string"}, "limit": {"type": "integer"}},
            "required": ["query"],
        },
    },
    "render_diagram": {
        "description": "Renderiza un diagrama con el motor real (excalidraw|mermaid|d2). Delega en el canvas_engine.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "tool": {"type": "string", "enum": ["excalidraw", "mermaid", "d2"]},
                "payload": {"type": "object"},
                "code": {"type": "string"},
            },
            "required": ["tool"],
        },
    },
    "render_motion": {
        "description": "Renderiza una motion con el motor real (hyperframes|remotion|rive). Delega en el canvas_engine.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "tool": {"type": "string", "enum": ["hyperframes", "remotion", "rive"]},
                "payload": {"type": "object"},
            },
            "required": ["tool"],
        },
    },
    "audio_explain": {
        "description": "Resumen + voz explicativa (MP3 real). Delega en el motor de audio del canvas.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {"type": "string"},
                "diagram": {"type": "object"},
                "lang": {"type": "string"},
                "voice": {"type": "string"},
            },
        },
    },
    "xray_audit": {
        "description": "Auditoria X-Ray determinista del MISMO codigo. Delega en el auditor real del canvas.",
        "inputSchema": {
            "type": "object",
            "properties": {"root": {"type": "string"}, "out": {"type": "string"}},
        },
    },
    "deploy_plan": {
        "description": "Plan de despliegue (dry-run) y checks fail-closed del motor de deploy.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "files": {"type": "array"},
                "root": {"type": "string"},
                "repo": {"type": "string"},
                "branch": {"type": "string"},
                "expected_head": {"type": "string"},
                "current_head": {"type": "string"},
                "mode": {"type": "string", "enum": ["plan", "execute"]},
                "authorize": {"type": "boolean"},
                "dry_run": {"type": "boolean"},
            },
            "required": ["files"],
        },
    },
}

# --------------------------------------------------------------------------- #
# Sesiones (con tope: no crece sin limite en un Space efimero)
# --------------------------------------------------------------------------- #
_SESSIONS: Dict[str, dict] = {}


def _new_session() -> str:
    sid = "sess-%d-%s" % (int(time.time() * 1000), uuid.uuid4().hex[:6])
    if len(_SESSIONS) >= MAX_SESSIONS:
        for old in sorted(_SESSIONS, key=lambda k: _SESSIONS[k].get("created_at", 0))[: len(_SESSIONS) - MAX_SESSIONS + 1]:
            _SESSIONS.pop(old, None)
    _SESSIONS[sid] = {"created_at": time.time(), "window": None, "initialized": False}
    return sid


def _session_ok(sid: str, window: str) -> bool:
    if not sid:
        return True  # modo sin estado: el handshake sigue siendo valido
    sess = _SESSIONS.get(sid)
    if not sess:
        return False
    if window and sess.get("window") and sess["window"] != window:
        return False
    return True


def _close_session(sid: str) -> bool:
    return _SESSIONS.pop(sid, None) is not None


# --------------------------------------------------------------------------- #
# Seguridad: origen, credenciales, payload
# --------------------------------------------------------------------------- #
def _allowed_origins() -> List[str]:
    raw = os.environ.get("MCP_ALLOWED_ORIGINS", DEFAULT_ALLOWED_ORIGINS)
    return [o.strip() for o in raw.split(",") if o.strip()]


def _origin_ok(origin: Optional[str]) -> Tuple[bool, str]:
    if not origin:
        return True, "sin cabecera Origin (cliente no navegador)"
    if origin in _allowed_origins():
        return True, "origin permitido: " + origin
    return False, "origin no permitido: " + origin


def _payload_has_credentials(payload: Any) -> List[str]:
    """Claves prohibidas + valores literales de cualquier token del entorno."""
    hits = deploy_engine._scan_payload_keys(payload)
    if hits:
        return hits
    try:
        blob = json.dumps(payload, ensure_ascii=False)
    except (TypeError, ValueError):
        return []
    for name in deploy_engine.TOKEN_ENV_VARS:
        val = os.environ.get(name)
        if val and len(val) >= 8 and val in blob:
            return ["<valor del token de %s>" % name]
    return []


def _jsonrpc_error(code: int, message: str, data: Any = None, rpc_id: Any = None) -> Dict[str, Any]:
    err: Dict[str, Any] = {"code": code, "message": message}
    if data is not None:
        err["data"] = data
    return {"jsonrpc": "2.0", "id": rpc_id, "error": err}


def _text_result(payload: Any, is_error: bool = False) -> Dict[str, Any]:
    return {
        "content": [{"type": "text", "text": json.dumps(payload, ensure_ascii=False, indent=2)}],
        "structuredContent": payload,
        "isError": bool(is_error),
    }


# --------------------------------------------------------------------------- #
# Implementacion REAL de cada tool (sin mocks: OMITIDO con causa exacta)
# --------------------------------------------------------------------------- #
def _scan_files(root: Path, exts: set) -> List[str]:
    out: List[str] = []
    if not root.is_dir():
        return out
    for base, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in ("__pycache__", ".git", "node_modules")]
        for name in sorted(files):
            if os.path.splitext(name)[1] in exts:
                out.append(os.path.relpath(os.path.join(base, name), CANVAS_ROOT))
    return out


async def _tool_memory_profile(args: Dict[str, Any], window: str) -> Dict[str, Any]:
    py = _scan_files(BACKEND_DIR, {".py"})
    front = _scan_files(FRONTEND_ROOT, {".html", ".js", ".css"})
    return {
        "status": "OK",
        "window": window,
        "state": {
            "canvas_root": str(CANVAS_ROOT),
            "backend_python_modules": sorted(py),
            "frontend_files": sorted(front),
            "backend_module_count": len(py),
            "frontend_file_count": len(front),
        },
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


async def _tool_memory_index(args: Dict[str, Any], window: str) -> Dict[str, Any]:
    query = str(args.get("query") or "").strip()
    limit = int(args.get("limit") or 20)
    if not query:
        return {"status": "ERROR", "reason": "falta 'query'"}
    needles = [q.lower() for q in query.split() if q.strip()]
    hits: List[Dict[str, Any]] = []
    exts = {".md", ".json", ".txt", ".py", ".js", ".html"}
    for base, dirs, files in os.walk(CANVAS_ROOT):
        dirs[:] = [d for d in dirs if d not in ("__pycache__", ".git", "node_modules")]
        for name in sorted(files):
            if os.path.splitext(name)[1] not in exts:
                continue
            path = os.path.join(base, name)
            try:
                with open(path, "r", encoding="utf-8", errors="replace") as fh:
                    for num, line in enumerate(fh, 1):
                        low = line.lower()
                        if any(n in low for n in needles):
                            hits.append({
                                "path": os.path.relpath(path, CANVAS_ROOT),
                                "line": num,
                                "snippet": line.strip()[:160],
                            })
                            break
            except OSError:
                continue
            if len(hits) >= limit:
                break
        if len(hits) >= limit:
            break
    return {"status": "OK", "query": query, "hits": hits[:limit], "hit_count": len(hits[:limit])}


def _render_payload(args: Dict[str, Any]) -> Any:
    """Normaliza el payload de render: {payload} | {code} | {spec}."""
    if args.get("payload") is not None:
        return args.get("payload")
    if args.get("code") is not None:
        return {"code": args.get("code")}
    if args.get("spec") is not None:
        return {"code": args.get("spec")}
    return {}


async def _tool_render_diagram(args: Dict[str, Any], window: str) -> Dict[str, Any]:
    tool = str(args.get("tool") or "").strip().lower()
    if not tool:
        return {"status": "ERROR", "reason": "falta 'tool' (excalidraw|mermaid|d2)"}
    try:
        result = canvas_engine.render_diagram(tool, _render_payload(args))
    except ValueError as exc:
        return {"status": "ERROR", "reason": str(exc)}
    ok = bool(result.get("ok"))
    return {
        "status": "OK" if ok else "OMITIDO",
        "window": window,
        "tool": tool,
        "result": result,
        "reason": None if ok else (result.get("error") or result.get("reason")),
        "ping_command": result.get("ping_command"),
    }


async def _tool_render_motion(args: Dict[str, Any], window: str) -> Dict[str, Any]:
    tool = str(args.get("tool") or "").strip().lower()
    if not tool:
        return {"status": "ERROR", "reason": "falta 'tool' (hyperframes|remotion|rive)"}
    try:
        result = canvas_engine.render_motion(tool, _render_payload(args))
    except ValueError as exc:
        return {"status": "ERROR", "reason": str(exc)}
    ok = bool(result.get("ok"))
    return {
        "status": "OK" if ok else "OMITIDO",
        "window": window,
        "tool": tool,
        "result": result,
        "reason": None if ok else (result.get("error") or result.get("reason")),
        "ping_command": result.get("ping_command"),
    }


async def _tool_audio_explain(args: Dict[str, Any], window: str) -> Dict[str, Any]:
    diagram = args.get("diagram")
    if diagram is None and args.get("text"):
        diagram = {"summary": args.get("text")}
    if diagram is None:
        return {"status": "ERROR", "reason": "falta 'text' o 'diagram'"}
    lang = args.get("lang") or args.get("target_lang")
    voice = args.get("voice") or "es-ES-AlvaroNeural"
    result = await audio_engine.explain(diagram, target_lang=lang, voice=voice)
    ok = bool(result.get("ok"))
    return {
        "status": "OK" if ok else "ERROR",
        "window": window,
        "result": result,
        "reason": result.get("error"),
    }


async def _tool_xray_audit(args: Dict[str, Any], window: str) -> Dict[str, Any]:
    root = str(args.get("root") or CANVAS_ROOT)
    out = str(args.get("out") or (XRAY_DIR))
    result = audit_runner.run_audit(root, out)
    ok = bool(result.get("ok"))
    validation = result.get("validation") or {}
    return {
        "status": "OK" if ok else "ERROR",
        "window": window,
        "root": root,
        "out": out,
        "exit_code": result.get("exit_code"),
        "validation": validation,
        "fingerprint": result.get("fingerprint"),
        "reason": None if ok else (result.get("stderr_tail") or "el auditor termino con error"),
    }


async def _tool_deploy_plan(args: Dict[str, Any], window: str) -> Dict[str, Any]:
    files = args.get("files") or []
    root = str(args.get("root") or str(CANVAS_ROOT / "deploy_target"))
    mode = str(args.get("mode") or "plan").lower()
    try:
        if mode == "execute":
            env_token = None
            for name in deploy_engine.TOKEN_ENV_VARS:
                if os.environ.get(name):
                    env_token = os.environ[name]
                    break
            result = deploy_engine.execute(
                files=files, root=root, repo=args.get("repo"), branch=args.get("branch"),
                expected_head=args.get("expected_head"), current_head=args.get("current_head"),
                authorization_token=env_token,
                dry_run=bool(args.get("dry_run", True)),
                workdir=os.environ.get("DEPLOY_WORKDIR", str(CANVAS_ROOT)),
                env=os.environ,
            )
            return {"status": result.get("status"), "result": result}
        result = deploy_engine.plan(
            files=files, root=root, repo=args.get("repo"), branch=args.get("branch"),
            expected_head=args.get("expected_head"), current_head=args.get("current_head"),
        )
        return {"status": "PLAN", "result": result}
    except deploy_engine.DeployAbort as exc:
        return {"status": "ABORT", "code": exc.code, "message": exc.message, "detail": exc.detail}


TOOL_IMPL = {
    "memory_profile": _tool_memory_profile,
    "memory_index": _tool_memory_index,
    "render_diagram": _tool_render_diagram,
    "render_motion": _tool_render_motion,
    "audio_explain": _tool_audio_explain,
    "xray_audit": _tool_xray_audit,
    "deploy_plan": _tool_deploy_plan,
}


# --------------------------------------------------------------------------- #
# Nucleo JSON-RPC (puro: sin FastAPI, testeable por separado)
# --------------------------------------------------------------------------- #
def _resolve_window(params: Dict[str, Any], meta: Dict[str, Any]) -> str:
    win = meta.get("window") or (params or {}).get("window")
    win = str(win or "").strip().lower()
    if win in ("ventana1", "ventana 1", "1", "mirror"):
        win = "w1"
    elif win in ("ventana2", "ventana 2", "2", "diff", "diff_editor"):
        win = "w2"
    elif win in ("ventana3", "ventana 3", "3", "deploy"):
        win = "w3"
    return win if win in WINDOW_ALLOWLIST else ""


async def handle_rpc(payload: Any, meta: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
    """payload: dict JSON-RPC. meta: {window, session_id}. Devuelve (http_status, body)."""
    if not isinstance(payload, dict):
        return 400, _jsonrpc_error(-32600, "Invalid Request: el payload debe ser un objeto JSON-RPC.")

    method = payload.get("method")
    rpc_id = payload.get("id")
    params = payload.get("params") or {}

    if method == "initialize":
        win = _resolve_window(params, meta)
        sid = _new_session()
        _SESSIONS[sid]["window"] = win or None
        _SESSIONS[sid]["initialized"] = True
        return 200, {
            "jsonrpc": "2.0",
            "id": rpc_id,
            "result": {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
                "sessionId": sid,
                "window": win or None,
                "windowName": WINDOW_NAMES.get(win),
                "allowedTools": WINDOW_ALLOWLIST.get(win, []),
            },
        }

    if method in ("notifications/initialized", "initialized", "notifications/cancelled"):
        return 202, {}

    win = _resolve_window(params, meta)
    if not win:
        return 200, _jsonrpc_error(
            -32602, "VENTANA NO IDENTIFICADA: envia X-MCP-Window: w1|w2|w3.",
            {"expected": sorted(WINDOW_ALLOWLIST.keys())}, rpc_id)

    allowed = WINDOW_ALLOWLIST[win]

    if method == "tools/list":
        tools = []
        for name in allowed:
            spec = TOOL_CATALOG[name]
            tools.append({"name": name, "description": spec["description"],
                          "inputSchema": spec["inputSchema"]})
        return 200, {"jsonrpc": "2.0", "id": rpc_id,
                     "result": {"tools": tools, "window": win, "windowName": WINDOW_NAMES[win]}}

    if method == "tools/call":
        name = params.get("name")
        args = params.get("arguments") or {}
        if name not in allowed:
            return 200, _jsonrpc_error(
                -32601, "TOOL NO PERMITIDA EN ESTA VENTANA: %s" % name,
                {"tool": name, "window": win, "allowed": allowed}, rpc_id)
        creds = _payload_has_credentials(args)
        if creds:
            return 200, _jsonrpc_error(
                -32002, "CREDENCIALES EN PAYLOAD RECHAZADAS", {"fields": creds}, rpc_id)
        try:
            payload_out = await TOOL_IMPL[name](args, win)
        except deploy_engine.DeployAbort as exc:
            payload_out = {"status": "ABORT", "code": exc.code, "message": exc.message}
        except Exception as exc:  # noqa: BLE001
            payload_out = {"status": "ERROR", "reason": "%s: %s" % (type(exc).__name__, exc)}
        is_error = str(payload_out.get("status")) in ("ERROR", "ABORT")
        return 200, {"jsonrpc": "2.0", "id": rpc_id,
                     "result": _text_result(payload_out, is_error)}

    if method == "ping":
        return 200, {"jsonrpc": "2.0", "id": rpc_id, "result": {}}

    return 200, _jsonrpc_error(-32601, "Method not found: %s" % method, rpc_id=rpc_id)


# --------------------------------------------------------------------------- #
# Rutas HTTP
# --------------------------------------------------------------------------- #
def _meta(request: Request) -> Dict[str, str]:
    return {
        "window": (request.headers.get("X-MCP-Window") or "").strip(),
        "session_id": (request.headers.get("Mcp-Session-Id")
                       or request.headers.get("mcp-session-id") or "").strip(),
    }


@router.post("/mcp")
async def mcp_endpoint(request: Request) -> JSONResponse:
    """Punto de entrada MCP (Streamable HTTP). Todo error sale en forma JSON-RPC."""
    ok, reason = _origin_ok(request.headers.get("Origin"))
    if not ok:
        return JSONResponse(status_code=403,
                            content=_jsonrpc_error(-32001, "ORIGEN NO VALIDADO: %s" % reason,
                                                  {"allowed": _allowed_origins()}))

    body = await request.body()
    if len(body) > MAX_PAYLOAD_BYTES:
        return JSONResponse(status_code=413,
                            content=_jsonrpc_error(-32000,
                                                  "PAYLOAD DEMASIADO GRANDE: maximo %d bytes" % MAX_PAYLOAD_BYTES,
                                                  {"max": MAX_PAYLOAD_BYTES, "received": len(body)}))
    try:
        payload = json.loads(body.decode("utf-8")) if body else {}
    except (ValueError, UnicodeDecodeError) as exc:
        return JSONResponse(status_code=400,
                            content=_jsonrpc_error(-32700, "Parse error: %s" % exc))

    meta = _meta(request)
    if not _session_ok(meta["session_id"], meta["window"]):
        return JSONResponse(status_code=200,
                            content=_jsonrpc_error(-32001, "SESION INVALIDA: inicializa de nuevo.",
                                                  {"sessionId": meta["session_id"]}))

    creds = _payload_has_credentials(payload)
    if creds:
        return JSONResponse(status_code=200,
                            content=_jsonrpc_error(-32002, "CREDENCIALES EN PAYLOAD RECHAZADAS",
                                                  {"fields": creds}))

    status, out = await handle_rpc(payload, meta)
    headers = {}
    if isinstance(out, dict) and isinstance(out.get("result"), dict) and out["result"].get("sessionId"):
        headers["Mcp-Session-Id"] = out["result"]["sessionId"]
    return JSONResponse(status_code=status, content=out, headers=headers)


@router.delete("/mcp")
async def mcp_delete(request: Request) -> JSONResponse:
    """Cierra la sesion indicada por Mcp-Session-Id."""
    meta = _meta(request)
    closed = _close_session(meta["session_id"])
    return JSONResponse(status_code=200,
                        content={"status": "session_closed" if closed else "session_unknown",
                                 "sessionId": meta["session_id"]})


@router.get("/mcp/health")
async def mcp_health() -> Dict[str, Any]:
    """Estado real del servidor MCP (sin mocks)."""
    return {
        "status": "OK",
        "server": SERVER_NAME,
        "version": SERVER_VERSION,
        "protocol": PROTOCOL_VERSION,
        "windows": {k: list(v) for k, v in WINDOW_ALLOWLIST.items()},
        "window_names": dict(WINDOW_NAMES),
        "canvas_root": str(CANVAS_ROOT),
        "allowed_origins": _allowed_origins(),
        "max_payload_bytes": MAX_PAYLOAD_BYTES,
        "active_sessions": len(_SESSIONS),
        "mounted_in": "backend/api.py (FastAPI) - un solo proceso",
    }


# --------------------------------------------------------------------------- #
# Motor de la guia viva (proxy SERVER-SIDE real: antes era un proxy HTTP que
# apuntaba a rutas que no existian -> 404 y motor "no disponible")
# --------------------------------------------------------------------------- #
def _guide_modules_present() -> List[str]:
    if not GUIDE_DIR.is_dir():
        return []
    return sorted(n for n in os.listdir(GUIDE_DIR) if n.endswith(".py"))


@router.get("/guide/status")
async def guide_status() -> Dict[str, Any]:
    """Estado real de los modulos del motor de la guia."""
    return {
        "status": "OK",
        "guide_dir": str(GUIDE_DIR),
        "guide_modules_present": _guide_modules_present(),
        "note": "los modulos de la guia se consultan por HTTP desde este mismo proceso",
    }


@router.post("/guide/match")
async def guide_match(request: Request) -> JSONResponse:
    """Consulta real al motor de la guia: decomposicion + match + parche quirurgico."""
    ok, reason = _origin_ok(request.headers.get("Origin"))
    if not ok:
        return JSONResponse(status_code=403,
                            content={"status": "ERROR", "reason": "ORIGEN NO VALIDADO: %s" % reason})
    body = await request.body()
    if len(body) > MAX_PAYLOAD_BYTES:
        return JSONResponse(status_code=413,
                            content={"status": "ERROR",
                                     "reason": "PAYLOAD DEMASIADO GRANDE (max %d B)" % MAX_PAYLOAD_BYTES})
    try:
        payload = json.loads(body.decode("utf-8")) if body else {}
    except (ValueError, UnicodeDecodeError) as exc:
        return JSONResponse(status_code=400,
                            content={"status": "ERROR", "reason": "Parse error: %s" % exc})

    creds = _payload_has_credentials(payload)
    if creds:
        return JSONResponse(status_code=400,
                            content={"status": "ERROR",
                                     "reason": "CREDENCIALES EN PAYLOAD RECHAZADAS",
                                     "fields": creds})

    query = str(payload.get("query") or "").strip()
    code = payload.get("code") or ""
    if not query:
        return JSONResponse(status_code=400,
                            content={"status": "ERROR", "reason": "falta 'query'"})
    try:
        import match as guide_match_mod  # modulo real del motor de la guia
        import grammar as guide_grammar
    except Exception as exc:  # noqa: BLE001
        return JSONResponse(status_code=503,
                            content={"status": "MOTOR DE GUIA NO DISPONIBLE",
                                     "reason": "%s: %s" % (type(exc).__name__, exc),
                                     "guide_modules_present": _guide_modules_present()})
    try:
        decomposition = guide_grammar.decompose(query)
        result = guide_match_mod.match_action(query, code, fichero=payload.get("base"))
        return JSONResponse(status_code=200, content={
            "status": "OK",
            "query": query,
            "decomposition": decomposition,
            "match": result,
            "guide_modules_present": _guide_modules_present(),
        })
    except Exception as exc:  # noqa: BLE001
        return JSONResponse(status_code=502,
                            content={"status": "ERROR",
                                     "reason": "%s: %s" % (type(exc).__name__, exc)})
