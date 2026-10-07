"""Compatibility adapter between ``puente_chat`` and the canonical YAIWES memory.

The chat bridge historically imports ``memory`` and ``scope_for`` from this
module.  The actual memory implementation now lives behind
``memoria_loader._memory``.  Keeping this tiny adapter avoids a second memory
store and makes every bridge feature use the same SQLite-backed facade exposed
at /memoria/*.
"""
from __future__ import annotations

import re
from typing import Any

from .memoria_loader import _memory

_CONTROL = re.compile(r"[\x00-\x1f\x7f]+")


def _clean(value: Any, fallback: str) -> str:
    text = _CONTROL.sub("", str(value or "")).strip()
    return text or fallback


def scope_for(owner: str, scope: str) -> str:
    """Return the deterministic namespace used by the chat bridge.

    ``MemorySave.scope`` is capped at 80 characters, so the legacy two-part
    namespace is normalized and bounded here instead of failing deep inside
    the memory facade.
    """
    owner_part = _clean(owner, "anonymous")
    scope_part = _clean(scope, "general")
    prefix = owner_part + ":"
    if scope_part.startswith(prefix):
        value = scope_part
    else:
        value = prefix + scope_part
    return value[:80]


def memory(store: Any | None = None) -> Any:
    """Return the one canonical ``memoria_yaiwes`` facade.

    ``store`` is intentionally accepted for backwards compatibility with
    ``puente_chat``.  The canonical loader already obtains the same Router
    store through ``get_store()`` and caches the facade per store identity.
    """
    _ = store
    return _memory()
