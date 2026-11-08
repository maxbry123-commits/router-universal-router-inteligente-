import json
import httpx
import os
from fallback_middleware import execute_with_fallback_async

class GenericModelAdapter:
    def __init__(self):
        self.providers = ["groq", "nvidia"]

    async def generate_json(self, prompt: str, schema_hint: str) -> dict:
        async def _call_llm(provider: str, p: str, model_family: str) -> str:
            base_url = "https://api.groq.com/openai/v1" if provider == "groq" else "https://integrate.api.nvidia.com/v1"
            model_name = "openai/gpt-oss-120b" if provider == "groq" else "meta/llama-3.3-70b-instruct"
            key = os.getenv(f"{provider.upper()}_API_KEY", "dummy")

            headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
            payload = {
                "model": model_name,
                "messages": [{"role": "user", "content": p}],
                "temperature": 0.1,
                "response_format": {"type": "json_object"}
            }
            async with httpx.AsyncClient(timeout=60) as client:
                r = await client.post(f"{base_url}/chat/completions", json=payload, headers=headers)
                r.raise_for_status()
                return r.json()["choices"][0]["message"]["content"]

        full_prompt = f"{prompt}\n\nResponde EXCLUSIVAMENTE con JSON válido siguiendo este esquema:\n{schema_hint}"
        raw_json = await execute_with_fallback_async(self.providers, _call_llm, full_prompt)

        stripped = raw_json.strip()
        if stripped.startswith("```"):
            stripped = stripped.split("\n", 1)[-1]
        if stripped.endswith("```"):
            stripped = stripped[:-3]

        return json.loads(stripped)
