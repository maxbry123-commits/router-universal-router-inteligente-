"""provider_fallback.py — Cadena de fallback real (HTTP)."""
import os

# --- C7: último eslabón determinista ---
def deterministic_fallback(prompt: str, artifact_dir: str = "artifacts") -> dict:
    """Devuelve bloque de artefacto si el motor determinista está disponible."""
    try:
        from router_llm_hf.chat_engine import responde
        return responde(prompt, artifact_dir=artifact_dir,
                        artifact_kinds=("md","py","html","json","txt","csv","yaml","yml","sh"))
    except Exception as e:
        return {"error": f"deterministic_unavailable: {e}"}
import httpx
import logging
import asyncio
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

class ProviderFallback:
    def __init__(self):
        # El banco manda: si NVIDIA_KEYS/GROQ_KEYS no vienen del entorno, se hidratan
        # descifrando el sello del repo con HF_VAULT_KEY (fail-open, nunca rompe).
        try:
            from external.core.bank_keys import hydrate as _hydrate_banco
            self.banco = _hydrate_banco()
        except Exception as _e:
            self.banco = {"origen": "import fallido: {}".format(type(_e).__name__)}
        self.nvidia_keys = self._parse_keys(os.getenv("NVIDIA_KEYS", ""))
        self.groq_keys = self._parse_keys(os.getenv("GROQ_KEYS", ""))
        self.nvidia_idx = 0
        self.groq_idx = 0
        # Diagnostico operativo: cuantas claves hay y el ultimo error por proveedor (nunca valores)
        self.diag = {"nvidia_keys": 0, "groq_keys": 0, "nvidia_error": None, "groq_error": None,
                     "banco_origen": (self.banco or {}).get("origen")}
        # 10 conexiones HTTP compartidas
        self.limits = httpx.Limits(max_connections=10, max_keepalive_connections=10)
        # MEDIDO: con 60 s un proveedor muerto se comia el watchdog (96 s) y el chat
        # se quedaba en PENSANDO. 25 s deja pasar a la cadena antes de tiempo.
        # (las llamadas al Space local usan su propio timeout: LOCAL_TIMEOUT_S.)
        self.client = httpx.AsyncClient(limits=self.limits, timeout=25.0)

    def _parse_keys(self, raw: str) -> List[str]:
        return [k.strip() for k in raw.split(",") if k.strip()]

    def _next_key(self, keys: List[str], idx_attr: str) -> Optional[str]:
        if not keys: return None
        idx = getattr(self, idx_attr)
        key = keys[idx % len(keys)]
        setattr(self, idx_attr, (idx + 1) % len(keys))
        return key

    # ids cortos del selector -> ids completos de NVIDIA/Groq (registry 2.0.0)
    # Modelos Groq en produccion (doc de Groq, 2026-11-16): si el id pedido no esta aqui,
    # se usa el de produccion verificado.
    # Modelos que sirve GROQ (api.groq.com/openai/v1). Un modelo, un proveedor.
    # Tope TOTAL por proveedor (segundos) antes de pasar al siguiente
    PROVIDER_DEADLINE_S = 30.0
    GROQ_MODELS = {
        "llama-3.1-8b-instant", "llama-3.3-70b-versatile", "llama-3.1-70b-versatile",
        "openai/gpt-oss-20b", "openai/gpt-oss-120b",
        "google/gemma3-27b-it", "google/gemma-3-27b-it",
        "moonshotai/kimi-k2-instruct", "qwen/qwen3-32b", "qwen/qwen3-32b",
        "deepseek-r1-distill-llama-70b", "qwen/qwen3.8-27b",
    }
    GROQ_DEFAULT = "llama-3.3-70b-versatile"
    # Modelos que sirve NVIDIA (integrate.api.nvidia.com). Un modelo, un proveedor.
    NVIDIA_MODELS = {
        "minimaxai/minimax-m3.1-flash", "minimaxai/minimax-m3.1",
        "nvidia/nemotron-3.5-lightning-30b-a3b", "nvidia/nemotron-3.5-bolt-e4b",
        "nvidia/nemotron-3-ultra-550b-a55b", "nvidia/nemotron-3-super-49b-v1.5",
        "nvidia/llama-3.1-8b-instruct", "nvidia/llama-3.3-70b-instruct",
        "nvidia/gpt-oss-20b", "nvidia/gpt-oss-120b",
        "meta/llama-3.1-8b-instruct", "meta/llama-3.3-70b-instruct",
        "openai/gpt-oss-20b-nvidia", "openai/gpt-oss-120b-nvidia",
    }
    # Prefijos de modelo servidos por NVIDIA NIM
    NVIDIA_PREFIXES = ("meta/", "nvidia/", "google/", "mistralai/", "z-ai/", "deepseek-ai/", "bigcode/", "stepfun-ai/", "poolside/", "snowflake/")

    MODEL_ALIASES = {
        "minimax-m3.1-flash": "minimaxai/minimax-m3.1-flash",
        "granite-meta": "nvidia/nemotron-3.5-lightning-30b-a3b",
        "nemotron-super": "nvidia/nemotron-3.5-lightning-30b-a3b",
        "nemotron-ultra": "nvidia/nemotron-3-ultra-550b-a55b",
        "qwen3.8-32b": "qwen/qwen3.8-27b",
    }

    def _resolve_model(self, model: Optional[str], default: str) -> str:
        if not model:
            return default
        key = model.strip().lower()
        if "/" in model:          # ya es un id completo de NVIDIA/Groq
            return model
        # id corto desconocido: se usa el default del proveedor (no se manda un id invalido)
        return self.MODEL_ALIASES.get(key, default)

    async def call(self, messages: list, model_requested: str = None, local_fn=None,
                   forced_provider: str = None) -> Dict[str, Any]:
        """Local -> enrutado por modelo (NVIDIA o Groq) -> error real si ese proveedor falla.

        ORDEN DEL OWNER: un modelo NUNCA cambia de API. Si el modelo es de Groq se
        llama solo a Groq; si es de NVIDIA, solo a NVIDIA. Si ese proveedor se agota
        se devuelve su error real (nunca un OK de otro proveedor).
        forced_provider: /v1/nvidia -> "nvidia", /v1/groq -> "groq" (ruta explicita).
        Tambien se puede fijar como atributo: provider_fb.forced_provider = "groq".
        """
        forced_provider = forced_provider or getattr(self, "forced_provider", None)
        # Conteo de claves refrescado en cada llamada (fuente de verdad: el entorno actual)
        self.diag["nvidia_keys"] = len(self.nvidia_keys)
        self.diag["groq_keys"] = len(self.groq_keys)

        # 1. Intentar Local
        if local_fn:
            try:
                return {"provider": "hf_local", "response": await local_fn(messages)}
            except Exception as e:
                logger.warning(f"HF local falló: {e}. Saltando a proveedores externos...")

        # 2. Determinar el proveedor segun el modelo (UN modelo -> UN proveedor)
        provider_priority = []
        if forced_provider in ("nvidia", "groq"):
            provider_priority = [forced_provider]
        elif model_requested:
            low = model_requested.lower()
            if model_requested in self.GROQ_MODELS:
                provider_priority = ["groq"]
            elif model_requested in self.NVIDIA_MODELS:
                provider_priority = ["nvidia"]
            elif "qwen" in low or "groq" in low:
                provider_priority = ["groq"]
            elif "llama" in low and "/" not in low:
                provider_priority = ["groq"]
            elif low.startswith(self.NVIDIA_PREFIXES):
                provider_priority = ["nvidia"]
            elif "minimax" in low or "nemotron" in low or "nvidia" in low:
                provider_priority = ["nvidia"]

        # Si no se especifico o no coincide: ambos, en ese orden
        if not provider_priority:
            provider_priority = ["nvidia", "groq"]
        order = list(provider_priority)
        # SIN rescate automatico: si el modelo fijaba proveedor, no se cambia de API.
        # (solo 'auto' usa los dos, en ese orden)

        # 3. Cadena real en el ORDEN de prioridad (NVIDIA/Groq): se respeta el proveedor del modelo.
        # DEADLINE POR PROVEEDOR: con 5-6 claves y 25 s cada una, un proveedor caido
        # se comia el watchdog entero (96 s). Ahora el proveedor tiene un tope total.
        import time as _t
        deadline = _t.time() + self.PROVIDER_DEADLINE_S
        for prov in order:
            if prov == "nvidia":
                for _ in range(len(self.nvidia_keys) or 1):
                    if _t.time() > deadline:
                        self.diag["nvidia_error"] = "deadline de proveedor agotado (%ss)" % self.PROVIDER_DEADLINE_S
                        break
                    key = self._next_key(self.nvidia_keys, "nvidia_idx")
                    if not key:
                        self.diag["nvidia_error"] = "sin claves en NVIDIA_KEYS"
                        break
                    try:
                        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
                        # si el modelo pedido es de NVIDIA se manda EXACTO; si no, el default
                        nv_model = (model_requested if model_requested in self.NVIDIA_MODELS
                                    else self._resolve_model(model_requested, "nvidia/nemotron-3.5-lightning-30b-a3b"))
                        payload = {"model": nv_model, "messages": messages}
                        resp = await self.client.post("https://integrate.api.nvidia.com/v1/chat/completions", headers=headers, json=payload)
                        if resp.status_code == 200:
                            return {"provider": "nvidia", "response": resp.json(), "degraded": "nvidia" in order[1:]}
                        logger.warning(f"NVIDIA HTTP {resp.status_code}")
                        self.diag["nvidia_error"] = f"HTTP {resp.status_code}"
                    except Exception as e:
                        logger.warning(f"NVIDIA key fallo: {e}")
                        self.diag["nvidia_error"] = f"{type(e).__name__}: {e}"[:200]
            elif prov == "groq":
                for _ in range(len(self.groq_keys) or 1):
                    if _t.time() > deadline:
                        self.diag["groq_error"] = "deadline de proveedor agotado (%ss)" % self.PROVIDER_DEADLINE_S
                        break
                    key = self._next_key(self.groq_keys, "groq_idx")
                    if not key:
                        self.diag["groq_error"] = "sin claves en GROQ_KEYS"
                        break
                    try:
                        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
                        gq_model = model_requested if model_requested in self.GROQ_MODELS else self.GROQ_DEFAULT
                        payload = {"model": gq_model, "messages": messages}
                        resp = await self.client.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
                        if resp.status_code == 200:
                            return {"provider": "groq", "response": resp.json(), "degraded": "groq" in order[1:]}
                        logger.warning(f"Groq HTTP {resp.status_code}")
                        self.diag["groq_error"] = f"HTTP {resp.status_code}"
                    except Exception as e:
                        logger.warning(f"Groq key fallo: {e}")
                        self.diag["groq_error"] = f"{type(e).__name__}: {e}"[:200]

        if len(order) == 1:
            return {"provider": "none",
                    "error": "Proveedor {} agotado para el modelo pedido (sin cambiar de API)".format(order[0]),
                    "diag": dict(self.diag)}
        return {"provider": "none", "error": "Todos los proveedores agotados", "diag": dict(self.diag)}
