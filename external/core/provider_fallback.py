"""provider_fallback.py — Cadena de fallback real (HTTP)."""
import os
import httpx
import logging
import asyncio
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

class ProviderFallback:
    def __init__(self):
        self.nvidia_keys = self._parse_keys(os.getenv("NVIDIA_KEYS", ""))
        self.groq_keys = self._parse_keys(os.getenv("GROQ_KEYS", ""))
        self.nvidia_idx = 0
        self.groq_idx = 0
        # 10 conexiones HTTP compartidas
        self.limits = httpx.Limits(max_connections=10, max_keepalive_connections=10)
        self.client = httpx.AsyncClient(limits=self.limits, timeout=60.0)

    def _parse_keys(self, raw: str) -> List[str]:
        return [k.strip() for k in raw.split(",") if k.strip()]

    def _next_key(self, keys: List[str], idx_attr: str) -> Optional[str]:
        if not keys: return None
        idx = getattr(self, idx_attr)
        key = keys[idx % len(keys)]
        setattr(self, idx_attr, (idx + 1) % len(keys))
        return key

    async def call(self, messages: list, local_fn=None) -> Dict[str, Any]:
        """Intenta local -> NVIDIA (4 APIs) -> Groq (6 APIs) con HTTP real."""
        
        # 1. Local
        if local_fn:
            try:
                return {"provider": "hf_local", "response": await local_fn(messages)}
            except Exception as e:
                logger.warning(f"HF local falló: {e}. Saltando a NVIDIA...")

        # 2. NVIDIA
        for _ in range(len(self.nvidia_keys) or 1):
            key = self._next_key(self.nvidia_keys, "nvidia_idx")
            if not key: break
            try:
                headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
                payload = {"model": "meta/llama-3.3-70b-instruct", "messages": messages}
                resp = await self.client.post("https://integrate.api.nvidia.com/v1/chat/completions", headers=headers, json=payload)
                if resp.status_code == 200:
                    return {"provider": "nvidia", "response": resp.json()}
            except Exception as e:
                logger.warning(f"NVIDIA key falló: {e}")

        # 3. Groq
        for _ in range(len(self.groq_keys) or 1):
            key = self._next_key(self.groq_keys, "groq_idx")
            if not key: break
            try:
                headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
                payload = {"model": "qwen/qwen3-32b", "messages": messages}
                resp = await self.client.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
                if resp.status_code == 200:
                    return {"provider": "groq", "response": resp.json()}
            except Exception as e:
                logger.warning(f"Groq key falló: {e}")

        return {"provider": "none", "error": "Todos los proveedores agotados"}
