"""Hooks so providers can read keys from the unlocked Secret Bank without importing it (no import cycles)."""
from __future__ import annotations

from typing import Callable

_provider_keys: Callable[[str], list[str]] = lambda provider: []


def set_provider_keys(fn: Callable[[str], list[str]]) -> None:
    global _provider_keys
    _provider_keys = fn

_SELLO = None


def _banco_unico(provider: str) -> list[str]:
    """Banco unico: plugins/fichas_qwen/sellos/proveedores.sello, abierto con FICHA_CLAVE_BANCO."""
    global _SELLO
    if _SELLO is None:
        import hashlib, json, os
        from pathlib import Path
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        clave = os.environ.get("FICHA_CLAVE_BANCO") or ""
        f = Path(__file__).resolve().parents[2] / "plugins" / "fichas_qwen" / "sellos" / "proveedores.sello"
        if not clave or not f.exists():
            return []
        b = f.read_bytes(); cab = b"FICHA-SELLO-1"; k = len(cab)
        ll = hashlib.scrypt(clave.encode(), salt=b[k:k + 16], n=2 ** 15, r=8, p=1, dklen=32, maxmem=2 ** 26)
        _SELLO = json.loads(AESGCM(ll).decrypt(b[k + 16:k + 28], b[k + 28:], cab).decode("utf-8"))
    return [str(x) for x in (_SELLO.get(provider) or []) if x]


def _secretos_chat(provider: str) -> list[str]:
    """Claves guardadas desde la ventana Secretos del chat con ese proveedor (plugin secretos). Nunca rompe el pool."""
    try:
        from plugins.secretos.plugin import por_proveedor
        return list(por_proveedor(provider))
    except Exception:  # noqa: BLE001
        return []


def provider_keys(provider: str) -> list[str]:
    try:
        base = [*_banco_unico(provider), *list(_provider_keys(provider))]
    except Exception:  # noqa: BLE001 - a locked or broken bank must never break the chat
        base = []
    return base + _secretos_chat(provider)
