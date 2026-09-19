"""Verify agent API keys against the certified hash-only keystore (MAXBRY-001..100).

Reuses APIKeyManager's PBKDF2 digest. The plaintext key embeds its agent id
(`riu_<agent_id>_<token>`), so only the record(s) whose agent id prefixes the key
are hashed: one PBKDF2 per request instead of scanning all 100 slots.
"""
from __future__ import annotations

import hmac
import json
import os
import sys
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parents[2]
_SECURITY = _ROOT / "security"
if str(_SECURITY) not in sys.path:
    sys.path.insert(0, str(_SECURITY))

from api_key_manager import APIKeyManager  # noqa: E402

KEYSTORE_ENV = "RIU_KEYSTORE_PATH"
DEFAULT_KEYSTORE = _SECURITY / "keystore" / "maxbry_100_api_keys_hash_state.json"


def load_records(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        data = next((v for v in data.values() if isinstance(v, list) and v and isinstance(v[0], dict) and "key_hash" in v[0]), [])
    return [r for r in data if isinstance(r, dict) and "key_hash" in r and "salt" in r]


def verify_keystore_key(candidate: str | None, *, scope: str = "route", path: str | Path | None = None) -> str | None:
    """Return the agent id for an active key that has `scope`; otherwise None (fail closed)."""
    if not candidate or not candidate.startswith("riu_"):
        return None
    keystore = Path(path or os.getenv(KEYSTORE_ENV) or DEFAULT_KEYSTORE)
    if not keystore.is_file():
        return None
    for rec in load_records(keystore):
        if rec.get("status", "active") != "active":
            continue
        safe = "".join(c for c in str(rec.get("agent_id", "")) if c.isalnum() or c in "-_")[:48]
        if not safe or not candidate.startswith(f"riu_{safe}_"):
            continue
        if not hmac.compare_digest(APIKeyManager._digest(candidate, rec["salt"]), rec["key_hash"]):
            continue
        if scope not in rec.get("scopes", ["route"]):
            return None
        return str(rec["agent_id"])
    return None
