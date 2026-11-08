# openai_compatible_proxy.py
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
import httpx, os, time, json
from key_pool import KeyPool
from quota_budget import QuotaBudget
from fallback_middleware import execute_with_fallback
from model_format_adapter import ModelFormatAdapter

app = FastAPI(title="Advanced LLM Proxy")

GROQ_KEYS = [k.strip() for k in os.getenv("GROQ_KEYS", "").split(",") if k.strip()]
NVIDIA_KEYS = [k.strip() for k in os.getenv("NVIDIA_KEYS", "").split(",") if k.strip()]

PROVIDERS = {
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "pool": KeyPool("groq", GROQ_KEYS),
        "budget": QuotaBudget(rpm=30, tpm=8000),
        "default_model": "openai/gpt-oss-120b"
    },
    "nvidia": {
        "base_url": "https://integrate.api.nvidia.com/v1",
        "pool": KeyPool("nvidia", NVIDIA_KEYS),
        "budget": QuotaBudget(rpm=40, tpm=100000),
        "default_model": "meta/llama-3.3-70b-instruct"
    }
}

# keep_alive eliminado (DAG hf-emergency-cleanup): el ping periodico a /health
# mantenia los Spaces de modelo encendidos sin carga real. El escalado real lo
# hace swe-code-s*/scaler.py, que mide la CPU del contenedor.

async def stream_with_heartbeat(upstream_client, url, headers, payload, heartbeat_s=15.0):
    async with upstream_client.stream("POST", url, json=payload, headers=headers) as response:
        response.raise_for_status()
        last_yield = time.time()
        async for chunk in response.aiter_text():
            if chunk:
                yield chunk
                last_yield = time.time()
            if time.time() - last_yield > heartbeat_s:
                yield 'data: {"choices":[{"delta":{"content":""}}]}\n\n'
                last_yield = time.time()

@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    body = await request.json()
    model = body.get("model", "groq")
    is_stream = body.get("stream", False)
    session_id = request.headers.get("X-Session-Id", "default")

    providers_order = ["groq", "nvidia"] if "groq" in model.lower() else ["nvidia", "groq"]

    async def call_provider(provider: str, prompt: str):
        cfg = PROVIDERS[provider]
        key = cfg["pool"].get_key(session_id=session_id)
        
        if not key:
            raise RuntimeError(f"Sin keys disponibles en {provider}")
        if not cfg["budget"].can_use(key, est_tokens=2000):
            raise RuntimeError(f"Quota excedida en {provider}")

        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        payload = {
            "model": body.get("model", cfg["default_model"]),
            "messages": body["messages"],
            "temperature": body.get("temperature", 0.1),
            "max_tokens": body.get("max_tokens", 4096),
            "stream": is_stream
        }

        if is_stream:
            return stream_with_heartbeat(
                httpx.AsyncClient(timeout=120),
                f"{cfg['base_url']}/chat/completions",
                headers, payload
            )
        else:
            async with httpx.AsyncClient(timeout=120) as client:
                r = await client.post(f"{cfg['base_url']}/chat/completions", json=payload, headers=headers)
                if r.status_code == 429:
                    cfg["pool"].mark_rate_limited(key)
                    raise RuntimeError("429 Rate Limit")
                r.raise_for_status()
                cfg["budget"].record(key, est_tokens=2000)
                
                result = r.json()
                content = result["choices"][0]["message"].get("content", "")
                parsed_tools = ModelFormatAdapter.parse(payload["model"], content)
                if parsed_tools:
                    result["choices"][0]["message"]["tool_calls"] = parsed_tools
                return result

    if is_stream:
        for provider in providers_order:
            try:
                gen = await call_provider(provider, body["messages"][-1]["content"])
                return StreamingResponse(gen, media_type="text/event-stream")
            except Exception:
                continue
        raise HTTPException(502, "Todos los proveedores fallaron en streaming")
    else:
        try:
            return await execute_with_fallback(providers_order, call_provider, body["messages"][-1]["content"])
        except Exception as e:
            raise HTTPException(502, detail=str(e))

@app.get("/health")
async def health():
    return {"status": "ok", "providers": list(PROVIDERS.keys())}
