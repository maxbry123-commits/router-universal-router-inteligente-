"""hf_datasets: lectura por llamada de datasets de HF. Sin estado, sin cache, sin escritura."""
from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

HUB = "https://huggingface.co/api"
DS_SERVER = "https://datasets-server.huggingface.co"
DEFAULT_REPO_DATASET = "COMAND-CENTER-1/yaiwes-hf-memoria"
ACTIONS = ("status", "search", "info", "splits", "rows", "repo_tree")
_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*(/[A-Za-z0-9][A-Za-z0-9._-]*)?$")


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


def _auth() -> dict[str, str]:
    token = os.getenv("HF_TOKEN", "").strip()
    return {"Authorization": "Bearer " + token} if token else {}


def _ds(payload: dict[str, Any]) -> str:
    ds = str(payload.get("dataset") or os.getenv("HF_REPO_DATASET", DEFAULT_REPO_DATASET)).strip()
    if not _ID_RE.match(ds):
        raise ValueError("dataset invalido")
    return ds


def _get(url: str) -> dict[str, Any]:
    st, raw = _http("GET", url, _auth())
    data = _json(raw)
    if st != 200 or data is None:
        return {"status": "error", "http_status": st, "error": raw[:300].decode("utf-8", "replace")}
    return {"status": "ok", "data": data}


def handle(action: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    q = urllib.parse.urlencode
    try:
        if action == "status":
            return {"status": "ok", "repo_dataset": os.getenv("HF_REPO_DATASET", DEFAULT_REPO_DATASET), "token_present": bool(_auth()), "actions": list(ACTIONS), "stores_data": False}
        if action == "search":
            limit = max(1, min(int(payload.get("limit") or 10), 50))
            return _get(f"{HUB}/datasets?" + q({"search": str(payload.get("query") or ""), "limit": limit}))
        if action == "info":
            return _get(f"{HUB}/datasets/{_ds(payload)}")
        if action == "splits":
            return _get(f"{DS_SERVER}/splits?" + q({"dataset": _ds(payload)}))
        if action == "rows":
            args = {"dataset": _ds(payload), "config": str(payload.get("config") or "default"), "split": str(payload.get("split") or "train"),
                    "offset": max(0, int(payload.get("offset") or 0)), "length": max(1, min(int(payload.get("length") or 10), 100))}
            return _get(f"{DS_SERVER}/rows?" + q(args))
        if action == "repo_tree":
            payload = {**payload, "dataset": os.getenv("HF_REPO_DATASET", DEFAULT_REPO_DATASET)}
            return _get(f"{HUB}/datasets/{_ds(payload)}/tree/main")
        return {"status": "error", "error": "accion no permitida", "allowed": list(ACTIONS)}
    except Exception as exc:
        return {"status": "error", "error": str(exc)[:300]}
