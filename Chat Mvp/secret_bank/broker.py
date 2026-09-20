"""Secret Broker: el Router pide una referencia; el broker usa la clave internamente.

El secreto solo llega a la función `fn` que el llamador interno pasa; el agente recibe el resultado
de `fn`, nunca la clave. Permisos fail-closed: una lista vacía deniega; "*" permite todo.
"""
from __future__ import annotations

import time
from typing import Any, Callable

from .session import SessionManager
from .vault import PermissionDenied


class SecretBroker:
    def __init__(self, sessions: SessionManager, *, clock: Callable[[], float] = time.time) -> None:
        self._sessions = sessions
        self._clock = clock

    @staticmethod
    def _allowed(allow: list[str], value: str) -> bool:
        return "*" in allow or value in allow

    def with_secret(self, session_id: str, credential_ref: str, *, agent: str, model: str, route: str,
                    fn: Callable[[str], Any]) -> Any:
        vault = self._sessions.get(session_id)
        record = vault.get_record(credential_ref)
        for label, allow, value in (
            ("agent", record["allowed_agents"], agent),
            ("model", record["allowed_models"], model),
            ("route", record["allowed_routes"], route),
        ):
            if not self._allowed(allow, value):
                vault.audit("DENIED", credential_ref, agent, f"{label} not allowed; model={model} route={route}")
                raise PermissionDenied(f"{label.upper()}_NOT_ALLOWED")
        try:
            secret = vault.get_secret(credential_ref, now=self._clock())
        except PermissionDenied as exc:
            vault.audit("DENIED", credential_ref, agent, str(exc))
            raise
        vault.audit("USE", credential_ref, agent, f"model={model} route={route}")
        return fn(secret)
