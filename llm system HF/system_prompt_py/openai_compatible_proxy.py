# openai_compatible_proxy.py
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import httpx
import os
import time
from key_pool import KeyPool
from quota_budget import QuotaBudget
from fallback_middleware import execute_with_fallback
from key_health_scorer import KeyHealthScorer
from event_emitter import EMITTER

app = FastAPI(title="OpenAI-Compatible LLM Proxy (10 Keys)")

# 1. Cargar keys desde variables de entorno (separadas por comas)
GROQ_KEYS = os.getenv("GROQ_KEYS", "").split(",")
NVIDIA_KEYS = os.getenv("NVIDIA_KEYS", "").split(",")

# Limpiar strings vacíos si los hay
GROQ_KEYS = [k.strip() for k in GROQ_KEYS if k.strip()]
NVIDIA_KEYS = [k.strip() for k in NVIDIA_KEYS if k.strip()]

print(f"✅ Cargadas {len(GROQ_KEYS)} keys de Groq y {len(NVIDIA_KEYS)} keys de NVIDIA.")

# 2. Inicializar Pools y Budgets
PROVIDERS = {
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "model": "openai/gpt-oss-120b",
        "pool": KeyPool("groq", GROQ_KEYS),
        "budget": QuotaBudget(rpm=30, tpm=8000)
    },
    "nvidia": {
        "base_url": "https://integrate.api.nvidia.com/v1",
        "model": "meta/llama-3.3-70b-instruct",
        "pool": KeyPool("nvidia", NVIDIA_KEYS),
        "budget": QuotaBudget(rpm=40, tpm=100000)
    }
}

# 3. Inicializar el Health Scorer
def simple_health_check(key: str) -> bool:
    # Petición mínima para verificar si la key es válida
    try:
        headers = {"Authorization": f"Bearer {key}"}
        # Usamos un modelo barato o solo verificamos la respuesta HTTP
        r = httpx.get("https://api.groq.com/openai/v1/models", headers=headers, timeout=5)
        return r.status_code == 200
    except:
        return False

scorer = KeyHealthScorer(health_check_fn=simple_health_check)
scorer.register_keys(GROQ_KEYS + NVIDIA_KEYS)

@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    body = await request.json()
    prompt = body["messages"][-1]["content"]
    model = body.get("model", "groq")

    providers_order = ["groq", "nvidia"] if model == "groq" else ["nvidia", "groq"]

    def call_provider(provider: str, prompt: str) -> str:
        cfg = PROVIDERS[provider]
        
        # Obtener key del pool
        key = cfg["pool"].get_key()
        if not key:
            raise RuntimeError(f"Todas las keys de {provider} están en cooldown.")
        
        # Verificar que el health scorer la considere sana
        if key not in scorer.get_healthy_keys():
            cfg["pool"].mark_rate_limited(key)
            raise RuntimeError(f"Key de {provider} marcada como no saludable.")

        # Verificar presupuesto local
        if not cfg["budget"].can_use(key, est_tokens=2000):
            raise RuntimeError(f"Quota local excedida en {provider}")

        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        payload = {
            "model": cfg["model"],
            "messages": [{"role": "user", "content": prompt}],
            "temperature": body.get("temperature", 0.1),
            "max_tokens": body.get("max_tokens", 4096)
        }

        with httpx.Client(timeout=120) as client:
            r = client.post(f"{cfg['base_url']}/chat/completions", json=payload, headers=headers)

            if r.status_code == 429:
                cfg["pool"].mark_rate_limited(key)
                scorer.mark_failure(key, "429")
                retry_after = r.headers.get("retry-after", "60")
                EMITTER.emit("rate_limit", {"provider": provider, "wait": retry_after})
                raise RuntimeError(f"429 en {provider}, retry-after={retry_after}s")
                
            if r.status_code in (401, 403):
                scorer.mark_failure(key, str(r.status_code))
                raise RuntimeError(f"Key inválida en {provider}: {r.status_code}")

            r.raise_for_status()
            cfg["budget"].record(key, est_tokens=2000)
            return r.json()["choices"][0]["message"]["content"]

    try:
        content = execute_with_fallback(providers_order, call_provider, prompt)
    except Exception as e:
        raise HTTPException(502, detail=str(e))

    return JSONResponse({
        "id": f"chatcmpl-{int(time.time())}",
        "object": "chat.completion",
        "model": model,
        "choices": [{"index": 0, "message": {"role": "assistant", "content": content}}]
    })
