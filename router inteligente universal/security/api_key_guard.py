"""Bearer guard for the Router Inteligente Universal gateway."""
from __future__ import annotations
from dataclasses import dataclass

from api_key_manager import APIKeyManager


@dataclass(frozen=True)
class AuthResult:
    ok: bool
    status_code: int
    detail: str
    principal: dict | None = None


def authorize_bearer(
    authorization: str | None,
    manager: APIKeyManager,
    *,
    scope: str = "route",
    model_id: str | None = None,
) -> AuthResult:
    if not authorization or not authorization.startswith("Bearer "):
        return AuthResult(False, 401, "missing_bearer")
    plaintext = authorization[7:].strip()
    if not plaintext:
        return AuthResult(False, 401, "missing_bearer")
    principal = manager.verify(plaintext, scope=scope, model_id=model_id)
    if principal is None:
        return AuthResult(False, 403, "invalid_key_or_scope")
    return AuthResult(True, 200, "ok", principal)
