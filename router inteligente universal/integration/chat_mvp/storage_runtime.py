"""Durable storage lifecycle for the chat Router.

The Router keeps its hot SQLite/database files on the local Job filesystem for
low latency.  This module closes the persistence loop:

    HF bucket -> restore before Store() opens -> local SQLite/docs
    local SQLite/docs -> periodic snapshot -> HF bucket

It is intentionally separate from ``router.py`` so the HTTP surface and the
storage lifecycle remain independently testable.
"""
from __future__ import annotations

import logging
import os
import threading
import time
from pathlib import Path
from typing import Any, Callable

_LOG = logging.getLogger("riu.storage")
_LOCK = threading.Lock()
_AUTOSYNC_THREAD: threading.Thread | None = None


def _settings() -> tuple[str, str, Path]:
    bucket = (os.getenv("HF_BUCKET_ID") or "").strip()
    token = (os.getenv("HF_WRITE_TOKEN") or os.getenv("HF_TOKEN") or "").strip()
    data_dir = Path(os.getenv("RIU_DATA_DIR") or "riu_data")
    return bucket, token, data_dir


def restore_from_bucket(
    data_dir: str | Path,
    bucket_id: str,
    token: str,
    *,
    fs_factory: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    """Restore the latest SQLite snapshot and documents before Store opens.

    Existing non-empty local SQLite is never overwritten.  That makes the
    operation safe if startup hooks are invoked twice in the same process.
    """
    data_dir = Path(data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)
    db_path = data_dir / "riu_chat.sqlite3"
    if db_path.exists() and db_path.stat().st_size > 0:
        return {"status": "LOCAL_PRESENT", "db": str(db_path), "files": 0}
    if not bucket_id or not token:
        return {"status": "SKIPPED_NOT_CONFIGURED", "files": 0}
    if fs_factory is None:
        from huggingface_hub import HfFileSystem as fs_factory  # noqa: N813

    fs = fs_factory(token=token)
    base = f"buckets/{bucket_id}/riu-chat"
    remote_db = f"{base}/riu_chat.sqlite3"
    try:
        raw = fs.cat_file(remote_db)
    except Exception as exc:  # noqa: BLE001 - first boot is allowed to have no snapshot
        return {"status": "NO_REMOTE_SNAPSHOT", "files": 0, "reason": type(exc).__name__}

    tmp = db_path.with_suffix(".restore.tmp")
    tmp.write_bytes(raw)
    os.replace(tmp, db_path)
    files = 1

    docs_dir = data_dir / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    try:
        remote_docs = fs.glob(f"{base}/docs/*")
    except Exception:  # noqa: BLE001
        remote_docs = []
    for remote in remote_docs:
        name = Path(str(remote)).name
        if not name or name in {".", ".."}:
            continue
        try:
            (docs_dir / name).write_bytes(fs.cat_file(str(remote)))
            files += 1
        except Exception as exc:  # noqa: BLE001 - one damaged attachment must not block Router boot
            _LOG.warning("document restore failed %s: %s", name, type(exc).__name__)

    return {"status": "RESTORED", "db": str(db_path), "files": files}


def restore_configured_storage() -> dict[str, Any]:
    bucket, token, data_dir = _settings()
    result = restore_from_bucket(data_dir, bucket, token)
    _LOG.info("storage restore: %s", result.get("status"))
    return result


def start_autosync(
    store: Any,
    sync_fn: Callable[[Any, str, str], dict[str, Any]],
    *,
    interval: int | None = None,
) -> dict[str, Any]:
    """Start one daemon autosync loop when RIU_AUTOSYNC_SECONDS is enabled."""
    global _AUTOSYNC_THREAD
    bucket, token, _data_dir = _settings()
    if interval is None:
        try:
            interval = int(os.getenv("RIU_AUTOSYNC_SECONDS") or "0")
        except ValueError:
            interval = 0
    if interval <= 0:
        return {"status": "DISABLED", "interval": interval}
    if not bucket or not token:
        return {"status": "SKIPPED_NOT_CONFIGURED", "interval": interval}

    with _LOCK:
        if _AUTOSYNC_THREAD and _AUTOSYNC_THREAD.is_alive():
            return {"status": "ALREADY_RUNNING", "interval": interval}

        def loop() -> None:
            while True:
                time.sleep(interval)
                try:
                    result = sync_fn(store, bucket, token)
                    _LOG.info("storage autosync: files=%s", result.get("files"))
                except Exception as exc:  # noqa: BLE001 - persistence failure must not take down chat
                    _LOG.warning("storage autosync failed: %s", type(exc).__name__)

        _AUTOSYNC_THREAD = threading.Thread(target=loop, name="riu-storage-autosync", daemon=True)
        _AUTOSYNC_THREAD.start()
    return {"status": "STARTED", "interval": interval}
