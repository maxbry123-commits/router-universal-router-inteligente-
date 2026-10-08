"""Runtime safety wrapper for puente_chat.

Keeps special pipeline fichas selectable, but prevents them from becoming the
first reserve candidates when the normal API-model sentinel resumes a task.
The legacy plugin builds reserve candidates from FICHAS insertion order, so
placing real API fichas first makes the existing fallback path deterministic
without removing consil/motor/xray/auditor from the catalog.
"""
from __future__ import annotations

from typing import Any

from . import plugin as _p
from . import plugin_long_context as _long


def _order_api_fallbacks_first() -> None:
    normal = {k: v for k, v in _p.FICHAS.items() if k not in _p.ESPECIALES}
    special = {k: v for k, v in _p.FICHAS.items() if k in _p.ESPECIALES}
    _p.FICHAS.clear()
    _p.FICHAS.update(normal)
    _p.FICHAS.update(special)


_order_api_fallbacks_first()


def handle(action: str, payload: dict[str, Any]) -> dict[str, Any]:
    result = _long.handle(action, payload)
    if action == "status" and isinstance(result, dict):
        result = dict(result)
        result["runtime_safety"] = {
            "enabled": True,
            "api_fallbacks_before_pipeline": True,
            "special_fichas_preserved": True,
        }
    return result
