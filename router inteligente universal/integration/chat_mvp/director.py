"""Clave del Director (candado). Director 2026-10-03: ningun agente cambia nada sin su autorizacion.

La clave NUNCA se guarda: solo su huella PBKDF2 en el secreto RIU_DIRECTOR_KEY_HASH = "pbkdf2_sha256$<iter>$<salt hex>$<hash hex>".
Se manda en la cabecera X-Director-Key. 5 intentos fallidos bloquean el candado 15 minutos (todas las IPs).
"""
from __future__ import annotations

import hashlib
import hmac
import os
import threading
import time

HEADER = "x-director-key"
MAX_FAILS = 5
LOCK_S = 15 * 60
_fails: list[float] = []
_lock = threading.Lock()


def make_hash(key: str, iterations: int = 200_000, salt: bytes | None = None) -> str:
    salt = salt or os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", key.encode("utf-8"), salt, iterations)
    return f"pbkdf2_sha256${iterations}${salt.hex()}${digest.hex()}"


def configured() -> bool:
    return os.getenv("RIU_DIRECTOR_KEY_HASH", "").startswith("pbkdf2_sha256$")


def locked() -> bool:
    with _lock:
        now = time.time()
        _fails[:] = [t for t in _fails if now - t < LOCK_S]
        return len(_fails) >= MAX_FAILS


def verify(candidate: str | None) -> bool:
    """True only for the Director key. Fails closed when the hash is not configured."""
    if not candidate or not configured() or locked():
        return False
    try:
        _, iters, salt, expected = os.environ["RIU_DIRECTOR_KEY_HASH"].split("$")
        digest = hashlib.pbkdf2_hmac("sha256", candidate.encode("utf-8"), bytes.fromhex(salt), int(iters)).hex()
    except Exception:  # noqa: BLE001 - malformed hash = locked
        return False
    if hmac.compare_digest(digest, expected):
        return True
    with _lock:
        _fails.append(time.time())
    return False
