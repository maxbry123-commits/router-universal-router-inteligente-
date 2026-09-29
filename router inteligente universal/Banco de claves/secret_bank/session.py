"""Sesión única: login una vez, el banco queda desbloqueado hasta que la sesión caduca."""
from __future__ import annotations

import secrets
import threading
import time
from pathlib import Path
from typing import Callable

from .vault import SessionExpired, UnlockedVault, Vault


class SessionManager:
    def __init__(self, *, ttl_seconds: float = 3600.0, clock: Callable[[], float] = time.time,
                 kdf: dict[str, int] | None = None) -> None:
        self._ttl = ttl_seconds
        self._clock = clock
        self._kdf = kdf
        self._sessions: dict[str, tuple[UnlockedVault, float]] = {}
        self._lock = threading.Lock()

    def login(self, vault_path: str | Path, passphrase: str) -> str:
        """Abre el vault con la contraseña maestra y devuelve un id de sesión aleatorio."""
        unlocked = Vault(vault_path, kdf=self._kdf).unlock(passphrase)
        session_id = secrets.token_urlsafe(32)
        with self._lock:
            self._sessions[session_id] = (unlocked, self._clock() + self._ttl)
        return session_id

    def get(self, session_id: str) -> UnlockedVault:
        with self._lock:
            item = self._sessions.get(session_id)
            if item is None:
                raise SessionExpired("NO_SESSION")
            unlocked, expires = item
            if self._clock() >= expires:
                del self._sessions[session_id]
                raise SessionExpired("SESSION_EXPIRED")
            return unlocked

    def logout(self, session_id: str) -> None:
        with self._lock:
            self._sessions.pop(session_id, None)
