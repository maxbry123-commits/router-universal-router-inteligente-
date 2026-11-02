"""hf_storage: puente list/read/write/backup_sqlite al almacenamiento permanente REAL de HF.

El Storage Bucket vigente es el mismo que usa storage_lifecycle/sync_to_bucket:
COMAND-CENTER-1/yaiwes-memoria-storage (prefijo riu-chat/), accedido via HfFileSystem
con rutas "buckets/<id>/riu-chat/..." — mismo backend, sin crear otro.

No guarda nada en el Router. Token solo por variable de entorno HF_TOKEN.
"""
from __future__ import annotations

import base64
import os
import time
import re
from typing import Any

DEFAULT_BUCKET = "COMAND-CENTER-1/yaiwes-memoria-storage"
PREFIX = "riu-chat"  # mismo prefijo que usa storage_lifecycle
MAX_READ = 2_000_000
ACTIONS = ("status", "list", "read", "write", "backup_sqlite")
_BUCKET_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*/[A-Za-z0-9][A-Za-z0-9._-]*$")


def _bucket() -> str:
    b = (os.getenv("HF_BUCKET_ID") or os.getenv("HF_STORAGE_BUCKET") or DEFAULT_BUCKET).strip()
    if not _BUCKET_RE.match(b):
        raise ValueError("bucket invalido")
    return b


def _fs():
    token = os.getenv("HF_TOKEN", "").strip()
    if not token:
        raise ValueError("HF_TOKEN ausente")
    from huggingface_hub import HfFileSystem
    return HfFileSystem(token=token, skip_instance_cache=True)


def _path(value: Any, allow_empty: bool = False) -> str:
    p = str(value or "").strip().lstrip("/")
    if (not p and not allow_empty) or "\\" in p or ".." in p.split("/"):
        raise ValueError("path invalido")
    return p


_RESERVADO = ("riu_chat.sqlite3", "docs/", "docs")  # snapshot de storage_lifecycle (restauracion en frio): solo lo escribe el autosync


def _reservado(p: str) -> bool:
    return p in _RESERVADO or p.startswith("docs/")


def _full(p: str) -> str:
    return f"buckets/{_bucket()}/{PREFIX}/{p}"


def handle(action: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    try:
        bucket = _bucket()
        if action == "status":
            return {"status": "ok", "bucket": bucket, "prefix": PREFIX, "repo_type": "bucket",
                    "token_present": bool(os.getenv("HF_TOKEN")), "actions": list(ACTIONS)}
        fs = _fs()
        if action == "list":
            p = _path(payload.get("path"), True)
            base = _full(p)
            try:
                entries = fs.ls(base, detail=True) if p else fs.ls(base, detail=True)
            except FileNotFoundError:
                return {"status": "ok", "bucket": bucket, "path": p, "entries": []}
            out = []
            for e in entries:
                name = str(e.get("name") or e.get("path") or "").rsplit("/", 1)[-1]
                out.append({"path": str(e.get("name") or e.get("path") or "").split(PREFIX + "/", 1)[-1],
                            "name": name, "type": e.get("type"), "size": e.get("size")})
            return {"status": "ok", "bucket": bucket, "path": p, "entries": out}
        if action == "read":
            p = _path(payload.get("path"))
            data = fs.cat_file(_full(p))
            if len(data) > MAX_READ:
                return {"status": "error", "error": "archivo supera %d bytes" % MAX_READ}
            try:
                return {"status": "ok", "bucket": bucket, "path": p, "encoding": "utf-8", "content": data.decode("utf-8")}
            except UnicodeDecodeError:
                return {"status": "ok", "bucket": bucket, "path": p, "encoding": "base64", "content": base64.b64encode(data).decode()}
        if action == "write":
            p = _path(payload.get("path"))
            if _reservado(p):
                return {"status": "error", "error": "ruta reservada al autosync (riu_chat.sqlite3, docs/)"}
            data = base64.b64decode(str(payload["content_b64"])) if "content_b64" in payload else str(payload.get("content", "")).encode("utf-8")
            fs.pipe_file(_full(p), data)
            return {"status": "ok", "bucket": bucket, "path": p, "bytes": len(data)}
        if action == "backup_sqlite":  # copia la base SQLite de memoria al mismo bucket permanente
            src = str(payload.get("db_path") or "")
            if not src or not os.path.isfile(src):
                return {"status": "error", "error": "db_path no existe"}
            dest = _path(payload.get("dest") or time.strftime("backups/riu_chat-%Y%m%dT%H%M%S.sqlite3", time.gmtime()))
            if _reservado(dest):
                return {"status": "error", "error": "ruta reservada al autosync (riu_chat.sqlite3, docs/)"}
            import sqlite3
            import tempfile
            with tempfile.TemporaryDirectory() as tmp:  # copia consistente con la API de backup (no bytes crudos de una base viva)
                dst = os.path.join(tmp, "b.sqlite3")
                con, out = sqlite3.connect(src), sqlite3.connect(dst)
                try:
                    con.backup(out)
                finally:
                    out.close()
                    con.close()
                with open(dst, "rb") as fh:
                    data = fh.read()
            fs.pipe_file(_full(dest), data)
            return {"status": "ok", "bucket": bucket, "path": dest, "bytes": len(data)}
        return {"status": "error", "error": "accion no permitida", "allowed": list(ACTIONS)}
    except Exception as exc:  # el plugin nunca tumba al host
        return {"status": "error", "error": str(exc)[:300]}

# YAIWES LOOP: checkpoint of the existing CIT-50 and Watchdog SQLite stores.
# Reuses this plugin's SAME HF Bucket; never stores WAL files on bucket/FUSE.
# Intended for the existing plugin's _store() adapter, not a new storage API.
def sqlite_checkpoint(db_path, store_name: str) -> dict:
    import hashlib
    import sqlite3
    import tempfile
    from pathlib import Path
    if store_name not in ("cola50", "watchdog48"):
        raise ValueError("store_name no autorizado")
    src = Path(db_path)
    if not src.is_file():
        raise RuntimeError("SQLite de origen inexistente")
    with tempfile.TemporaryDirectory() as temp:
        dst = Path(temp) / "snapshot.sqlite3"
        with sqlite3.connect(str(src)) as source, sqlite3.connect(str(dst)) as target:
            source.backup(target)  # consistent copy including live WAL state
        data = dst.read_bytes()
    if not 0 < len(data) <= 20_000_000:
        raise RuntimeError("snapshot SQLite fuera de limites")
    digest = hashlib.sha256(data).hexdigest()
    uri = _full("tasks/system/" + store_name + ".sqlite3")
    fs = _fs()  # Existing HF_TOKEN (not passed in a contract or logged).
    fs.pipe_file(uri, data)
    if hashlib.sha256(fs.cat_file(uri)).hexdigest() != digest:
        raise RuntimeError("HF_STORAGE_READBACK_MISMATCH")
    return {"ok": True, "sha256": digest, "bytes": len(data), "store_name": store_name}


def sqlite_restore_if_missing(db_path, store_name: str) -> dict:
    import hashlib
    import sqlite3
    import tempfile
    from pathlib import Path
    if store_name not in ("cola50", "watchdog48"):
        raise ValueError("store_name no autorizado")
    path = Path(db_path)
    if path.exists():
        return {"ok": True, "status": "PRESENT_LOCAL"}
    fs = _fs()  # Never fall back silently to a fresh empty DB on a network/auth error.
    try:
        data = fs.cat_file(_full("tasks/system/" + store_name + ".sqlite3"))
    except FileNotFoundError:
        return {"ok": True, "status": "FIRST_BOOT_NO_SNAPSHOT"}
    if not 0 < len(data) <= 20_000_000:
        raise RuntimeError("HF_STORAGE_SNAPSHOT_INVALID_SIZE")
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(prefix=".restore-", suffix=".sqlite3",
                                     dir=str(path.parent), delete=False) as tmp:
        temp_path = Path(tmp.name)
        tmp.write(data)
    try:
        with sqlite3.connect(str(temp_path)) as connection:
            if connection.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise RuntimeError("HF_STORAGE_SQLITE_INTEGRITY_FAILED")
        # No concurrent SQLite process can start before this call returns.
        temp_path.replace(path)
    finally:
        temp_path.unlink(missing_ok=True)
    return {"ok": True, "status": "RESTORED", "sha256": hashlib.sha256(data).hexdigest()}
