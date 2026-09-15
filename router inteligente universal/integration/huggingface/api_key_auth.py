"""Agent API-key authentication for the existing RIU Hugging Face gateway.

Keys are supplied only through RIU_AGENT_API_KEYS at runtime. The repository
stores no credentials. Format: JSON object mapping key -> agent id.
"""
from __future__ import annotations

import hmac
import json
import os


def _keys() -> dict[str, str]:
    raw = os.getenv("RIU_AGENT_API_KEYS", "")
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError("RIU_AGENT_API_KEYS_INVALID_JSON") from exc
    if not isinstance(parsed, dict):
        raise RuntimeError("RIU_AGENT_API_KEYS_INVALID_FORMAT")
    return {str(key): str(agent) for key, agent in parsed.items()}


def authenticate_api_key(candidate: str | None) -> str:
    """Return agent id for a valid key; otherwise fail closed."""
    if not candidate:
        raise RuntimeError("RIU_API_KEY_REQUIRED")
    for expected, agent_id in _keys().items():
        if hmac.compare_digest(candidate, expected):
            return agent_id
    raise RuntimeError("RIU_API_KEY_INVALID")
