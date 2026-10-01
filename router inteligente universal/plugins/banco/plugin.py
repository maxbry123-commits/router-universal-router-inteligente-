"""Plugin banco: banco cifrado AES-GCM aislado. Respaldo; el Router no depende de el.
MASTER solo desde env RIU_BANK_MASTER. get_keys devuelve secretos SOLO con internal=True
(llamada Python interna del Router); por la ruta HTTP /plugins/banco/call/get_keys se deniega."""
from __future__ import annotations
import os
from pathlib import Path
from .vault import Vault, VaultError

BANK = Path(os.environ.get("RIU_BANK_PATH") or Path(__file__).parent / "bank" / "bank.vault")


def _open():
    m = os.environ.get("RIU_BANK_MASTER")
    if not m:
        raise VaultError("MASTER_MISSING")
    return Vault(BANK).unlock(m)


def _counts(v) -> dict:
    c: dict = {}
    for r in v.list():
        p = r["credential_ref"].split("/", 1)[0]
        c[p] = c.get(p, 0) + 1
    return c


def get_keys(provider: str) -> list:
    """Uso interno del Router (import directo). Devuelve [(ref, secreto)]."""
    v = _open()
    refs = [r["credential_ref"] for r in v.list() if r["credential_ref"].split("/", 1)[0] == provider]
    return [(ref, v.get_secret(ref)) for ref in sorted(refs)]


def handle(action: str, payload: dict | None = None, *, internal: bool = False) -> dict:
    payload = payload or {}
    try:
        if action == "status":
            if not BANK.exists():
                return {"ok": False, "error": "BANK_MISSING"}
            if not os.environ.get("RIU_BANK_MASTER"):
                return {"ok": True, "locked": True, "reason": "MASTER_MISSING"}
            return {"ok": True, "locked": False, "credentials": sum(_counts(_open()).values())}
        if action == "providers":
            return {"ok": True, "providers": _counts(_open())}
        if action == "get_keys":
            if not internal:
                return {"ok": False, "error": "INTERNAL_ONLY"}
            return {"ok": True, "keys": get_keys(str(payload.get("provider", "")))}
        return {"ok": False, "error": "UNKNOWN_ACTION"}
    except VaultError as e:
        return {"ok": False, "error": str(e)}
