"""HF bridge: snapshot/restore of the SQLite memory to a private HF dataset (no router edits).
Token only from env HF_TOKEN. Dataset: RIU_HF_MEMORY_DATASET (default COMAND-CENTER-1/yaiwes-hf-memoria)."""
from __future__ import annotations

import hashlib
import os
import shutil
import sqlite3
import tempfile
from pathlib import Path
from typing import Any

REPO = os.environ.get("RIU_HF_MEMORY_DATASET", "COMAND-CENTER-1/yaiwes-hf-memoria")
REMOTE = "snapshots/memoria.sqlite"


def _api() -> Any:
    from huggingface_hub import HfApi

    return HfApi(token=os.environ.get("HF_TOKEN"))


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def health() -> dict[str, Any]:
    try:
        info = _api().dataset_info(REPO)
        return {"status": "OK", "repo": REPO, "private": bool(info.private)}
    except Exception as exc:  # noqa: BLE001
        return {"status": "GAP", "repo": REPO, "reason": type(exc).__name__}


def snapshot(db_path: str | Path) -> dict[str, Any]:
    db = Path(db_path)
    if not db.exists():
        return {"status": "GAP", "reason": "db_missing"}
    with tempfile.TemporaryDirectory() as tmp:
        copy = Path(tmp) / "memoria.sqlite"
        src, dst = sqlite3.connect(db), sqlite3.connect(copy)
        try:
            src.backup(dst)
        finally:
            dst.close()
            src.close()
        _api().upload_file(path_or_fileobj=str(copy), path_in_repo=REMOTE, repo_id=REPO, repo_type="dataset", commit_message="memoria snapshot")
        return {"status": "SNAPSHOT_OK", "repo": REPO, "remote": REMOTE, "sha256": _sha(copy), "bytes": copy.stat().st_size}


def _has_rows(db: Path) -> bool:
    if not db.exists() or db.stat().st_size == 0:
        return False
    con = sqlite3.connect(db)
    try:
        tables = [r[0] for r in con.execute("select name from sqlite_master where type='table'")]
        return any(con.execute(f'select 1 from "{t}" limit 1').fetchone() for t in tables)
    finally:
        con.close()


def restore_if_empty(db_path: str | Path) -> dict[str, Any]:
    db = Path(db_path)
    if _has_rows(db):
        return {"status": "SKIPPED_NOT_EMPTY"}
    from huggingface_hub import hf_hub_download

    got = hf_hub_download(repo_id=REPO, repo_type="dataset", filename=REMOTE, token=os.environ.get("HF_TOKEN"))
    db.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(got, db)
    return {"status": "RESTORED", "sha256": _sha(db), "bytes": db.stat().st_size}
