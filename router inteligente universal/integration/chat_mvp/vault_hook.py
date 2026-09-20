"""Hooks so providers can read keys from the unlocked Secret Bank without importing it (no import cycles)."""
from __future__ import annotations

from typing import Callable

_provider_keys: Callable[[str], list[str]] = lambda provider: []


def set_provider_keys(fn: Callable[[str], list[str]]) -> None:
    global _provider_keys
    _provider_keys = fn


def provider_keys(provider: str) -> list[str]:
    try:
        return list(_provider_keys(provider))
    except Exception:  # noqa: BLE001 - a locked or broken bank must never break the chat
        return []
