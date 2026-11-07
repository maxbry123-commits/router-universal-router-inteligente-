# fallback_middleware.py
import time
from typing import List, Callable
from api_limiter import wait_for_slot
from recovery_engine import call_with_recovery, DeadLetterQueue, CircuitOpenError
from schema_validator import validate_llm_output, SchemaValidationError

DLQ = DeadLetterQueue()

class AllProvidersFailedError(Exception):
    """Se lanza cuando todos los proveedores de la cadena fallan."""
    pass

def execute_with_fallback(
    providers: List[str],
    llm_call_fn: Callable[[str], str],
    prompt: str,
    payload_for_dlq: dict = None
) -> str:
    """
    Ejecuta la llamada al LLM probando en orden los proveedores.
    Si el proveedor A falla (API, Rate Limit o JSON roto), pasa al proveedor B.
    """
    last_error = None

    for provider in providers:
        print(f"🔄 Intentando con proveedor: {provider}")
        
        # 1. Esperar cupo en el Rate Limiter
        if not wait_for_slot(provider, est_tokens=2000):
            last_error = f"Rate limit excedido en {provider}"
            print(f"⚠️ {last_error}. Saltando al siguiente...")
            continue

        try:
            # 2. Llamar al LLM con el motor de recuperación (Circuit Breaker + Retries)
            raw_output = call_with_recovery(
                provider=provider,
                fn=lambda: llm_call_fn(provider, prompt),
                max_retries=3,
                payload=payload_for_dlq
            )
            
            # 3. Validar que el JSON sea estricto
            validated_output = validate_llm_output(raw_output)
            print(f"✅ Éxito con {provider}. Status: {validated_output.status}")
            return raw_output # Retornamos el string original, ya validado

        except (SchemaValidationError, CircuitOpenError, Exception) as e:
            last_error = str(e)
            print(f"❌ Fallo en {provider}: {last_error}")
            
            # Registrar el fallo en la Dead Letter Queue
            if payload_for_dlq:
                DLQ.push(provider, last_error, payload_for_dlq)
            
            # Saltar al siguiente proveedor
            continue

    # Si el bucle termina, todos fallaron
    raise AllProvidersFailedError(f"Todos los proveedores fallaron. Último error: {last_error}")
