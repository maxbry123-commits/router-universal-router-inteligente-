import asyncio
from typing import List, Callable
from provider_window import WINDOW, WINDOW_S, ProviderHTTPError, ProviderRateLimited, NoBalanceError, is_no_balance
from event_emitter import EMITTER

class AllProvidersFailedError(Exception):
    pass

async def execute_with_fallback_async(
    providers: List[str],
    llm_call_fn: Callable,
    prompt: str,
    model_family: str = "qwen2.5",
    payload_for_dlq: dict = None,
    session_id: str = "default",
    window=None,
    retry_budget_s: float = WINDOW_S,
) -> str:
    win = window or WINDOW
    no_balance = []
    last_error = None
    for provider in providers:
        budget = {"left": retry_budget_s, "attempt": 0}
        while True:
            await win.acquire(provider)
            try:
                return await llm_call_fn(provider, prompt, model_family)
            except ProviderHTTPError as e:
                if e.status == 429:
                    if await win.backoff(e.retry_after, budget):
                        continue
                    raise ProviderRateLimited(f"{provider}: 429 persistente dentro de la ventana; no se cambia de proveedor")
                if is_no_balance(e):
                    no_balance.append(provider)
                    EMITTER.emit("no_balance", {"provider": provider, "status": e.status})
                last_error = str(e)
                break
            except asyncio.TimeoutError:
                last_error = f"Timeout en {provider}"
                break
            except ProviderRateLimited:
                raise
            except Exception as e:
                last_error = str(e)
                break

    if no_balance and len(no_balance) == len(providers):
        raise NoBalanceError(f"SIN SALDO en: {', '.join(no_balance)}")
    raise AllProvidersFailedError(f"Todos los proveedores fallaron. Último error: {last_error}")
