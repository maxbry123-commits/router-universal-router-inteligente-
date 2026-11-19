"""
openai_compatible_proxy.py — Data Plane (Salida 1/3)
Ubicacion: ROUTER MVP v1/system_prompt_py/openai_compatible_proxy.py
Delega control via control_bridge; nunca decide, solo ejecuta.
"""
from fastapi import FastAPI, Request, HTTPException, Header

# --- Salida 2B: endpoints aditivos ---
try:
    from ext_endpoints import ext_router
    from ext_runtime import ChatRuntimeMiddleware
    _HAS_EXT = True
except Exception as _e:
    ext_router = None; ChatRuntimeMiddleware = None; _HAS_EXT = False
    print(f"[ext] import falló: {_e}")

# --- C6: errores tipados (aditivo) ---
_ERROR_CODES = {
    "sin claves en NVIDIA_KEYS": ("NO_PROVIDER_KEYS", "configura NVIDIA_KEYS o GROQ_KEYS"),
    "sin claves en GROQ_KEYS":   ("NO_PROVIDER_KEYS", "configura NVIDIA_KEYS o GROQ_KEYS"),
    "Todos los proveedores fallaron": ("ALL_PROVIDERS_DOWN", "revisa /v1/providers/health o usa determinista"),
}
def _typed_error(detail: str, request_id: str = "", extra: dict = None) -> dict:
    code, recovery = _ERROR_CODES.get(detail, ("UNKNOWN", "revisar logs"))
    body = {"error": {"code": code, "message": detail,
                      "recovery": recovery, "request_id": request_id}}
    if extra: body["error"].update(extra)
    return body

# --- C5: x-request-id middleware ---
import uuid as _uuid_c5
from starlette.middleware.base import BaseHTTPMiddleware as _BaseMW_C5
class _RequestIdMiddleware(_BaseMW_C5):
    async def dispatch(self, request, call_next):
        rid = request.headers.get("x-request-id") or str(_uuid_c5.uuid4())
        request.state.request_id = rid
        response = await call_next(request)
        response.headers["x-request-id"] = rid
        return response

# --- C4: contrato artifacts[] (aditivo) ---
from typing import TypedDict as _TD_C4, List as _L_C4
class _ArtifactDict(_TD_C4, total=False):
    name: str
    sha256: str
    path: str
    bytes: int

def _validate_artifact(a: dict) -> dict:
    return {"name": str(a.get("name","")),
            "sha256": str(a.get("sha256","")),
            "path": str(a.get("path","")),
            "bytes": int(a.get("bytes",0) or 0)}

def _validate_artifacts(items) -> _L_C4[dict]:
    if not items: return []
    return [_validate_artifact(x) for x in items if isinstance(x, dict)]
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import httpx
import os
import uuid
import threading
import time
import subprocess
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
# FIX (MINIMAX 2E): el proxy importa modulos que viven en SU MISMA carpeta
# (key_pool, fallback_middleware, control_bridge, ...). Con uvicorn y cwd en
# esa carpeta funcionaba, pero importarlo desde otro sitio (tests, otro
# proceso) reventaba con ModuleNotFoundError: key_pool.
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from key_pool import KeyPool
from fallback_middleware import execute_with_fallback_async
from provider_timeouts import get_timeout
from provider_window import ProviderHTTPError
from queue_manager import QueueManager
from control_bridge import BRIDGE
from router_llm_hf.harness_wiring import HarnessClient
from external.core.provider_fallback import ProviderFallback
# Control Plane cableado (Op2): los modos de servicio y su contrato, y el
# detector. Antes el proxy NUNCA detectaba modo ni resolvia adapter.
from router_llm_hf.service_routes import (
    SERVICE_MODES,
    service_mode_for_path,
    local_target_for_mode,
)
from router_llm_hf.mode_detector import detect_mode, detect_service_route

# --- MINIMAX 4: lifecycle ---
try:
    from external.core.power_daemon import PowerDaemon
    _power_daemon = PowerDaemon()
except Exception as _e:
    _power_daemon = None
    print(f"[INFRA] PowerDaemon no disponible: {_e}")

from external.core.billing_monitor import BillingMonitor
from external.core.storage_wiring import StorageWiring
_storage_ok = False
# --- FIN MINIMAX 4 ---


from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app):
    from external.core.env_config import get_env
    _c = get_env()
    if not _c.ROUTER_API_KEY:
        raise RuntimeError('ROUTER_API_KEY ausente')
    """Startup/Shutdown: inicializa y cierra el pool MCP."""
    try:
        from external.core.mcp_pool import get_pool
        get_pool()
    except Exception as e:
        print(f"[lifespan] pool no disponible: {e}")
    try:
        # FIX (MINIMAX 2E): el adaptador del nucleo verifica el bucket con la API
        # real de HF (GET, solo lectura) y NO crea nada. La version de
        # external/tools usaba repo_type="bucket" (invalido en huggingface_hub)
        # e intentaba crear el bucket en cada arranque del Space.
        from external.core.storage_wiring import StorageWiring
        _st = StorageWiring.ensure_bucket()
        print(f"[lifespan] storage_wiring: {_st.get('status')}")
    except Exception as e:
        print(f"[lifespan] storage_wiring: {e}")
    yield
    try:
        from external.core.mcp_pool import get_pool
        await get_pool().close()
    except Exception as e:
        print(f"[lifespan] shutdown: {e}")

app = FastAPI(lifespan=lifespan)
try:
    if _HAS_EXT and ext_router is not None:
        app.include_router(ext_router)
        app.add_middleware(ChatRuntimeMiddleware)
        print("[ext] mounted: feedback, tasks, queue, versions + ChatRuntimeMiddleware")
except Exception as _e:
    print(f"[ext] mount falló: {_e}")

app.add_middleware(_RequestIdMiddleware)

# --- MINIMAX 4: MCP_MEMORY_URL ---
import os as _os
if not _os.getenv("MCP_MEMORY_URL"):
    _os.environ["MCP_MEMORY_URL"] = "hf://buckets/COMAND-CENTER-1/yaiwes-memoria-storage"
    print("[INFRA] MCP_MEMORY_URL configurada: hf://buckets/COMAND-CENTER-1/yaiwes-memoria-storage")
# --- FIN MINIMAX 4 ---


# --- MINIMAX 4: lifecycle ---
@app.on_event("startup")
async def _infra_startup():
    global _storage_ok
    try:
        _storage_ok = StorageWiring.verify_storage_connection()
    except Exception as _e:
        _storage_ok = False
        print(f"[INFRA] StorageWiring falló: {_e}")
    if _power_daemon is not None:
        try:
            if hasattr(_power_daemon, "start"):
                _power_daemon.start()
            else:
                print("[INFRA] PowerDaemon sin .start() — no se arranca.")
        except Exception as _e:
            print(f"[INFRA] PowerDaemon.start() falló: {_e}")
    print(f"[INFRA] storage_ok={_storage_ok} power_daemon={'ON' if _power_daemon else 'OFF'}")

@app.on_event("shutdown")
async def _infra_shutdown():
    if _power_daemon is not None and hasattr(_power_daemon, "stop"):
        try:
            _power_daemon.stop()
        except Exception as _e:
            print(f"[INFRA] PowerDaemon.stop() falló: {_e}")
    print("[INFRA] shutdown")

@app.get("/billing/status")
def billing_status():
    return BillingMonitor.check_runtime_cost()
# --- FIN MINIMAX 4 ---


# Minimax 1 - CORS para que el navegador del frontend (montado en /chat) pueda llamar al proxy
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Minimax 1 - montaje del frontend estatico (chat-router/chat) en /chat
# Ruta ABSOLUTA: el Space arranca con CWD en "ROUTER MVP v1/system_prompt_py"
FRONTEND_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "chat-router", "chat",
)


def create_app():
    """Monta el frontend estatico en /chat y devuelve la app."""
    try:
        if not os.path.isdir(FRONTEND_DIR):
            raise FileNotFoundError(f"no existe: {FRONTEND_DIR}")
        app.mount("/chat", StaticFiles(directory=FRONTEND_DIR, html=True), name="chat")
        print(f"[OK] Frontend montado en /chat -> {FRONTEND_DIR}")
    except Exception as e:
        print(f"[WARN] No se pudo montar el frontend: {e}")
    return app


app = create_app()
GROQ_KEYS = [k.strip() for k in os.getenv("GROQ_KEYS", "").split(",") if k.strip()]
NVIDIA_KEYS = [k.strip() for k in os.getenv("NVIDIA_KEYS", "").split(",") if k.strip()]

PROVIDERS = {
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "pool": KeyPool("groq", GROQ_KEYS),
        "default_model": "openai/gpt-oss-120b",
    },
    "nvidia": {
        "base_url": "https://integrate.api.nvidia.com/v1",
        "pool": KeyPool("nvidia", NVIDIA_KEYS),
        "default_model": "nvidia/nemotron-3.5-lightning-30b-a3b",
    },
}

ROUTER_API_KEY = os.getenv("ROUTER_API_KEY")
if not ROUTER_API_KEY:
    raise RuntimeError("FATAL: ROUTER_API_KEY no configurada.")

QUEUE = QueueManager(max_concurrent=3)

# Minimax 1 — pool MCP (10 conexiones) + cadena de fallback NVIDIA/Groq
harness_client = HarnessClient()
provider_fb = ProviderFallback()


def daily_cleanup_loop():
    while True:
        time.sleep(86400)
        try:
            subprocess.run(["python3", "maintenance.py"], check=False)
        except Exception as e:
            print(f"Error en mantenimiento: {e}")


threading.Thread(target=daily_cleanup_loop, daemon=True).start()


def _log_checkpoint_error(task):
    """Log del fallo del checkpoint (no bloqueante)."""
    try:
        exc = task.exception()
        if exc:
            print(f"[WARN] Fallo checkpoint (no bloqueante): {exc}")
    except Exception as e:
        print(f"[WARN] Fallo checkpoint (no bloqueante): {e}")


def _content_of(response) -> str:
    """Extrae el texto de una respuesta OpenAI-compatible."""
    try:
        msg = response["choices"][0]["message"]
        content = msg.get("content")
        if not content:
            content = msg.get("reasoning_content")   # modelos de razonamiento
        return content or ""
    except Exception:
        return str(response)


# Modelos locales (Grupo 2) -> Space que los sirve. registry.json 2.0.0 models.local
LOCAL_SPACES = {
    "Qwen/Qwen2.5-Coder-0.5B-Instruct-GGUF": "space-grupo-2-router-llm-hf-1",
    "LiquidAI/LFM2.5-350M-GGUF": "space-grupo-2-router-llm-hf-2",
    "unsloth/Qwen3.5-0.8B-GGUF": "space-grupo-2-router-llm-hf-3",
}
LOCAL_TIMEOUT_S = 75.0   # el Space puede estar dormido: despertar + cargar modelo cabe en el watchdog de 96 s

# --- MINIMAX 2E: agentes + espejo (mirror) ---
# Los agentes del registro central (router_llm_hf/AGENTS_REGISTRY.json) se
# exponen por HTTP para que el chat y sus paneles (OpenClaw, Hermes) los usen
# con el MISMO motor de los Motores: la ruta es determinista y no depende de
# ningun servicio externo adicional.
AGENT_PROMPTS = {
    "openclaw": (
        "Eres OpenClaw, el agente autonomo del router. Resuelves la tarea de "
        "punta a punta y no pides confirmacion en cada paso."
    ),
    "hermes": (
        "Eres Hermes, el agente de comunicacion del router. Redactas, "
        "resumes y mantienes el hilo con la persona."
    ),
    "chat_a": (
        "Eres ChatA, el arquitecto del router. Descompones la tarea, propones "
        "el plan y el consejo tecnico antes de escribir codigo."
    ),
    "chat_b": (
        "Eres ChatB, el implementador del router. Escribes el codigo, usas las "
        "herramientas y devuelves el resultado verificable."
    ),
    "ruflo": (
        "Eres Ruflo, la raiz de agente claude-flow del workspace. Planificas "
        "con agentes especializados (architect, coder, reviewer, security) y "
        "devuelves el plan y el resultado verificable."
    ),
    "rowboat": (
        "Eres Rowboat, la raiz de agente del workspace. Explicas, operas y "
        "documentas con los componentes disponibles y devuelves el resultado."
    ),
}


def _agent_prompt(agent_name: str):
    return AGENT_PROMPTS.get(agent_name)


def _motor_determinista(messages=None, respuesta_externa="", **kw):
    # C7: consolidado en el fallback unificado (external/core/provider_fallback.py).
    # ADAPTACION DECLARADA: el DAG delegaba con *a/**kw, asi que el primer
    # argumento (la lista de mensajes) llegaba como prompt y el motor recibia la
    # repr de la lista -> no detectaba la peticion de archivo. Aqui se extrae el
    # prompt del usuario antes de delegar (mismo comportamiento real).
    from external.core.provider_fallback import deterministic_fallback
    prompt = ""
    if isinstance(messages, str):
        prompt = messages
    else:
        for _m in (messages or []):
            if isinstance(_m, dict) and _m.get("role") == "user":
                prompt = _m.get("content") or ""
                break
    det = deterministic_fallback(prompt, artifact_dir=ARTIFACT_DIR)
    if not isinstance(det, dict):
        det = {"content": str(det), "artifacts": []}
    det.setdefault("artifacts", [])
    det.setdefault("content", "")
    if respuesta_externa:
        det["content"] = f"{respuesta_externa}\n\n{det.get('content') or ''}"
    return det

async def _run_chat_chain(messages, model_requested, *, service_mode=None, route_path="",
                          detected_mode=None, adapter=None, agent=None):
    """Nucleo de ejecucion del chat (compartido por el chat y por el espejo).

    Orden determinista:
      1. Harness DeepSeek, si AGENT_HARNESS_URL esta configurada.
      2. Motores: Local (S1/S2/S3) -> NVIDIA -> Groq.
      3. Checkpoint en el banco de memoria, si hay endpoint HTTP.
    """
    adapter = adapter or {}

    # 0. Harness DeepSeek (env-gated). Si responde, su respuesta es la que sale:
    #    es el motor mas determinista de la casa. Si falla, se avisa y se sigue
    #    con la cadena de Motores (el error nunca se pierde en silencio).
    harness_url = os.getenv("AGENT_HARNESS_URL")
    if harness_url:
        try:
            from router_llm_hf.harness_wiring import call_harness
            hres = await call_harness({"messages": messages, "max_tokens": 1024})
            hcontent = _content_of(hres)
            if hcontent:
                return JSONResponse({
                    "id": "chatcmpl-harness",
                    "object": "chat.completion",
                    "provider": "harness",
                    "agent": agent,
                    "mode": detected_mode,
                    "service_mode": service_mode,
                    "route": route_path,
                    "model": model_requested,
                    "choices": [{
                        "index": 0,
                        "message": {"role": "assistant", "content": hcontent},
                        "finish_reason": "stop"
                    }]
                })
        except Exception as e:
            print(f"[harness] fallback a Motores: {type(e).__name__}: {e}")

    # 1. Ejecucion local: Space del Grupo 2 que sirve ese modelo.
    async def local_execution(msgs: list):
        space = LOCAL_SPACES.get(model_requested)
        model_to_serve = model_requested
        # Ruta de servicio: el Space del Grupo 2 lo decide el modo (Op2).
        if not space and service_mode:
            _target = local_target_for_mode(service_mode)
            if _target:
                space, model_to_serve = _target
        if not space:
            raise NotImplementedError(f"modelo no local: {model_requested}")
        url = f"https://comand-center-1-{space}.hf.space/v1/chat/completions"
        headers = {"x-api-key": ROUTER_API_KEY, "Content-Type": "application/json"}
        try:
            r = await provider_fb.client.post(
                url, headers=headers,
                json={"model": model_to_serve, "messages": msgs},
                timeout=LOCAL_TIMEOUT_S,
            )
        except Exception as e:
            raise RuntimeError(f"Space {space} inaccesible: {e}")
        if r.status_code != 200:
            raise RuntimeError(f"Space {space} HTTP {r.status_code}")
        return r.json()

    # 2. Cadena de fallback: Local -> NVIDIA (4 APIs) -> Groq (6 APIs), con HTTP real.
    await QUEUE.acquire()
    try:
        fallback_result = await BRIDGE.run(
            str(uuid.uuid4()),
            provider_fb.call(messages, model_requested=model_requested, local_fn=local_execution),
        )
        if fallback_result.get("provider") == "none":
            # MINIMAX 2H: la cadena se queda sin proveedor externo (NVIDIA/Groq
            # sin clave, Spaces PAUSED por 402). Antes: 503 y el chat muerto.
            # Ahora el ultimo eslabon es el motor determinista local, que
            # responde con el estado REAL del sistema. El diagnostico se
            # conserva: el error nunca se pierde en silencio.
            det = _motor_determinista(messages)
            return JSONResponse({
                "id": "chatcmpl-determinista",
                "object": "chat.completion",
                "provider": "determinista",
                "degraded": True,
                "mode": detected_mode,
                "service_mode": service_mode,
                "route": route_path,
                "agent": agent,
                "model": model_requested,
                "diag": fallback_result.get("diag") or {},
                "artifacts": det.get("artifacts") or [],
                "tipo": det.get("tipo"),
                "choices": [{
                    "index": 0,
                    "message": {"role": "assistant", "content": det.get("content") or ""},
                    "finish_reason": "stop"
                }]
            })

        provider_used = fallback_result.get("provider")
        content = _content_of(fallback_result.get("response"))

        # 3. Checkpoint en el banco de memoria. Si MCP_MEMORY_URL es hf:// no hay
        #    POST posible: harness_wiring lo deja encolado en local (sin falso OK).
        memory_url = os.getenv("MCP_MEMORY_URL")
        memory_http = os.getenv("MCP_MEMORY_HTTP_URL")
        if memory_url or memory_http:
            task = asyncio.create_task(harness_client.send_checkpoint({
                "model": model_requested,
                "provider_used": provider_used,
                "agent": agent,
                "messages": messages
            }))
            task.add_done_callback(_log_checkpoint_error)
        else:
            print("[WARN] MCP_MEMORY_URL no configurada. Chat en modo degradado (sin persistencia).")

        # 4. Si el mensaje pide un archivo, se materializa (sha256 real) y el
        #    bloque del artefacto se antepone al contenido: el chat lo muestra.
        _prompt = ""
        for _m in messages or []:
            if _m.get("role") == "user":
                _prompt = _m.get("content") or ""
                break
        artifacts: list = []
        try:
            from router_llm_hf.chat_engine import pide_archivo
            _pide = pide_archivo(_prompt)
        except Exception:
            _pide = None
        if _pide:
            det = _motor_determinista(messages, respuesta_externa=content)
            artifacts = det.get("artifacts") or []
            content = det.get("content") or content

        # 5. Respuesta con el contenido real del proveedor.
        return JSONResponse({
            "id": "chatcmpl-fallback",
            "object": "chat.completion",
            "provider": provider_used,
            "agent": agent,
            "artifacts": _validate_artifacts(artifacts),
            "degraded": bool(fallback_result.get("degraded")),
            "mode": detected_mode,
            "service_mode": service_mode,
            "route": route_path,
            "adapter": {
                "base_model": adapter.get("base_model"),
                "lora": adapter.get("lora"),
                "dataset": adapter.get("dataset"),
            },
            "model": model_requested,
            "choices": [{
                "index": 0,
                "message": {"role": "assistant", "content": content},
                "finish_reason": "stop"
            }]
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(502, detail=str(e))
    finally:
        await QUEUE.release()


@app.post("/v1/nvidia")
@app.post("/v1/groq")
@app.post("/v1/swe")
@app.post("/v1/swe-free")
@app.post("/v1/team-qwe")
@app.post("/v1/deployment")
@app.post("/v1/chat/completions")
async def chat_completions(request: Request, x_api_key: str = Header(None)):
    if x_api_key != ROUTER_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")

    try:
        body = await request.json()
    except Exception:
        raise HTTPException(400, detail="Invalid JSON")

    messages = body.get("messages") or []
    if not messages:
        raise HTTPException(400, detail="messages vacio")
    # Extraemos el modelo. Si el selector envia "nvidia:minimax...", lo limpiamos.
    raw_model = body.get("model", "auto")
    model_requested = raw_model.split(":")[-1] if ":" in raw_model else raw_model
    model_auto = model_requested in ("auto", "", "default")

    # --- RUTA DE SERVICIO (Op2) --------------------------------------------
    # /v1/swe, /v1/swe-free, /v1/team-qwe y /v1/deployment dejan de ser el
    # mismo handler generico: cada una tiene su modo y su destino.
    route_path = request.url.path
    service_mode = service_mode_for_path(route_path)
    if service_mode and model_auto:
        _target = local_target_for_mode(service_mode)
        if _target:
            model_requested = _target[1]

    # --- CONTROL PLANE (Op2): deteccion de modo + adapter -------------------
    prompt = ""
    for _m in messages:
        if _m.get("role") == "user":
            prompt = _m.get("content") or ""
            break
    detected_mode = detect_service_route(prompt) or detect_mode(prompt)
    adapter = {}
    try:
        from router_llm_hf.mode_router import get_adapter_config
        adapter = get_adapter_config(detected_mode) or {}
    except Exception as _e:
        print(f"[CTRL] adapter no resoluble para {detected_mode}: {_e}")

    return await _run_chat_chain(
        messages, model_requested,
        service_mode=service_mode, route_path=route_path,
        detected_mode=detected_mode, adapter=adapter,
    )


async def _agent_request(agent_name, request: Request, x_api_key):
    """Espejo HTTP de un agente del registro central.

    El chat y sus paneles usan esta ruta: el agente se ejecuta con el MISMO
    motor de los Motores, asi que el espejo es determinista.
    """
    if x_api_key != ROUTER_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    prompt = _agent_prompt(agent_name)
    if not prompt:
        raise HTTPException(404, detail=f"agente desconocido: {agent_name}; known={sorted(AGENT_PROMPTS)}")

    # MINIMAX 2F · interruptor ON/OFF: un agente apagado no se enruta.
    try:
        from router_llm_hf.agent_router import get_agent, is_enabled
        if get_agent(agent_name) and not is_enabled(agent_name):
            raise HTTPException(
                status_code=409,
                detail=f"agente {agent_name} esta OFF (interruptor del registro central); "
                       f"enciendelo en /v1/agents/{agent_name}/state o en la ventana AGENTES del chat",
            )
    except HTTPException:
        raise
    except Exception as _e:
        print(f"[AGENTS] estado de {agent_name} no consultable: {_e}")

    try:
        body = await request.json()
    except Exception:
        raise HTTPException(400, detail="Invalid JSON")
    user_messages = body.get("messages") or []
    if not user_messages:
        raise HTTPException(400, detail="messages vacio")
    messages = [{"role": "system", "content": prompt}] + user_messages
    raw_model = body.get("model", "auto")
    model_requested = raw_model.split(":")[-1] if ":" in raw_model else raw_model
    user_prompt = ""
    for _m in user_messages:
        if _m.get("role") == "user":
            user_prompt = _m.get("content") or ""
            break
    detected = detect_service_route(user_prompt) or detect_mode(user_prompt)
    return await _run_chat_chain(
        messages, model_requested,
        service_mode=None, route_path=f"/v1/agents/{agent_name}",
        detected_mode=detected, adapter={}, agent=agent_name,
    )


@app.post("/v1/agents/{agent_name}")
async def agent_chat(agent_name: str, request: Request, x_api_key: str = Header(None)):
    return await _agent_request(agent_name, request, x_api_key)


@app.post("/v1/openclaw")
async def openclaw_chat(request: Request, x_api_key: str = Header(None)):
    return await _agent_request("openclaw", request, x_api_key)


@app.post("/v1/hermes")
async def hermes_chat(request: Request, x_api_key: str = Header(None)):
    return await _agent_request("hermes", request, x_api_key)


@app.get("/v1/agents")
async def list_agents():
    """Agentes del registro central: el chat los lee de aqui (no hardcodeados).

    MINIMAX 2F: una sola ruta canonica (antes habia 4 definiciones y FastAPI
    solo honraba la primera). Cada agente trae su interruptor ON/OFF real, si
    su ruta existe de verdad en esta app, su historial y su memoria.
    """
    from router_llm_hf.agent_router import list_agents as _list
    try:
        data = _list()
    except Exception as e:
        return {"ok": False, "error": str(e), "agents": {}}
    app_paths = {getattr(r, "path", "") for r in app.routes}
    for name, cfg in (data.get("agents") or {}).items():
        path = cfg.get("chat_path") or ""
        cfg["route"] = path
        cfg["implemented"] = bool(path) and path in app_paths
        cfg["mirror"] = bool(cfg.get("mirror_endpoint"))
        cfg["tools"] = cfg.get("tools") or []
    data["botonera_ids"] = [b["id"] for b in _botonera()]
    return data


def _botonera():
    """Botonera NCT/APEX (9 botones + HANDOFF)."""
    try:
        from router_llm_hf.nct_format import BOTONERA
        return BOTONERA
    except Exception:
        return []


@app.post("/v1/agents/{agent_name}/state")
async def agent_state(agent_name: str, request: Request, x_api_key: str = Header(None)):
    """Interruptor ON/OFF del agente. Body: {"enabled": true|false}."""
    if x_api_key != ROUTER_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(400, detail="Invalid JSON")
    if "enabled" not in body:
        raise HTTPException(400, detail="falta 'enabled'")
    try:
        from router_llm_hf.agent_router import set_agent_enabled
        state = set_agent_enabled(agent_name, bool(body["enabled"]), str(body.get("reason") or "chat"))
    except KeyError as e:
        raise HTTPException(404, detail=str(e))
    except Exception as e:
        raise HTTPException(500, detail=f"no se pudo cambiar el estado: {e}")
    return {"ok": True, "agent": agent_name, "state": state}


@app.get("/v1/agents/{agent_name}/history")
async def agent_history(agent_name: str, limit: int = 50, x_api_key: str = Header(None)):
    """Historial append-only del agente (turnos guardados)."""
    if x_api_key != ROUTER_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    try:
        from router_llm_hf.agent_state import get_history
        turns = get_history(agent_name, limit=limit)
    except Exception as e:
        raise HTTPException(500, detail=str(e))
    return {"ok": True, "agent": agent_name, "count": len(turns), "turns": turns}


@app.get("/v1/agents/{agent_name}/memory")
async def agent_memory_get(agent_name: str, x_api_key: str = Header(None)):
    """Memoria persistente del agente (clave -> valor)."""
    if x_api_key != ROUTER_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    try:
        from router_llm_hf.agent_state import get_memory, memory_keys
        memory = get_memory(agent_name)
    except Exception as e:
        raise HTTPException(500, detail=str(e))
    return {"ok": True, "agent": agent_name, "memory": memory, "keys": sorted(memory_keys(agent_name))}


@app.post("/v1/agents/{agent_name}/memory")
async def agent_memory_set(agent_name: str, request: Request, x_api_key: str = Header(None)):
    """Guarda memoria del agente. Body: {"key": "...", "value": ...} o {"patch": {...}}."""
    if x_api_key != ROUTER_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(400, detail="Invalid JSON")
    try:
        from router_llm_hf.agent_state import merge_memory, set_memory
        if body.get("patch"):
            memory = merge_memory(agent_name, body["patch"])
        elif body.get("key"):
            memory = set_memory(agent_name, str(body["key"]), body.get("value"))
        else:
            raise HTTPException(400, detail="falta 'key' o 'patch'")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, detail=str(e))
    return {"ok": True, "agent": agent_name, "memory": memory}


@app.get("/harness/health")
async def harness_health():
    """Estado real del Harness DeepSeek (no lanza excepcion)."""
    from router_llm_hf.harness_wiring import health_harness
    return await health_harness()

@app.get("/health")
def health():
    return {"status": "ok"}


# ─── MINIMAX 2F · ARTIFACTOS (crear/leer md, py, html y otros) ───────────
ARTIFACT_DIR = os.getenv("ARTIFACT_DIR", os.path.join(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))), "artifacts"))
ARTIFACT_KINDS = ("md", "py", "html", "json", "txt", "csv", "yaml", "yml", "sh")


def _artifact_safe(name: str) -> str:
    base = os.path.basename(str(name or "").strip())
    base = base.replace("..", "_").replace("/", "_")
    if not base or base in (".", ".."):
        raise HTTPException(400, detail="nombre de artefacto invalido")
    return base


@app.get("/v1/artifacts")
async def list_artifacts(x_api_key: str = Header(None)):
    """Artefactos reales del workspace (con sha256 y tamano)."""
    import hashlib
    out = []
    try:
        names = sorted(os.listdir(ARTIFACT_DIR))
    except FileNotFoundError:
        names = []
    except OSError as e:
        raise HTTPException(500, detail=str(e))
    for name in names:
        path = os.path.join(ARTIFACT_DIR, name)
        if not os.path.isfile(path):
            continue
        data = open(path, "rb").read()
        out.append({
            "name": name,
            "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
            "kind": name.rsplit(".", 1)[-1] if "." in name else "",
        })
    return {"ok": True, "dir": ARTIFACT_DIR, "count": len(out), "artifacts": out,
            "kinds": list(ARTIFACT_KINDS)}


@app.post("/v1/artifacts")
async def create_artifact(request: Request, x_api_key: str = Header(None)):
    """Crea un artefacto (markdown, python, html y otros).

    Body: {"name": "x.md", "content": "...", "kind": "md"}
    """
    import hashlib
    if x_api_key != ROUTER_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(400, detail="Invalid JSON")
    name = _artifact_safe(body.get("name") or "")
    content = body.get("content")
    if content is None:
        raise HTTPException(400, detail="falta 'content'")
    if not isinstance(content, str):
        raise HTTPException(400, detail="'content' debe ser texto")
    kind = str(body.get("kind") or (name.rsplit(".", 1)[-1] if "." in name else "txt")).lower()
    if kind not in ARTIFACT_KINDS:
        raise HTTPException(400, detail=f"kind no soportado: {kind}; soportados={list(ARTIFACT_KINDS)}")
    if not name.endswith("." + kind):
        name = f"{name}.{kind}"
    try:
        os.makedirs(ARTIFACT_DIR, exist_ok=True)
        path = os.path.join(ARTIFACT_DIR, name)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(content)
    except OSError as e:
        raise HTTPException(500, detail=f"no se pudo escribir el artefacto: {e}")
    data = content.encode("utf-8")
    return {"ok": True, "name": name, "path": path, "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(), "kind": kind}


@app.get("/v1/artifacts/{name}")
async def read_artifact(name: str, x_api_key: str = Header(None)):
    """Lee un artefacto por nombre."""
    path = os.path.join(ARTIFACT_DIR, _artifact_safe(name))
    if not os.path.isfile(path):
        raise HTTPException(404, detail=f"artefacto no encontrado: {name}")
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        return {"ok": True, "name": os.path.basename(path), "content": fh.read()}


# ─── MINIMAX 2F · NCT/APEX: input 📌, salida F3/F4, botonera, recovery ───
@app.post("/v1/nct/parse")
async def nct_parse(request: Request, x_api_key: str = Header(None)):
    """Parsea el bloque 📌 y devuelve clasificacion + campos + vista previa."""
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(400, detail="Invalid JSON")
    text = body.get("text") or body.get("input") or ""
    try:
        from router_llm_hf import nct_format
        parsed = nct_format.parse_input_block(text)
        classification = nct_format.classify_input(text)
        preview = nct_format.render_input_preview(parsed, classification)
    except Exception as e:
        raise HTTPException(500, detail=str(e))
    return {"ok": True, "parsed": parsed, "classification": classification, "preview": preview}


@app.post("/v1/nct/render")
async def nct_render(request: Request, x_api_key: str = Header(None)):
    """Renderiza la salida normalizada F3/F4 (con handoff interno, no visible)."""
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(400, detail="Invalid JSON")
    try:
        from router_llm_hf import nct_format
        out = nct_format.render_output(body.get("data") or body, body.get("format"))
    except Exception as e:
        raise HTTPException(500, detail=str(e))
    return out


@app.get("/v1/nct/botonera")
async def nct_botonera(x_api_key: str = Header(None)):
    """Botonera del sistema (9 botones + HANDOFF)."""
    from router_llm_hf.nct_format import BOTONERA
    return {"ok": True, "botonera": BOTONERA, "count": len(BOTONERA)}


@app.get("/v1/nct/recovery")
async def nct_recovery(x_api_key: str = Header(None)):
    """Estado de recuperacion reconstruido de la bitacora (no es un archivo)."""
    try:
        from router_llm_hf.nct_format import recovery_state
        return recovery_state()
    except Exception as e:
        raise HTTPException(500, detail=str(e))


# ─── MINIMAX 2F · RAICES: estado real + auto-pull (dry-run por defecto) ───
@app.get("/v1/roots")
async def roots_status(x_api_key: str = Header(None)):
    """Estado real de las 3 raices del workspace y su manifest."""
    import hashlib
    import json as _json
    try:
        from router_llm_hf.agent_router import load_registry
        reg = load_registry()
    except Exception as e:
        raise HTTPException(500, detail=str(e))
    repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    out = {}
    for name, cfg in (reg.get("roots") or {}).items():
        rel = cfg.get("path") or ""
        path = os.path.join(repo_root, rel)
        entry = {
            "path": rel,
            "exists": os.path.isdir(path),
            "kind": cfg.get("kind"),
            "source": cfg.get("source"),
            "auto_pull": bool(cfg.get("auto_pull")),
            "manifest": cfg.get("manifest"),
            "note": cfg.get("note"),
        }
        if entry["exists"]:
            try:
                total = 0
                files = 0
                for root, _dirs, names in os.walk(path):
                    files += len(names)
                    for n in names:
                        try:
                            total += os.path.getsize(os.path.join(root, n))
                        except OSError:
                            pass
                entry["files"] = files
                entry["bytes"] = total
            except OSError as e:
                entry["error"] = str(e)
        manifest_path = cfg.get("manifest")
        if manifest_path:
            mpath = os.path.join(repo_root, manifest_path)
            if os.path.isfile(mpath):
                try:
                    with open(mpath, "rb") as fh:
                        raw = fh.read()
                    entry["manifest_sha256"] = hashlib.sha256(raw).hexdigest()
                    entry["manifest_bytes"] = len(raw)
                    data = _json.loads(raw.decode("utf-8"))
                    if isinstance(data, dict):
                        entry["manifest_keys"] = sorted(data.keys())[:20]
                        if "parts" in data:
                            entry["manifest_parts"] = len(data["parts"])
                        if "extraction_verified" in data:
                            entry["extraction_verified"] = data["extraction_verified"]
                except Exception as e:
                    entry["manifest_error"] = str(e)
        out[name] = entry
    return {"ok": True, "count": len(out), "roots": out}


@app.post("/v1/roots/pull")
async def roots_pull(request: Request, x_api_key: str = Header(None)):
    """Auto-pull de las raices. Body: {"apply": false} (dry-run por defecto)."""
    if x_api_key != ROUTER_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    try:
        body = await request.json()
    except Exception:
        body = {}
    apply_changes = bool(body.get("apply"))
    script = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))), "scripts", "pull_agent_roots.py")
    if not os.path.isfile(script):
        raise HTTPException(500, detail="no existe scripts/pull_agent_roots.py")
    import subprocess
    import sys as _sys
    cmd = [_sys.executable, script, "--all"] + (["--apply"] if apply_changes else [])
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    except Exception as e:
        raise HTTPException(500, detail=f"auto-pull fallo: {e}")
    return {"ok": proc.returncode == 0, "apply": apply_changes, "returncode": proc.returncode,
            "stdout": proc.stdout[-8000:], "stderr": proc.stderr[-4000:]}


@app.get("/v1/modes")
def modes():
    """Catalogo de modos: codigo + servicio (Op2). MINIMAX 2F: ruta unica."""
    from router_llm_hf.mode_detector import RULES, SERVICE_MODE_NAMES
    return {
        "code_modes": sorted(RULES.keys()),
        "service_modes": sorted(SERVICE_MODE_NAMES),
        "total": len(RULES) + len(SERVICE_MODE_NAMES),
        "service_routes": {m: c["route"] for m, c in SERVICE_MODES.items()},
        "adapters_repo": "COMAND-CENTER-1/swe-code-adapters",
    }


@app.get("/control-plane/status")
def control_plane_status():
    return BRIDGE.status()


# ─── ENDPOINTS /v1/loop/* (para el LOOP del frontend) ───
_LOOP_STATE: dict = {}

@app.get("/v1/loop/config")
async def loop_config():
    return {"max_iterations": int(os.getenv("LOOP_MAX_ITER", "8"))}

@app.post("/v1/loop/start")
async def loop_start(request: Request):
    body = await request.json()
    task_id = body.get("taskId", "default")
    _LOOP_STATE[task_id] = {"iteration": 0, "status": "running"}
    return {"ok": True, "taskId": task_id}

@app.post("/v1/loop/step")
async def loop_step(request: Request):
    """Un paso del loop REAL: ejecuta el motor determinista y deja checkpoint.

    FIX (MINIMAX 2E): antes solo incrementaba un contador, asi que el panel LOOP
    del chat no ejecutaba nada y /v1/loop/resume no encontraba ningun
    checkpoint que reanudar.
    """
    body = await request.json()
    task_id = body.get("taskId", "default")
    state = _LOOP_STATE.get(task_id, {})
    if not state:
        raise HTTPException(404, f"Task {task_id} no iniciada")
    state["iteration"] = state.get("iteration", 0) + 1
    engine = {}
    try:
        from router_llm_hf.loop_engine import main as engine_main
        import json as _json
        import io as _io
        import contextlib as _ctx
        buf = _io.StringIO()
        with _ctx.redirect_stdout(buf):
            rc = engine_main([
                "loop_engine",
                _json.dumps({
                    "input": body.get("input", ""),
                    "iteration": state["iteration"],
                    "max_iterations": int(body.get("maxIterations") or os.getenv("LOOP_MAX_ITER", "8")),
                    "task_id": task_id,
                }),
            ])
        engine = _json.loads(buf.getvalue() or "{}")
        if rc not in (0, 2):
            engine = {"error": f"motor rc={rc}"}
        state["status"] = "done" if engine.get("done") else "running"
        state["mode"] = engine.get("mode")
        state["engine"] = engine
    except Exception as e:
        state["status"] = "error"
        state["error"] = f"{type(e).__name__}: {e}"
    _LOOP_STATE[task_id] = state
    return {"ok": True, "iteration": state["iteration"], "state": state, "engine": engine}

@app.post("/v1/loop/error")
async def loop_error(request: Request):
    body = await request.json()
    task_id = body.get("taskId", "default")
    if task_id in _LOOP_STATE:
        _LOOP_STATE[task_id]["status"] = "error"
    return {"ok": True, "logged": True}


@app.get("/v1/loop/resume")
async def loop_resume(taskId: str):
    import json
    from router_llm_hf.checkpoint_manager import CheckpointManager
    cm = CheckpointManager()
    try:
        if taskId not in cm.list_checkpoints():
            return {"ok": False, "reason": "not_found"}
        state = json.loads(open(f"state/checkpoints/{taskId}.json").read())
        return {"ok": True, "state": state,
                "next_iteration": state.get("iteration", 0)}
    except Exception as e:
        return {"ok": False, "error": f"{type(e).__name__}:{e}"}
