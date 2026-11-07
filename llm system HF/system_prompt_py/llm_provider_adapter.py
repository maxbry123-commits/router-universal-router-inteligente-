# llm_provider_adapter.py
import requests
from typing import List
from key_pool import KeyPool
from quota_budget import QuotaBudget
from bulkhead import get_bulkhead
from schema_validator import validate_llm_output, SchemaValidationError
from fallback_middleware import execute_with_fallback, AllProvidersFailedError
from event_emitter import EMITTER
from forensic_dlq import ForensicDLQ

# Inicialización de Pools (Se llenan desde variables de entorno)
KEY_POOLS = {
    "groq": KeyPool("groq", keys=["gsk_key1", "gsk_key2"]),
    "nvidia": KeyPool("nvidia", keys=["nvapi_key1", "nvapi_key2"])
}
BUDGETS = {
    "groq": QuotaBudget(rpm=30, tpm=8000),
    "nvidia": QuotaBudget(rpm=40, tpm=100000)
}
DLQ = ForensicDLQ()

def call_provider(provider: str, prompt: str) -> str:
    """Lógica interna de llamada a un proveedor específico."""
    key = KEY_POOLS[provider].get_key()
    if not key:
        raise RuntimeError(f"Todas las keys de {provider} están en cooldown.")
        
    if not BUDGETS[provider].can_use(key, est_tokens=2000):
        raise RuntimeError(f"Quota local excedida para la key de {provider}.")
        
    with get_bulkhead(provider): # Control de concurrencia
        base_url = "https://api.groq.com/openai/v1" if provider == "groq" else "https://integrate.api.nvidia.com/v1"
        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        payload = {
            "model": "llama3-70b-8192" if provider == "groq" else "meta/llama3-70b-instruct",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1
        }
        
        try:
            EMITTER.emit("request_start", {"provider": provider})
            resp = requests.post(f"{base_url}/chat/completions", json=payload, headers=headers, timeout=60)
            
            if resp.status_code == 429:
                KEY_POOLS[provider].mark_rate_limited(key)
                raise RuntimeError("429 Rate Limit")
                
            resp.raise_for_status()
            BUDGETS[provider].record(key, est_tokens=2000)
            EMITTER.emit("request_success", {"provider": provider})
            return resp.json()["choices"][0]["message"]["content"]
            
        except Exception as e:
            EMITTER.emit("request_fail", {"provider": provider, "error": str(e)})
            DLQ.log_failure(provider, str(e), prompt)
            raise e

def generate_code(prompt: str) -> str:
    """
    Función principal: Usa el Fallback Middleware para saltar entre Groq y Nvidia,
    y valida que la salida sea un JSON estricto.
    """
    providers = ["groq", "nvidia"]
    
    # Ejecuta con Fallback
    raw_response = execute_with_fallback(
        providers=providers,
        llm_call_fn=call_provider,
        prompt=prompt,
        payload_for_dlq={"prompt": prompt}
    )
    
    # Valida que el LLM devolvió el esquema esperado (JSON válido)
    try:
        validated = validate_llm_output(raw_response)
        return validated.code if validated.code else raw_response
    except SchemaValidationError as e:
        EMITTER.emit("schema_validation_fail", {"error": str(e)})
        raise e
