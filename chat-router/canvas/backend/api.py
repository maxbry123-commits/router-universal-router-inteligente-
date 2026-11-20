"""API REST + WebSocket + MCP del Canvas (N4-A + N4-D2).

Fichero: api.py
Rutas:
  GET  /health            -> estado real de los 6 adapters (health.health_payload)
  POST /render/diagram    -> {"tool","payload"}
  POST /render/motion     -> {"tool","payload"}
  POST /convert           -> {"src","dst","payload"}
  POST /audio/explain     -> {"diagram":dict,"target_lang":Optional[str],"voice":str}
  GET  /audio/{audio_id}  -> FileResponse (media_type="audio/mpeg")
  POST /gaps              -> crea un gap (la evidencia se valida contra INVENTORY.json)
  GET  /gaps              -> gaps + contador por estado/tipo/severidad
  GET  /xray/{artifact}   -> artefactos del auditor (allowlist, .md en texto plano)
  POST /xray/audit        -> re-audita una raiz (xray/audit_runner.py)
  WS   /ws/progress       -> cada 5 s envia el estado real de health_all()
  POST /mcp               -> MCP JSON-RPC 2.0 (backend/mcp_router.py)
  GET  /mcp/health        -> estado real del MCP y sus allowlists
  POST /guide/match       -> motor de la guia vivo (match + parche quirurgico)
  GET  /ui/               -> frontend estatico (las 3 ventanas + el index)

UN SOLO PROCESO: la API, el MCP y el frontend viven en esta misma app FastAPI.
Mapeo de errores: ValueError -> 400, cualquier otra excepcion -> 502.
FAIL_CLOSED: el cliente recibe SIEMPRE JSON con el motivo real del fallo.

BUG REAL CORREGIDO (INPUT BLOCK): `get_audio` usa `Path` y faltaba
`from pathlib import Path` en el bloque de referencia.

Este modulo SOLO enruta: la logica vive en canvas_engine.py, health.py,
audio_engine.py, mcp_router.py y xray/audit_runner.py (1 funcion = 1 fichero).
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional

# --- importacion de hermanos (canvas_engine, health, audio_engine) ----------
BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from fastapi.responses import FileResponse, PlainTextResponse  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402
from pydantic import BaseModel, Field  # noqa: E402

import audio_engine  # noqa: E402
import canvas_engine as engine  # noqa: E402
import health as health_module  # noqa: E402

# --- integracion del NODO B (X-Ray + gaps): api.py SOLO enruta ---------------
XRAY_DIR = Path(__file__).resolve().parent / "xray"
if str(XRAY_DIR) not in sys.path:
    sys.path.insert(0, str(XRAY_DIR))
import audit_runner  # noqa: E402
import gaps_store  # noqa: E402

# --- MCP: APIRouter de FastAPI montado en ESTA app (un solo proceso) --------
# Antes era un http.server aparte (backend/deploy/mcp_server.py, puerto 8078):
# dos procesos, dos CORS, dos ciclos de vida. Ahora vive bajo el mismo techo.
from mcp_router import router as mcp_router  # noqa: E402

# Directorio con los artefactos del auditor (INVENTORY.json, FINGERPRINT.json...).
# Se puede mover con la variable de entorno XRAY_OUT_DIR. Allowlist de nombres:
# solo se sirve lo que el auditor genera; nunca rutas arbitrarias.
XRAY_OUT_DIR = Path(os.environ.get("XRAY_OUT_DIR", str(XRAY_DIR)))
XRAY_ARTIFACTS = (
    "INVENTORY.json",
    "FINGERPRINT.json",
    "CONTRACTS.md",
    "GAPS.md",
    "NEXT_ACTIONS.md",
    "XRAY_REPORT.md",
    "MANIFEST.md",
    "ARCHITECTURE.md",
    "gaps.json",
    "STATE.json",
)

app = FastAPI(
    title="Canvas Backend",
    version="1.0.0",
    description="Adapters de diagrama/motion + motor de audio explicativo (N4-A) + VENTANA GAPS/X-Ray (N4-B, integrado por el supervisor).",
)

WS_PROGRESS_INTERVAL = 5  # segundos entre envios de /ws/progress

# --- CORS: el frontend puede servirse en otro origen (p.ej. estatico en :8088
# y API en :8077). Orígenes configurables con CANVAS_ALLOWED_ORIGINS (CSV).
# En produccion, si el frontend lo sirve esta misma app, no hace falta.
ALLOWED_ORIGINS = [o.strip() for o in os.environ.get("CANVAS_ALLOWED_ORIGINS", "*").split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# El MCP se monta SIN prefijo extra: sus rutas ya son /mcp, /mcp/health,
# /guide/match y /guide/status. (Montarlo con prefix="/mcp" sobre rutas que
# empiezan por "/mcp" produciria /mcp/mcp: el error clasico del doble prefijo.)
app.include_router(mcp_router)


# --------------------------------------------------------------------------
# Modelos de entrada (pydantic v2)
# --------------------------------------------------------------------------
class RenderRequest(BaseModel):
    tool: str = Field(..., description="excalidraw|mermaid|d2 (diagrama) o hyperframes|remotion|rive (motion)")
    payload: Any = Field(default=None, description="Payload especifico de la herramienta")


class ConvertRequest(BaseModel):
    src: str = Field(..., description="herramienta origen")
    dst: str = Field(..., description="herramienta destino")
    payload: Any = Field(default=None)


class AudioExplainRequest(BaseModel):
    diagram: Dict[str, Any] = Field(default_factory=dict, description="Diagrama JSON (o {'summary': '...'})")
    target_lang: Optional[str] = Field(default=None, description="idioma destino; None o 'es' = sin traduccion")
    voice: str = Field(default="es-ES-AlvaroNeural", description="voz de edge-tts")


class GapRequest(BaseModel):
    """Gap de la VENTANA GAPS. La evidencia se valida contra INVENTORY.json."""

    tipo: str = Field(..., description="GAP|ERROR|DRIFT|BROKEN_CANDIDATE|HUÉRFANO")
    severidad: str = Field(..., description="P0|P1|P2|P3")
    titulo: str = Field(..., description="descripcion corta")
    evidencia: str = Field(..., description="ruta:línea (+ sha256:...)")
    componente: str = Field(default="", description="componente afectado")
    notas: str = Field(default="", description="texto libre, máx 500 chars")


class XrayAuditRequest(BaseModel):
    root: str = Field(default="", description="raíz a auditar; vacío = directorio de trabajo")
    out: str = Field(default="", description="directorio de salida; vacío = XRAY_OUT_DIR")


# --------------------------------------------------------------------------
# Helpers de error (FAIL_CLOSED)
# --------------------------------------------------------------------------
def _fail(exc: Exception) -> HTTPException:
    """ValueError -> 400; cualquier otra excepcion -> 502."""
    if isinstance(exc, ValueError):
        return HTTPException(status_code=400, detail=str(exc))
    return HTTPException(status_code=502, detail=f"{type(exc).__name__}: {exc}")


# --------------------------------------------------------------------------
# Rutas REST
# --------------------------------------------------------------------------
@app.get("/health")
async def get_health() -> Dict[str, Any]:
    """Estado real de los 6 adapters."""
    try:
        return health_module.health_payload()
    except Exception as exc:
        raise _fail(exc)


@app.post("/render/diagram")
async def post_render_diagram(request: RenderRequest) -> Dict[str, Any]:
    """Renderiza un diagrama (excalidraw|mermaid|d2)."""
    try:
        return engine.render_diagram(request.tool, request.payload)
    except Exception as exc:
        raise _fail(exc)


@app.post("/render/motion")
async def post_render_motion(request: RenderRequest) -> Dict[str, Any]:
    """Renderiza una animacion (hyperframes|remotion|rive)."""
    try:
        return engine.render_motion(request.tool, request.payload)
    except Exception as exc:
        raise _fail(exc)


@app.post("/convert")
async def post_convert(request: ConvertRequest) -> Dict[str, Any]:
    """Convierte entre herramientas de diagrama."""
    try:
        return engine.cross_convert(request.src, request.dst, request.payload)
    except Exception as exc:
        raise _fail(exc)


@app.post("/audio/explain")
async def post_audio_explain(request: AudioExplainRequest) -> Dict[str, Any]:
    """Diagrama -> resumen (<=150 palabras) -> traduccion opcional -> TTS -> mp3."""
    try:
        return await audio_engine.explain(
            request.diagram,
            target_lang=request.target_lang,
            voice=request.voice,
        )
    except Exception as exc:
        raise _fail(exc)


@app.get("/audio/{audio_id}")
async def get_audio(audio_id: str) -> FileResponse:
    """Devuelve el mp3 (o wav) generado por /audio/explain."""
    try:
        path = audio_engine.resolve_audio(audio_id)
        if path is None:
            raise HTTPException(
                status_code=404,
                detail=f"audio no encontrado en la cache: '{audio_id}'",
            )
        media_type = "audio/wav" if path.suffix.lower() == ".wav" else "audio/mpeg"
        return FileResponse(path=str(path), media_type=media_type)
    except HTTPException:
        raise
    except Exception as exc:
        raise _fail(exc)


# --------------------------------------------------------------------------
# Rutas del NODO B (X-Ray + VENTANA GAPS). La lógica vive en gaps_store.py y
# xray_audit.py; aqui SOLO se enruta (1 funcion = 1 fichero).
# --------------------------------------------------------------------------
def _xray_store() -> Path:
    return Path(os.environ.get("XRAY_STORE", str(XRAY_DIR / "gaps.json")))


def _xray_inventory() -> Path:
    return Path(os.environ.get("XRAY_INVENTORY", str(XRAY_OUT_DIR / "INVENTORY.json")))


@app.post("/gaps")
async def post_gap(request: GapRequest) -> Dict[str, Any]:
    """Crea un gap. Si la evidencia no valida contra INVENTORY.json -> 400 y NO se crea."""
    try:
        record = gaps_store.add_gap(
            request.model_dump(),
            store_path=_xray_store(),
            inventory_path=_xray_inventory(),
        )
        return {"ok": True, "gap": record}
    except gaps_store.GapsStoreError as exc:
        raise HTTPException(
            status_code=400,
            detail={"ok": False, "error": exc.code, "detail": exc.detail},
        )
    except Exception as exc:
        raise _fail(exc)


@app.get("/gaps")
async def get_gaps(estado: str = "") -> Dict[str, Any]:
    """Lista los gaps + contador por estado/tipo/severidad (lo que pinta V2)."""
    try:
        gaps = gaps_store.load_gaps(_xray_store())
        if estado:
            gaps = [g for g in gaps if str(g.get("estado")) == estado]
        counter = gaps_store.count_gaps(gaps)
        return {"ok": True, "items": gaps, "total": counter["total"], "count": counter}
    except Exception as exc:
        raise _fail(exc)


@app.get("/xray/{artifact}")
async def get_xray_artifact(artifact: str) -> Any:
    """Sirve un artefacto del auditor (allowlist estricta; sin path traversal)."""
    if artifact not in XRAY_ARTIFACTS:
        raise HTTPException(status_code=404, detail=f"artefacto no permitido: {artifact}")
    path = XRAY_OUT_DIR / artifact
    if not path.is_file():
        # El store de gaps puede no existir todavia: se responde con el estado
        # real (vacio) en vez de un 404 que la UI no distingue de un fallo.
        if artifact == "gaps.json":
            return {"schema": "xray-gaps-store/1", "count": 0, "gaps": [],
                    "note": "aun no hay gaps registrados"}
        raise HTTPException(
            status_code=404,
            detail=f"artefacto ausente (ejecuta el auditor): {artifact}",
        )
    if artifact.endswith(".json"):
        return json.loads(path.read_text(encoding="utf-8"))
    # Los .md se sirven como markdown CRUDO (text/markdown): si se devolvieran
    # como string JSON, el frontend veria los \n escapados en vez de saltos.
    return PlainTextResponse(
        content=path.read_text(encoding="utf-8"),
        media_type="text/markdown; charset=utf-8",
    )


@app.post("/xray/audit")
async def post_xray_audit(request: XrayAuditRequest) -> Dict[str, Any]:
    """Re-audita una raiz con xray_audit.py (el motor determinista del NODO B)."""
    root = request.root or str(Path.cwd())
    out = request.out or str(XRAY_OUT_DIR)
    result = audit_runner.run_audit(root, out)
    if not result["ok"]:
        raise HTTPException(status_code=502, detail=result)
    return result


# --------------------------------------------------------------------------
# WebSocket de progreso
# --------------------------------------------------------------------------
@app.websocket("/ws/progress")
async def ws_progress(websocket: WebSocket) -> None:
    """Envia cada 5 s el estado real de health_all() como JSON."""
    await websocket.accept()
    try:
        while True:
            try:
                snapshot = engine.health_all()
                payload = {
                    "type": "health",
                    "data": snapshot,
                    "timestamp": time.time(),
                }
            except Exception as exc:  # pragma: no cover - defensivo
                payload = {
                    "type": "error",
                    "error": f"{type(exc).__name__}: {exc}",
                    "timestamp": time.time(),
                }
            await websocket.send_json(payload)
            await asyncio.sleep(WS_PROGRESS_INTERVAL)
    except WebSocketDisconnect:
        return
    except Exception:
        return


@app.get("/")
async def root() -> Dict[str, Any]:
    """Indice de rutas (sin mock: solo datos reales del backend)."""
    return {
        "service": "canvas-backend",
        "node": "N4-A",
        "routes": [
            "GET /health",
            "POST /render/diagram",
            "POST /render/motion",
            "POST /convert",
            "POST /audio/explain",
            "GET /audio/{audio_id}",
            "POST /gaps",
            "GET /gaps",
            "GET /xray/{artifact}",
            "POST /xray/audit",
            "WS /ws/progress",
            "POST /mcp",
            "GET /mcp/health",
            "DELETE /mcp",
            "POST /guide/match",
            "GET /guide/status",
            "GET /ui/ (frontend estatico)",
        ],
        "diagram_tools": engine.DIAGRAM_TOOLS,
        "motion_tools": engine.MOTION_TOOLS,
        "timestamp": time.time(),
    }


# --------------------------------------------------------------------------
# FRONTEND ESTATICO (refutacion 4, corregida).
# Antes las 3 ventanas (w1_mirror, w2_diff_editor, w3_deploy) NO las servia
# esta app: habia que levantar un http.server aparte. Ahora se sirven desde el
# mismo proceso FastAPI, en /ui, con el MISMO origen que la API -> el fetch
# relative de frontend/shared/api.js funciona sin CORS ni puertos extra.
# El montaje va AL FINAL: en FastAPI gana la primera ruta que coincide, y las
# rutas de la API ya estan registradas arriba.
# --------------------------------------------------------------------------
FRONTEND_DIR = BACKEND_DIR.parent / "frontend"
if FRONTEND_DIR.is_dir():
    app.mount("/ui", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
else:  # pragma: no cover - solo si el entregable esta incompleto
    @app.get("/ui")
    async def ui_missing() -> Dict[str, Any]:
        return {"ok": False, "error": "directorio frontend/ no encontrado",
                "expected": str(FRONTEND_DIR)}

