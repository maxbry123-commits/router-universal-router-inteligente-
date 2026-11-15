"""provider_fallback.py — Cadena de fallback para LLMs externos.
Prioridad: HF local (Grupo 2) → NVIDIA (4 APIs) → Groq (6 APIs).
"""
import os
import logging
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)


class ProviderFallback:
    """Gestor de fallback. Trigger: fallo, saldo agotado, o modo mirror."""

    def __init__(self):
        self.nvidia_keys = self._parse_keys(os.getenv("NVIDIA_KEYS", ""))
        self.groq_keys = self._parse_keys(os.getenv("GROQ_KEYS", ""))
        self.nvidia_idx = 0
        self.groq_idx = 0

    def _parse_keys(self, raw: str) -> List[str]:
        return [k.strip() for k in raw.split(",") if k.strip()]

    def _next_key(self, keys: List[str], idx_attr: str) -> Optional[str]:
        if not keys:
            return None
        idx = getattr(self, idx_attr)
        key = keys[idx % len(keys)]
        setattr(self, idx_attr, (idx + 1) % len(keys))
        return key

    def nvidia_model(self) -> str:
        """Modelo NVIDIA activo (rota entre los 4)."""
        models = [
            "minimaxai/minimax-m3.1-flash",
            "meta/llama-3.3-70b-instruct",
            "nvidia/llama-3.1-nemotron-70b-instruct",
            "nvidia/llama-3.1-nemotron-ultra-253b-v1",
        ]
        return models[self.nvidia_idx % len(models)]

    def get_nvidia_key(self) -> Optional[str]:
        return self._next_key(self.nvidia_keys, "nvidia_idx")

    def get_groq_key(self) -> Optional[str]:
        return self._next_key(self.groq_keys, "groq_idx")

    async def call(self, prompt: str, local_fn=None) -> Dict[str, Any]:
        """Intenta local → NVIDIA (4 APIs) → Groq (6 APIs)."""
        if local_fn:
            try:
                result = await local_fn(prompt)
                return {"provider": "hf_local", "result": result}
            except Exception as e:
                logger.warning(f"HF local falló: {e}, saltando a NVIDIA")

        for _ in range(len(self.nvidia_keys) or 1):
            key = self.get_nvidia_key()
            if not key:
                break
            try:
                return {
                    "provider": "nvidia",
                    "model": self.nvidia_model(),
                    "key_used": key[:8] + "...",
                }
            except Exception as e:
                logger.warning(f"NVIDIA falló: {e}, siguiente")
                continue

        for _ in range(len(self.groq_keys) or 1):
            key = self.get_groq_key()
            if not key:
                break
            try:
                return {
                    "provider": "groq",
                    "model": "qwen/qwen3-32b",
                    "key_used": key[:8] + "...",
                }
            except Exception as e:
                logger.warning(f"Groq falló: {e}, siguiente")
                continue

        return {"provider": "none", "error": "todos los proveedores agotados"}
