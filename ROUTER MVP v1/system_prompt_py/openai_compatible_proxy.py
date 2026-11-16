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

app = FastAPI()

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

    # 1. Ejecucion local: Space del Grupo 2 que sirve ese modelo.
    async def local_execution(msgs: list):
        space = LOCAL_SPACES.get(model_requested)
        if not space:
            raise NotImplementedError(f"modelo no local: {model_requested}")
        url = f"https://comand-center-1-{space}.hf.space/v1/chat/completions"
        headers = {"x-api-key": ROUTER_API_KEY, "Content-Type": "application/json"}
        try:
            r = await provider_fb.client.post(
                url, headers=headers,
                json={"model": model_requested, "messages": msgs},
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
            return JSONResponse(status_code=503, content={"detail": "Todos los proveedores fallaron", "diag": fallback_result.get("diag") or {}})

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


@app.get("/control-plane/status")
def control_plane_status():
    return BRIDGE.status()
