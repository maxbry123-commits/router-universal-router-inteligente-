import asyncio
import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "engine" / "resilience.py"
spec = importlib.util.spec_from_file_location("riu_resilience", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)

CircuitBreaker = module.CircuitBreaker
EstadoBreaker = module.EstadoBreaker
RetryPolicy = module.RetryPolicy
ejecutar_con_resiliencia = module.ejecutar_con_resiliencia


def test_breaker_closed_open_half_open_closed():
    breaker = CircuitBreaker(umbral_fallos=2, ventana_s=60, enfriamiento_s=30)
    assert breaker.puede_intentar(0) is True
    breaker.registrar_fallo(1)
    assert breaker.estado == EstadoBreaker.CLOSED
    breaker.registrar_fallo(2)
    assert breaker.estado == EstadoBreaker.OPEN
    assert breaker.puede_intentar(31) is False
    assert breaker.puede_intentar(32) is True
    assert breaker.estado == EstadoBreaker.HALF_OPEN
    breaker.registrar_exito()
    assert breaker.estado == EstadoBreaker.CLOSED
    assert breaker.fallos_recientes == []


def test_breaker_discards_failures_outside_window():
    breaker = CircuitBreaker(umbral_fallos=2, ventana_s=10, enfriamiento_s=30)
    breaker.registrar_fallo(1)
    breaker.registrar_fallo(12)
    assert breaker.estado == EstadoBreaker.CLOSED
    assert breaker.fallos_recientes == [12]


def test_retry_backoff_and_success_without_connector_ownership():
    attempts = 0
    delays = []

    async def operation():
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise ValueError("transient")
        return {"status": "DONE"}

    async def fake_sleep(delay):
        delays.append(delay)

    result = asyncio.run(
        ejecutar_con_resiliencia(
            operation,
            breaker=CircuitBreaker(),
            retry=RetryPolicy(intentos=3, base_ms=500),
            dormir=fake_sleep,
        )
    )
    assert result == {"status": "DONE"}
    assert attempts == 3
    assert delays == [0.5, 1.0]


def test_open_breaker_fails_closed_without_calling_operation():
    called = False
    breaker = CircuitBreaker(umbral_fallos=1, enfriamiento_s=30)
    breaker.registrar_fallo(100)

    async def operation():
        nonlocal called
        called = True
        return "unexpected"

    # Force deterministic timestamp check by keeping OPEN and a large monotonic origin.
    breaker.abierto_desde = 10**20
    try:
        asyncio.run(ejecutar_con_resiliencia(operation, breaker=breaker))
    except RuntimeError as exc:
        assert str(exc) == "CIRCUIT_OPEN"
    else:
        raise AssertionError("OPEN circuit must fail closed")
    assert called is False


def test_invalid_policy_rejected():
    try:
        RetryPolicy(intentos=0)
    except ValueError:
        pass
    else:
        raise AssertionError("invalid retry policy accepted")
