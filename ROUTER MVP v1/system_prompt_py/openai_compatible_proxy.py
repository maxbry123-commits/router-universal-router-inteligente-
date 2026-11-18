"""
openai_compatible_proxy.py — Data Plane (Salida 1/3)
Ubicacion: ROUTER MVP v1/system_prompt_py/openai_compatible_proxy.py
Delega control via control_bridge; nunca decide, solo ejecuta.
"""
from fastapi import FastAPI, Request, HTTPException, Header
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
        from external.tools.storage_wiring import StorageWiring
        StorageWiring.ensure_bucket()
    except Exception as e:
        print(f"[lifespan] storage_wiring: {e}")
    yield
    try:
        from external.core.mcp_pool import get_pool
        await get_pool().close()
    except Exception as e:
        print(f"[lifespan] shutdown: {e}")

app = FastAPI(lifespan=lifespan)

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
    "Qwen/Qwen2.5-Coder-0.5B-Instruct-GGUF": "swe-code-s1",
    "LiquidAI/LFM2.5-350M-GGUF": "swe-code-s2",
    "unsloth/Qwen3.5-0.8B-GGUF": "swe-code-s3",
}
LOCAL_TIMEOUT_S = 75.0   # el Space puede estar dormido: despertar + cargar modelo cabe en el watchdog de 96 s

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
            # 503 con diagnostico real (conteo de claves y ultimo error), no una cadena generica
            return JSONResponse(status_code=503, content={
                "detail": "Todos los proveedores fallaron",
                "diag": fallback_result.get("diag") or {},
                "mode": detected_mode,
                "service_mode": service_mode,
                "route": route_path,
            })

        provider_used = fallback_result.get("provider")
        content = _content_of(fallback_result.get("response"))

        # 3. Checkpoint opcional: si hay MCP_MEMORY_URL, guardamos; si no, avisamos y continuamos.
        memory_url = os.getenv("MCP_MEMORY_URL")
        if memory_url:
            task = asyncio.create_task(harness_client.send_checkpoint({
                "model": model_requested,
                "provider_used": provider_used,
                "messages": messages
            }))
            task.add_done_callback(_log_checkpoint_error)
        else:
            print("[WARN] MCP_MEMORY_URL no configurada. Chat en modo degradado (sin persistencia).")

        # 4. Respuesta con el contenido real del proveedor.
        return JSONResponse({
            "id": "chatcmpl-fallback",
            "object": "chat.completion",
            "provider": provider_used,
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

@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/v1/modes")
def modes():
    """Catalogo de modos: 12 de codigo + 4 de servicio (Op2)."""
    from router_llm_hf.mode_detector import RULES, SERVICE_MODE_NAMES
    return {
        "code_modes": sorted(RULES.keys()),
        "service_modes": sorted(SERVICE_MODE_NAMES),
        "total": len(RULES) + len(SERVICE_MODE_NAMES),
        "service_routes": {m: c["route"] for m, c in SERVICE_MODES.items()},
        "adapters_repo": "COMAND-CENTER-1/swe-code-adapters",
    }


@app.get("/v1/agents")
def agents():
    """Registro de agentes + si su ruta existe REALMENTE en esta app."""
    import json as _json
    reg_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "router_llm_hf", "AGENTS_REGISTRY.json",
    )
    try:
        with open(reg_path, "r", encoding="utf-8") as fh:
            registry = _json.load(fh)
    except Exception as e:
        return {"ok": False, "error": str(e), "agents": {}}
    app_paths = {getattr(r, "path", "") for r in app.routes}
    out = {}
    for name, cfg in (registry.get("agents") or {}).items():
        endpoint = cfg.get("endpoint") or ""
        path = ""
        if endpoint.startswith(("http://", "https://", "wss://", "ws://")):
            rest = endpoint.split("://", 1)[1]
            path = "/" + rest.split("/", 1)[1] if "/" in rest else "/"
        implemented = bool(path) and path in app_paths
        out[name] = {
            "type": cfg.get("type"),
            "endpoint": endpoint,
            "declared_status": cfg.get("status"),
            "route": path,
            "implemented": implemented,
        }
    return {"ok": True, "agents": out}


@app.get("/v1/modes")
def modes():
    """Catalogo de modos: 12 de codigo + 4 de servicio (Op2)."""
    from router_llm_hf.mode_detector import RULES, SERVICE_MODE_NAMES
    return {
        "code_modes": sorted(RULES.keys()),
        "service_modes": sorted(SERVICE_MODE_NAMES),
        "total": len(RULES) + len(SERVICE_MODE_NAMES),
        "service_routes": {m: c["route"] for m, c in SERVICE_MODES.items()},
        "adapters_repo": "COMAND-CENTER-1/swe-code-adapters",
    }


@app.get("/v1/agents")
def agents():
    """Registro de agentes + si su ruta existe REALMENTE en esta app."""
    import json as _json
    reg_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "router_llm_hf", "AGENTS_REGISTRY.json",
    )
    try:
        with open(reg_path, "r", encoding="utf-8") as fh:
            registry = _json.load(fh)
    except Exception as e:
        return {"ok": False, "error": str(e), "agents": {}}
    app_paths = {getattr(r, "path", "") for r in app.routes}
    out = {}
    for name, cfg in (registry.get("agents") or {}).items():
        endpoint = cfg.get("endpoint") or ""
        path = ""
        if endpoint.startswith(("http://", "https://", "wss://", "ws://")):
            rest = endpoint.split("://", 1)[1]
            path = "/" + rest.split("/", 1)[1] if "/" in rest else "/"
        implemented = bool(path) and path in app_paths
        out[name] = {
            "type": cfg.get("type"),
            "endpoint": endpoint,
            "declared_status": cfg.get("status"),
            "route": path,
            "implemented": implemented,
        }
    return {"ok": True, "agents": out}


@app.get("/v1/modes")
def modes():
    """Catalogo de modos: 12 de codigo + 4 de servicio (Op2)."""
    from router_llm_hf.mode_detector import RULES, SERVICE_MODE_NAMES
    return {
        "code_modes": sorted(RULES.keys()),
        "service_modes": sorted(SERVICE_MODE_NAMES),
        "total": len(RULES) + len(SERVICE_MODE_NAMES),
        "service_routes": {m: c["route"] for m, c in SERVICE_MODES.items()},
        "adapters_repo": "COMAND-CENTER-1/swe-code-adapters",
    }


@app.get("/v1/agents")
def agents():
    """Registro de agentes + si su ruta existe REALMENTE en esta app."""
    import json as _json
    reg_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "router_llm_hf", "AGENTS_REGISTRY.json",
    )
    try:
        with open(reg_path, "r", encoding="utf-8") as fh:
            registry = _json.load(fh)
    except Exception as e:
        return {"ok": False, "error": str(e), "agents": {}}
    app_paths = {getattr(r, "path", "") for r in app.routes}
    out = {}
    for name, cfg in (registry.get("agents") or {}).items():
        endpoint = cfg.get("endpoint") or ""
        path = ""
        if endpoint.startswith(("http://", "https://", "wss://", "ws://")):
            rest = endpoint.split("://", 1)[1]
            path = "/" + rest.split("/", 1)[1] if "/" in rest else "/"
        implemented = bool(path) and path in app_paths
        out[name] = {
            "type": cfg.get("type"),
            "endpoint": endpoint,
            "declared_status": cfg.get("status"),
            "route": path,
            "implemented": implemented,
        }
    return {"ok": True, "agents": out}


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
    body = await request.json()
    task_id = body.get("taskId", "default")
    state = _LOOP_STATE.get(task_id, {})
    if not state:
        raise HTTPException(404, f"Task {task_id} no iniciada")
    state["iteration"] = state.get("iteration", 0) + 1
    return {"ok": True, "iteration": state["iteration"], "state": state}

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
