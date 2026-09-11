"""Fail-closed verifier for Router destination responses."""
from __future__ import annotations


def verify_response(result: dict) -> dict:
    ok = (
        isinstance(result, dict)
        and result.get("status") == "DONE"
        and bool(result.get("via"))
        and result.get("output") is not None
    )
    return {
        "verified": ok,
        "status": "PASS" if ok else "FAIL",
        "via": result.get("via") if isinstance(result, dict) else None,
    }
