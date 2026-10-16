"""hf_storage: puente list/read/write/backup_sqlite al almacenamiento permanente REAL de HF.

El Storage Bucket vigente es el mismo que usa storage_lifecycle/sync_to_bucket:
COMAND-CENTER-1/yaiwes-memoria-storage (prefijo riu-chat/), accedido via HfFileSystem
con rutas "buckets/<id>/riu-chat/..." — mismo backend, sin crear otro.

No guarda nada en el Router. Token solo por variable de entorno HF_TOKEN.
"""
from __future__ import annotations

import base64
import os
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
            data = base64.b64decode(str(payload["content_b64"])) if "content_b64" in payload else str(payload.get("content", "")).encode("utf-8")
            fs.pipe_file(_full(p), data)
            return {"status": "ok", "bucket": bucket, "path": p, "bytes": len(data)}
        if action == "backup_sqlite":  # copia la base SQLite de memoria al mismo bucket permanente
            src = str(payload.get("db_path") or "")
            if not src or not os.path.isfile(src):
                return {"status": "error", "error": "db_path no existe"}
            dest = _path(payload.get("dest") or "riu_chat.sqlite3")
            with open(src, "rb") as fh:
                data = fh.read()
            fs.pipe_file(_full(dest), data)
            return {"status": "ok", "bucket": bucket, "path": dest, "bytes": len(data)}
        return {"status": "error", "error": "accion no permitida", "allowed": list(ACTIONS)}
    except Exception as exc:  # el plugin nunca tumba al host
        return {"status": "error", "error": str(exc)[:300]}
