"""hf_storage: puente list/read/write al almacenamiento permanente de HF (repo dataset).

No guarda nada en el Router. Token solo por variable de entorno HF_TOKEN.
GPT no dejo codigo de puente (T-08 sigue PENDIENTE, solo documento), por eso es nuevo.
"""
from __future__ import annotations

import base64
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

HF = "https://huggingface.co"
DEFAULT_REPO = "COMAND-CENTER-1/yaiwes-hf-memoria"
MAX_READ = 2_000_000
ACTIONS = ("status", "list", "read", "write", "backup_sqlite")
_REPO_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*/[A-Za-z0-9][A-Za-z0-9._-]*$")


def _http(method, url, headers=None, data=None, timeout=30):
    """HTTP minimo (stdlib). Devuelve (status, bytes). Los tests lo reemplazan por un mock."""
    req = urllib.request.Request(url, data=data, method=method, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()
    except Exception as e:  # red caida, DNS, timeout
        return 0, str(e).encode()


def _json(body):
    try:
        return json.loads(body.decode("utf-8", "replace"))
    except ValueError:
        return None


def _repo() -> str:
    repo = os.getenv("HF_STORAGE_REPO", DEFAULT_REPO).strip()
    if not _REPO_RE.match(repo):
        raise ValueError("HF_STORAGE_REPO invalido")
    return repo


def _auth() -> dict[str, str]:
    token = os.getenv("HF_TOKEN", "").strip()
    return {"Authorization": "Bearer " + token} if token else {}


def _path(value: Any, allow_empty: bool = False) -> str:
    p = str(value or "").strip().lstrip("/")
    if (not p and not allow_empty) or "\\" in p or ".." in p.split("/"):
        raise ValueError("path invalido")
    return p


def _commit(repo: str, path: str, data: bytes, summary: str) -> dict[str, Any]:
    if not _auth():
        return {"status": "error", "error": "HF_TOKEN ausente"}
    head = {"key": "header", "value": {"summary": summary[:200]}}
    fil = {"key": "file", "value": {"content": base64.b64encode(data).decode(), "path": path, "encoding": "base64"}}
    body = (json.dumps(head) + "\n" + json.dumps(fil) + "\n").encode()
    url = f"{HF}/api/datasets/{repo}/commit/main"
    st, raw = _http("POST", url, {**_auth(), "Content-Type": "application/x-ndjson"}, body, 60)
    if st >= 400 or st == 0:
        return {"status": "error", "http_status": st, "error": raw[:300].decode("utf-8", "replace")}
    return {"status": "ok", "repo": repo, "path": path, "bytes": len(data)}


def handle(action: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    try:
        repo = _repo()
        if action == "status":
            return {"status": "ok", "repo": repo, "repo_type": "dataset", "token_present": bool(_auth()), "actions": list(ACTIONS)}
        if action == "list":
            p = _path(payload.get("path"), True)
            url = f"{HF}/api/datasets/{repo}/tree/main" + ("/" + urllib.parse.quote(p) if p else "")
            st, raw = _http("GET", url, _auth())
            data = _json(raw)
            if st != 200 or not isinstance(data, list):
                return {"status": "error", "http_status": st, "error": raw[:300].decode("utf-8", "replace")}
            return {"status": "ok", "repo": repo, "entries": [{"path": e.get("path"), "type": e.get("type"), "size": e.get("size")} for e in data]}
        if action == "read":
            p = _path(payload.get("path"))
            st, raw = _http("GET", f"{HF}/datasets/{repo}/resolve/main/{urllib.parse.quote(p)}", _auth(), None, 60)
            if st != 200:
                return {"status": "error", "http_status": st, "error": raw[:300].decode("utf-8", "replace")}
            if len(raw) > MAX_READ:
                return {"status": "error", "error": "archivo supera %d bytes" % MAX_READ}
            try:
                return {"status": "ok", "path": p, "encoding": "utf-8", "content": raw.decode("utf-8")}
            except UnicodeDecodeError:
                return {"status": "ok", "path": p, "encoding": "base64", "content": base64.b64encode(raw).decode()}
        if action == "write":
            p = _path(payload.get("path"))
            if "content_b64" in payload:
                data = base64.b64decode(str(payload["content_b64"]))
            else:
                data = str(payload.get("content", "")).encode("utf-8")
            return _commit(repo, p, data, str(payload.get("summary") or "hf_storage write " + p))
        if action == "backup_sqlite":  # T-08: copia la base SQLite de memoria al dataset privado
            src = str(payload.get("db_path") or "")
            if not src or not os.path.isfile(src):
                return {"status": "error", "error": "db_path no existe"}
            dest = _path(payload.get("dest") or "sqlite/memoria_yaiwes.db")
            with open(src, "rb") as fh:
                data = fh.read()
            return _commit(repo, dest, data, "backup sqlite memoria")
        return {"status": "error", "error": "accion no permitida", "allowed": list(ACTIONS)}
    except Exception as exc:  # el plugin nunca tumba al host
        return {"status": "error", "error": str(exc)[:300]}
