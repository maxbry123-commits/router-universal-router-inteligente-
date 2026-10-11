"""STORAGE_LIFECYCLE: restore al arrancar + autosync periodico, sobre el Store y el bucket HF existentes.
Solo stdlib. No crea otro almacenamiento. Nunca pisa una base local que ya tenga datos."""
from __future__ import annotations

import os
import sqlite3
import threading
from pathlib import Path
from typing import Any, Callable

STATUS: dict[str, Any] = {"restore": "NOT_RUN", "autosync": "OFF", "last_sync": None, "last_error": None}


def restore_if_empty(data_dir: Any, bucket: str | None, token: str | None, fs_factory: Callable[..., Any] | None = None) -> dict[str, Any]:
    d = Path(data_dir)
    db = d / "riu_chat.sqlite3"
    if db.exists() and db.stat().st_size > 0:
        STATUS["restore"] = "SKIPPED_LOCAL_EXISTS"
        return {"status": STATUS["restore"]}
    if not bucket or not token:
        STATUS["restore"] = "SKIPPED_NOT_CONFIGURED"
        return {"status": STATUS["restore"]}
    try:
        if fs_factory is None:
            from huggingface_hub import HfFileSystem as fs_factory  # noqa: N813
        fs = fs_factory(token=token)
        base = f"buckets/{bucket}/riu-chat"
        data = fs.cat_file(f"{base}/riu_chat.sqlite3")
    except Exception as exc:  # noqa: BLE001
        STATUS["restore"] = f"NO_REMOTE_SNAPSHOT:{type(exc).__name__}"
        return {"status": STATUS["restore"]}
    d.mkdir(parents=True, exist_ok=True)
    tmp = d / "riu_chat.sqlite3.restore"
    tmp.write_bytes(data)
    try:
        con = sqlite3.connect(tmp)
        ok = con.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        con.close()
    except Exception:  # noqa: BLE001
        ok = False
    if not ok:
        tmp.unlink(missing_ok=True)
        STATUS["restore"] = "REMOTE_SNAPSHOT_CORRUPT"
        return {"status": STATUS["restore"]}
    os.replace(tmp, db)
    docs = 0
    (d / "docs").mkdir(exist_ok=True)
    try:
        for p in fs.ls(f"{base}/docs", detail=False):
            name = str(p).rsplit("/", 1)[-1]
            if name and not (d / "docs" / name).exists():
                (d / "docs" / name).write_bytes(fs.cat_file(p if str(p).startswith("buckets/") else f"{base}/docs/{name}"))
                docs += 1
    except Exception:  # noqa: BLE001 - los documentos son best-effort; la base ya esta
        pass
    STATUS["restore"] = "RESTORED"
    return {"status": "RESTORED", "docs": docs}


_thread: threading.Thread | None = None


def start_autosync(get_store: Callable[[], Any], sync_fn: Callable[..., Any], bucket: str | None, token: str | None, interval: float | None = None) -> dict[str, Any]:
    global _thread
    secs = float(os.getenv("RIU_AUTOSYNC_SECONDS", "300")) if interval is None else interval
    if not bucket or not token or secs <= 0:
        STATUS["autosync"] = "OFF_NOT_CONFIGURED"
        return {"status": STATUS["autosync"]}
    if _thread is not None and _thread.is_alive():
        return {"status": "ALREADY_RUNNING"}
    stop = threading.Event()

    def loop() -> None:
        import time
        while not stop.wait(secs):
            try:
                sync_fn(get_store(), bucket, token)
                STATUS["last_sync"] = time.time()
                STATUS["last_error"] = None
            except Exception as exc:  # noqa: BLE001
                STATUS["last_error"] = type(exc).__name__

    _thread = threading.Thread(target=loop, daemon=True, name="riu-autosync")
    _thread.start()
    STATUS["autosync"] = "RUNNING"
    return {"status": "RUNNING", "every_s": secs, "stop": stop}
