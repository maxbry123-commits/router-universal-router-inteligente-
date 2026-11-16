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

    # ids cortos del selector -> ids completos de NVIDIA/Groq (registry 2.0.0)
    MODEL_ALIASES = {
        "minimax-m3.1-flash": "minimaxai/minimax-m3.1-flash",
        "granite-meta": "meta/llama-3.3-70b-instruct",
        "nemotron-super": "nvidia/llama-3.1-nemotron-70b-instruct",
        "nemotron-ultra": "nvidia/llama-3.1-nemotron-ultra-253b-v1",
        "qwen3.8-32b": "qwen/qwen3-32b",
    }

    def _resolve_model(self, model: Optional[str], default: str) -> str:
        if not model:
            return default
        key = model.strip().lower()
        if "/" in model:          # ya es un id completo de NVIDIA/Groq
            return model
        return self.MODEL_ALIASES.get(key, model)

    async def call(self, messages: list, model_requested: str = None, local_fn=None) -> Dict[str, Any]:
        """Local -> Enrutamiento por modelo (NVIDIA o Groq) -> Fallback."""

        # 1. Intentar Local
        if local_fn:
            try:
                return {"provider": "hf_local", "response": await local_fn(messages)}
            except Exception as e:
                logger.warning(f"HF local falló: {e}. Saltando a proveedores externos...")

        # 2. Determinar prioridad basada en el modelo
        provider_priority = []
        if model_requested:
            low = model_requested.lower()
            if "minimax" in low or "meta" in low or "nemotron" in low or "nvidia" in low:
                provider_priority = ["nvidia"]
            elif "qwen" in low or "groq" in low:
                provider_priority = ["groq"]

        # Si no se especificó o no coincide, usar ambos por defecto
        if not provider_priority:
            provider_priority = ["nvidia", "groq"]

        # 3. Intentar NVIDIA
        if "nvidia" in provider_priority:
            for _ in range(len(self.nvidia_keys) or 1):
                key = self._next_key(self.nvidia_keys, "nvidia_idx")
                if not key: break
                try:
                    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
                    # Usamos el modelo pedido o el default
                    nv_model = self._resolve_model(model_requested, "meta/llama-3.3-70b-instruct")
                    payload = {"model": nv_model, "messages": messages}
                    resp = await self.client.post("https://integrate.api.nvidia.com/v1/chat/completions", headers=headers, json=payload)
                    if resp.status_code == 200:
                        return {"provider": "nvidia", "response": resp.json()}
                    logger.warning(f"NVIDIA HTTP {resp.status_code}")
                except Exception as e:
                    logger.warning(f"NVIDIA key falló: {e}")

        # 4. Intentar Groq
        if "groq" in provider_priority:
            for _ in range(len(self.groq_keys) or 1):
                key = self._next_key(self.groq_keys, "groq_idx")
                if not key: break
                try:
                    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
                    # Groq siempre usa qwen3-32b según el registry
                    payload = {"model": "qwen/qwen3-32b", "messages": messages}
                    resp = await self.client.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
                    if resp.status_code == 200:
                        return {"provider": "groq", "response": resp.json()}
                    logger.warning(f"Groq HTTP {resp.status_code}")
                except Exception as e:
                    logger.warning(f"Groq key falló: {e}")

        return {"provider": "none", "error": "Todos los proveedores agotados"}
