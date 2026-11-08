import asyncio
from typing import List, Callable
from api_limiter import wait_for_slot
from provider_budget import BUDGET

class AllProvidersFailedError(Exception):
    pass

async def execute_with_fallback_async(
    providers: List[str],
    llm_call_fn: Callable,
    prompt: str,
    model_family: str = "qwen2.5",
    payload_for_dlq: dict = None,
    session_id: str = "default"
) -> str:
    last_error = None
    for provider in providers:
        if not await BUDGET.can_use(provider, session_id):
            continue
        if not wait_for_slot(provider, est_tokens=2000):
            continue
        try:
            result = await llm_call_fn(provider, prompt, model_family)
            await BUDGET.record(provider, session_id)
            return result
        except asyncio.TimeoutError:
            last_error = f"Timeout en {provider}"
        except Exception as e:
            last_error = str(e)

    raise AllProvidersFailedError(f"Todos los proveedores fallaron. Último error: {last_error}")
