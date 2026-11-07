# fallback_middleware.py
import asyncio
from typing import List, Callable
from api_limiter import wait_for_slot
from event_emitter import EMITTER
from forensic_dlq import ForensicDLQ

DLQ = ForensicDLQ()

class AllProvidersFailedError(Exception):
    pass

async def execute_with_fallback_async(
    providers: List[str],
    llm_call_fn: Callable,
    prompt: str,
    model_family: str = "qwen2.5",
    payload_for_dlq: dict = None
) -> str:
    last_error = None

    for provider in providers:
        EMITTER.emit("fallback_try", {"provider": provider})

        if not wait_for_slot(provider, est_tokens=2000):
            last_error = f"Rate limit local excedido en {provider}"
            EMITTER.emit("fallback_skip", {"provider": provider, "reason": last_error})
            continue

        try:
            result = await llm_call_fn(provider, prompt, model_family)
            EMITTER.emit("fallback_success", {"provider": provider})
            return result
        except asyncio.TimeoutError as e:
            last_error = f"Timeout en {provider}"
            EMITTER.emit("fallback_timeout", {"provider": provider})
        except Exception as e:
            last_error = str(e)
            EMITTER.emit("fallback_fail", {"provider": provider, "error": last_error})
            if payload_for_dlq:
                DLQ.log_failure(provider, last_error, prompt)

    raise AllProvidersFailedError(
        f"Todos los proveedores fallaron. Último error: {last_error}"
    )
