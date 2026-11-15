"""
openai_compatible_proxy.py — Data Plane (Salida 1/3)
Ubicacion: ROUTER MVP v1/system_prompt_py/openai_compatible_proxy.py
Delega control via control_bridge; nunca decide, solo ejecuta.
"""
from fastapi import FastAPI, Request, HTTPException, Header
from fastapi.responses import JSONResponse
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
        "default_model": "meta/llama-3.3-70b-instruct",
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


def _content_of(response) -> str:
    """Extrae el texto de una respuesta OpenAI-compatible."""
    try:
        return response["choices"][0]["message"]["content"]
    except Exception:
        return str(response)


@app.post("/v1/chat/completions")
async def chat_completions(request: Request, x_api_key: str = Header(None)):
    if x_api_key != ROUTER_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")

    # FAIL_CLOSED: sin banco de memoria no hay checkpoint, luego no hay respuesta.
    if not os.getenv("MCP_MEMORY_URL"):
        raise HTTPException(status_code=503, detail="MCP_MEMORY_URL no configurada: checkpoint al banco de memoria obligatorio (fail-closed)")

    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    messages = body.get("messages") or []
    if not messages:
        raise HTTPException(status_code=400, detail="messages vacio")
    model_requested = body.get("model", "auto")
    session_id = request.headers.get("X-Session-Id") or str(uuid.uuid4())
    task_id = str(uuid.uuid4())
    last = messages[-1]
    prompt = last.get("content", "") if isinstance(last, dict) else str(last)

    # 1. Cadena de fallback: HF local (Grupo 2) -> NVIDIA (4 APIs) -> Groq (6 APIs).
    #    provider_fb decide el proveedor; la ejecucion real la hace el pool de claves.
    async def local_execution(msgs: list):
        # El modelo local vive en los Spaces del Grupo 2: no cableado en este Data Plane.
        raise NotImplementedError("modelo local no cableado en el Data Plane")

    providers_order = ["groq", "nvidia"] if "groq" in model_requested.lower() else ["nvidia", "groq"]

    await QUEUE.acquire()
    try:
        async def call_provider(provider, prompt, model_family):
            cfg = PROVIDERS[provider]
            key = cfg["pool"].get_key(session_id=session_id)
            if not key:
                raise RuntimeError(f"Sin keys en {provider}")
            headers = {
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": body.get("model", cfg["default_model"]),
                "messages": body["messages"],
                "temperature": 0.1,
            }
            timeout = get_timeout(provider)
            async with httpx.AsyncClient(timeout=timeout) as client:
                r = await client.post(
                    f'{cfg["base_url"]}/chat/completions',
                    json=payload,
                    headers=headers,
                )
                if r.status_code >= 400:
                    if r.status_code == 429:
                        cfg["pool"].mark_rate_limited(key)
                    raise ProviderHTTPError(provider, r.status_code, None, r.text[:300])
                return r.json()["choices"][0]["message"]["content"]

        provider_used = None
        try:
            result = await BRIDGE.run(
                task_id,
                execute_with_fallback_async(
                    providers_order,
                    call_provider,
                    prompt,
                    session_id=session_id,
                ),
            )
            provider_used = providers_order[0]
        except Exception:
            # Fallback real (HTTP): local -> NVIDIA (4 APIs) -> Groq (6 APIs).
            fallback_result = await provider_fb.call(messages, local_fn=local_execution)
            if fallback_result.get("provider") == "none":
                raise HTTPException(status_code=503, detail="Todos los proveedores fallaron")
            provider_used = fallback_result.get("provider")
            result = _content_of(fallback_result.get("response"))

        # 2. Checkpoint al Harness / banco de memoria (obligatorio: fail-closed).
        try:
            checkpoint = await harness_client.send_checkpoint({
                "model": model_requested,
                "provider_used": provider_used,
                "messages": messages
            })
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"checkpoint al banco de memoria fallo: {e}")
        if isinstance(checkpoint, dict) and checkpoint.get("error"):
            raise HTTPException(status_code=502, detail=f"checkpoint al banco de memoria fallo: {checkpoint['error']}")

        return JSONResponse({"choices": [{"message": {"role": "assistant", "content": result}}]})
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
