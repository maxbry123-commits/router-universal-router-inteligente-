from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import httpx
import os
from key_pool import KeyPool
from fallback_middleware import execute_with_fallback_async

app = FastAPI()

GROQ_KEYS = [k.strip() for k in os.getenv("GROQ_KEYS", "").split(",") if k.strip()]
NVIDIA_KEYS = [k.strip() for k in os.getenv("NVIDIA_KEYS", "").split(",") if k.strip()]

PROVIDERS = {
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "pool": KeyPool("groq", GROQ_KEYS),
        "default_model": "openai/gpt-oss-120b"
    },
    "nvidia": {
        "base_url": "https://integrate.api.nvidia.com/v1",
        "pool": KeyPool("nvidia", NVIDIA_KEYS),
        "default_model": "meta/llama-3.3-70b-instruct"
    }
}

@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    body = await request.json()
    model = body.get("model", "groq")
    session_id = request.headers.get("X-Session-Id", "default")
    providers_order = ["groq", "nvidia"] if "groq" in model.lower() else ["nvidia", "groq"]

    async def call_provider(provider: str, prompt: str, model_family: str):
        cfg = PROVIDERS[provider]
        key = cfg["pool"].get_key(session_id=session_id)
        if not key:
            raise RuntimeError(f"Sin keys en {provider}")

        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        payload = {
            "model": body.get("model", cfg["default_model"]),
            "messages": body["messages"],
            "temperature": body.get("temperature", 0.1)
        }

        async with httpx.AsyncClient(timeout=120) as client:
            r = await client.post(f"{cfg['base_url']}/chat/completions", json=payload, headers=headers)
            if r.status_code == 429:
                cfg["pool"].mark_rate_limited(key)
                raise RuntimeError("429")
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]

    try:
        prompt = body["messages"][-1]["content"]
        result = await execute_with_fallback_async(providers_order, call_provider, prompt, session_id=session_id)
        return JSONResponse({
            "id": "chatcmpl-proxy",
            "object": "chat.completion",
            "choices": [{"index": 0, "message": {"role": "assistant", "content": result}}]
        })
    except Exception as e:
        raise HTTPException(502, detail=str(e))

@app.get("/health")
def health():
    return {"status": "ok"}
