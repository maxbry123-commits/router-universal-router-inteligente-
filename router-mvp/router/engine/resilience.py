"""Deterministic resilience primitives for Router Inteligente Universal.

C10 owns retry/backoff and per-node circuit-breaker state only. It does not
own routing, connectors, Enchufe validation, or orchestration.

Contract sources:
- DOC-A02_ARCHITECTURE.md C10
- resumen ROUTER_INTELIGENTE_UNIVERSAL_v6.md §6
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Awaitable, Callable, TypeVar


T = TypeVar("T")


class EstadoBreaker(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitBreaker:
    """Per-node CLOSED -> OPEN -> HALF_OPEN circuit breaker."""

    umbral_fallos: int = 5
    ventana_s: float = 60.0
    enfriamiento_s: float = 30.0
    estado: EstadoBreaker = EstadoBreaker.CLOSED
    fallos_recientes: list[float] = field(default_factory=list)
    abierto_desde: float = 0.0

    def __post_init__(self) -> None:
        if self.umbral_fallos < 1:
            raise ValueError("umbral_fallos must be >= 1")
        if self.ventana_s <= 0 or self.enfriamiento_s < 0:
            raise ValueError("ventana_s must be > 0 and enfriamiento_s >= 0")

    def registrar_fallo(self, ahora: float | None = None) -> None:
        ahora = time.monotonic() if ahora is None else ahora
        self.fallos_recientes = [
            instante
            for instante in self.fallos_recientes
            if ahora - instante < self.ventana_s
        ]
        self.fallos_recientes.append(ahora)
        if len(self.fallos_recientes) >= self.umbral_fallos:
            self.estado = EstadoBreaker.OPEN
            self.abierto_desde = ahora

    def puede_intentar(self, ahora: float | None = None) -> bool:
        ahora = time.monotonic() if ahora is None else ahora
        if self.estado == EstadoBreaker.CLOSED:
            return True
        if (
            self.estado == EstadoBreaker.OPEN
            and ahora - self.abierto_desde >= self.enfriamiento_s
        ):
            self.estado = EstadoBreaker.HALF_OPEN
            return True
        return self.estado == EstadoBreaker.HALF_OPEN

    def registrar_exito(self) -> None:
        self.estado = EstadoBreaker.CLOSED
        self.fallos_recientes = []
        self.abierto_desde = 0.0


@dataclass(frozen=True)
class RetryPolicy:
    """R5 exponential backoff policy; defaults are fixed by architecture v6."""

    intentos: int = 3
    base_ms: int = 500

    def __post_init__(self) -> None:
        if self.intentos < 1:
            raise ValueError("intentos must be >= 1")
        if self.base_ms < 0:
            raise ValueError("base_ms must be >= 0")

    def demora_s(self, numero_fallo: int) -> float:
        """Delay after failure 1..N: base * 2**(failure-1)."""
        if numero_fallo < 1:
            raise ValueError("numero_fallo must be >= 1")
        return (self.base_ms / 1000.0) * (2 ** (numero_fallo - 1))


async def ejecutar_con_resiliencia(
    operacion: Callable[[], Awaitable[T]],
    *,
    breaker: CircuitBreaker,
    retry: RetryPolicy | None = None,
    dormir: Callable[[float], Awaitable[None]] = asyncio.sleep,
) -> T:
    """Run one already-authorized connector operation behind R5/R6.

    This function intentionally receives a zero-argument operation instead of
    resolving a connector itself. Connector ownership remains in RedUniversal /
    Enchufe Universal; C10 only decides retry/circuit state.
    """

    policy = retry or RetryPolicy()
    if not breaker.puede_intentar():
        raise RuntimeError("CIRCUIT_OPEN")

    ultimo_error: BaseException | None = None
    for intento in range(1, policy.intentos + 1):
        try:
            resultado = await operacion()
        except Exception as exc:
            ultimo_error = exc
            breaker.registrar_fallo()
            if breaker.estado == EstadoBreaker.OPEN:
                break
            if intento < policy.intentos:
                await dormir(policy.demora_s(intento))
        else:
            breaker.registrar_exito()
            return resultado

    assert ultimo_error is not None
    raise ultimo_error
