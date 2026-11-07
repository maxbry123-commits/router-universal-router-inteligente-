# llm_provider_adapter.py
import os
import re
import httpx
from typing import List, Optional
from key_pool import KeyPool
from quota_budget import QuotaBudget
from bulkhead import get_bulkhead
from schema_validator import validate_llm_output, SchemaValidationError
from event_emitter import EMITTER
from forensic_dlq import ForensicDLQ
from model_format_adapter import ModelFormatAdapter

GROQ_KEYS = [k.strip() for k in os.getenv("GROQ_KEYS", "").split(",") if k.strip()]
NVIDIA_KEYS = [k.strip() for k in os.getenv("NVIDIA_KEYS", "").split(",") if k.strip()]

KEY_POOLS = {
    "groq": KeyPool("groq", GROQ_KEYS),
    "nvidia": KeyPool("nvidia", NVIDIA_KEYS)
}
BUDGETS = {
    "groq": QuotaBudget(rpm=30, tpm=8000),
    "nvidia": QuotaBudget(rpm=40, tpm=100000)
}
DLQ = ForensicDLQ()

GAP_PATTERN = re.compile(r"GAP(?:_DETECTADO)?:\s*(.+)", re.IGNORECASE)

def is_gap_response(text: str) -> bool:
    return bool(GAP_PATTERN.search(text or ""))

async def call_provider_async(provider: str, prompt: str, model_family: str = "qwen2.5") -> str:
    key = KEY_POOLS[provider].get_key()
    if not key:
        raise RuntimeError(f"Todas las keys de {provider} están en cooldown.")
    if not BUDGETS[provider].can_use(key, est_tokens=2000):
        raise RuntimeError(f"Quota local excedida en {provider}.")

    base_url = "https://api.groq.com/openai/v1" if provider == "groq" else "https://integrate.api.nvidia.com/v1"
    model_name = "openai/gpt-oss-120b" if provider == "groq" else "meta/llama-3.3-70b-instruct"
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    payload = {
        "model": model_name,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
        "max_tokens": 4096
    }

    with get_bulkhead(provider):
        try:
            EMITTER.emit("request_start", {"provider": provider})
            async with httpx.AsyncClient(timeout=90) as client:
                r = await client.post(f"{base_url}/chat/completions", json=payload, headers=headers)

                if r.status_code == 429:
                    KEY_POOLS[provider].mark_rate_limited(key)
                    retry_after = r.headers.get("retry-after", "60")
                    raise RuntimeError(f"429 en {provider}, retry-after={retry_after}s")
                if r.status_code in (401, 403):
                    KEY_POOLS[provider].mark_rate_limited(key)
                    raise RuntimeError(f"Key inválida en {provider}: {r.status_code}")

                r.raise_for_status()
                BUDGETS[provider].record(key, est_tokens=2000)
                content = r.json()["choices"][0]["message"]["content"]
                EMITTER.emit("request_success", {"provider": provider})

                tool_calls = ModelFormatAdapter.parse(model_family, content)
                if tool_calls:
                    EMITTER.emit("tool_calls_parsed", {"model": model_family, "count": len(tool_calls)})

                if is_gap_response(content):
                    EMITTER.emit("gap_detected", {"provider": provider, "gap": content[:200]})
                    return content

                try:
                    validated = validate_llm_output(content)
                    return validated.code if validated.code else content
                except SchemaValidationError as e:
                    EMITTER.emit("schema_validation_fail", {"error": str(e)})
                    DLQ.log_failure(provider, f"schema_invalid: {e}", prompt)
                    raise

        except Exception as e:
            EMITTER.emit("request_fail", {"provider": provider, "error": str(e)})
            DLQ.log_failure(provider, str(e), prompt)
            raise

async def generate_code(prompt: str, model_family: str = "qwen2.5") -> str:
    from fallback_middleware import execute_with_fallback_async
    providers = ["groq", "nvidia"]
    return await execute_with_fallback_async(
        providers=providers,
        llm_call_fn=call_provider_async,
        prompt=prompt,
        model_family=model_family,
        payload_for_dlq={"prompt": prompt}
    )
