"""Motor de pruebas API/SDK del laboratorio.

No contiene ni persiste secretos. Las credenciales se obtienen únicamente del
banco secreto ya abierto en memoria por el Router y nunca se incluyen en la salida.
"""
from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

MODEL_CANDIDATES = (
    "gpt-5-mini",
    "gpt-5-nano",
    "gpt-4.1-mini",
    "gpt-4o-mini",
    "gpt-4.1",
)


def _keys() -> list[str]:
    from integration.chat_mvp import vault_hook
    return list(vault_hook.provider_keys("openai"))


def _safe_error(exc: BaseException) -> dict[str, Any]:
    out: dict[str, Any] = {"ok": False, "error_type": type(exc).__name__}
    for name in ("status_code", "code", "type"):
        value = getattr(exc, name, None)
        if isinstance(value, (str, int)):
            out[name] = value
    return out


def _probe_one(index: int, key: str) -> dict[str, Any]:
    from openai import OpenAI

    client = OpenAI(api_key=key, timeout=12.0, max_retries=0)
    row: dict[str, Any] = {"key_index": index}

    started = time.perf_counter()
    try:
        client.get("/me", cast_to=dict)
        row["me"] = {"ok": True, "status_code": 200, "ms": int((time.perf_counter() - started) * 1000)}
    except Exception as exc:  # noqa: BLE001
        row["me"] = _safe_error(exc)
        row["me"]["ms"] = int((time.perf_counter() - started) * 1000)

    started = time.perf_counter()
    model_ids: set[str] = set()
    try:
        page = client.models.list()
        model_ids = {str(item.id) for item in page.data if getattr(item, "id", None)}
        row["models"] = {
            "ok": True,
            "status_code": 200,
            "model_count": len(model_ids),
            "ms": int((time.perf_counter() - started) * 1000),
        }
    except Exception as exc:  # noqa: BLE001
        row["models"] = _safe_error(exc)
        row["models"]["ms"] = int((time.perf_counter() - started) * 1000)

    model = next((m for m in MODEL_CANDIDATES if m in model_ids), None)
    if model is None:
        row["responses"] = {"ok": False, "error_type": "NO_SUPPORTED_TEST_MODEL"}
        return row

    started = time.perf_counter()
    try:
        response = client.responses.create(
            model=model,
            input="Reply exactly with SDK_OK",
            max_output_tokens=16,
        )
        row["responses"] = {
            "ok": bool(getattr(response, "id", None)),
            "status_code": 200,
            "model": model,
            "response_id_present": bool(getattr(response, "id", None)),
            "ms": int((time.perf_counter() - started) * 1000),
        }
    except Exception as exc:  # noqa: BLE001
        row["responses"] = _safe_error(exc)
        row["responses"]["model"] = model
        row["responses"]["ms"] = int((time.perf_counter() - started) * 1000)

    return row


def status() -> dict[str, Any]:
    try:
        import openai
        sdk = str(getattr(openai, "__version__", "unknown"))
    except Exception:  # noqa: BLE001
        sdk = None
    keys = _keys()
    return {
        "status": "ok" if keys and sdk else "degraded",
        "openai_keys_available": len(keys),
        "openai_sdk_version": sdk,
        "secrets_returned": False,
    }


def run_all() -> dict[str, Any]:
    try:
        import openai
        sdk_version = str(getattr(openai, "__version__", "unknown"))
    except Exception as exc:  # noqa: BLE001
        return {"status": "blocked", "reason": "OPENAI_SDK_NOT_AVAILABLE", "error_type": type(exc).__name__}

    keys = _keys()
    if not keys:
        return {"status": "blocked", "reason": "VAULT_LOCKED_OR_NO_OPENAI_KEYS", "checks_total": 0, "checks_pass": 0}

    started = time.perf_counter()
    rows: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=min(14, len(keys))) as pool:
        futures = {pool.submit(_probe_one, i, key): i for i, key in enumerate(keys, 1)}
        for future in as_completed(futures):
            i = futures[future]
            try:
                rows.append(future.result())
            except Exception as exc:  # noqa: BLE001
                rows.append({
                    "key_index": i,
                    "me": {"ok": False, "error_type": "WORKER_FAILED"},
                    "models": {"ok": False, "error_type": type(exc).__name__},
                    "responses": {"ok": False, "error_type": "WORKER_FAILED"},
                })

    rows.sort(key=lambda r: r["key_index"])
    checks_total = len(rows) * 3
    checks_pass = sum(
        1
        for row in rows
        for name in ("me", "models", "responses")
        if bool(row.get(name, {}).get("ok"))
    )
    return {
        "status": "ok" if checks_pass == checks_total else "partial",
        "sdk_version": sdk_version,
        "keys_found": len(keys),
        "checks_total": checks_total,
        "checks_pass": checks_pass,
        "checks_fail": checks_total - checks_pass,
        "elapsed_ms": int((time.perf_counter() - started) * 1000),
        "rows": rows,
        "secrets_returned": False,
    }
