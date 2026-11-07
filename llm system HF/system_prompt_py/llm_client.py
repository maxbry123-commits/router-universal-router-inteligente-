# llm_client.py
import requests
from recovery_engine import call_with_recovery
from api_limiter import wait_for_slot

class LLMClient:
    def __init__(self, provider: str, api_key: str):
        self.provider = provider
        self.api_key = api_key
        self.base_url = "https://api.groq.com/openai/v1" if provider == "groq" else "https://integrate.api.nvidia.com/v1"

    def generate(self, prompt: str, timeout: int = 60) -> str:
        # 1. Esperar cupo en el limitador (evita el 429)
        if not wait_for_slot(self.provider, estimated_tokens=2000):
            raise RuntimeError(f"Rate limit excedido en {self.provider}")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "llama3-70b-8192" if self.provider == "groq" else "meta/llama3-70b-instruct",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1
        }

        # 2. Envolver la llamada en el motor de recuperación
        def _do_request():
            resp = requests.post(f"{self.base_url}/chat/completions", json=payload, headers=headers, timeout=timeout)
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]

        return call_with_recovery(self.provider, _do_request, payload={"prompt": prompt})
