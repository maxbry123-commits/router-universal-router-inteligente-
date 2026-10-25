"""hf_skills: listado/lectura por llamada de la biblioteca oficial huggingface/skills (solo lectura).

Repo y commit vienen de integration/huggingface/hf_skills_registry.json (hecho por GPT):
upstream.repository = https://github.com/huggingface/skills, commit abc20ae526d8b4c0e4dff89f904adce28a4a0eb6.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

REPO = "huggingface/skills"
REPO_URL = "https://github.com/huggingface/skills"
PINNED_COMMIT = "abc20ae526d8b4c0e4dff89f904adce28a4a0eb6"
KNOWN_SKILLS = ("hf-cli", "huggingface-datasets", "huggingface-llm-trainer", "huggingface-vision-trainer", "huggingface-community-evals",
                "huggingface-trackio", "huggingface-papers", "huggingface-paper-publisher", "huggingface-tool-builder", "gradio", "transformers-js")
MAX_READ = 200_000
ACTIONS = ("status", "registry", "list", "read")


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


def _headers(raw: bool = False) -> dict[str, str]:
    h = {"Accept": "application/vnd.github.raw" if raw else "application/vnd.github+json", "User-Agent": "riu-hf-skills"}
    tok = os.getenv("GITHUB_TOKEN", "").strip()
    if tok:
        h["Authorization"] = "Bearer " + tok
    return h


def _path(value: Any) -> str:
    p = str(value or "").strip().strip("/")
    if ".." in p.split("/") or "\\" in p:
        raise ValueError("path invalido")
    return p


def _url(p: str, ref: str) -> str:
    return f"https://api.github.com/repos/{REPO}/contents/{urllib.parse.quote(p)}?ref={urllib.parse.quote(ref)}"


def handle(action: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    try:
        ref = str(payload.get("ref") or PINNED_COMMIT)
        if action == "status":
            return {"status": "ok", "repo": REPO_URL, "pinned_commit": PINNED_COMMIT, "read_only": True, "actions": list(ACTIONS)}
        if action == "registry":
            return {"status": "ok", "repo": REPO_URL, "pinned_commit": PINNED_COMMIT, "skills": list(KNOWN_SKILLS)}
        if action == "list":
            st, raw = _http("GET", _url(_path(payload.get("path")), ref), _headers())
            data = _json(raw)
            if st != 200 or not isinstance(data, list):
                return {"status": "error", "http_status": st, "error": raw[:300].decode("utf-8", "replace")}
            return {"status": "ok", "ref": ref, "entries": [{"name": e.get("name"), "type": e.get("type"), "path": e.get("path"), "size": e.get("size")} for e in data]}
        if action == "read":
            p = _path(payload.get("path"))
            if not p:
                return {"status": "error", "error": "path requerido"}
            st, raw = _http("GET", _url(p, ref), _headers(True), None, 60)
            if st != 200:
                return {"status": "error", "http_status": st, "error": raw[:300].decode("utf-8", "replace")}
            return {"status": "ok", "ref": ref, "path": p, "content": raw[:MAX_READ].decode("utf-8", "replace"), "truncated": len(raw) > MAX_READ}
        return {"status": "error", "error": "accion no permitida", "allowed": list(ACTIONS)}
    except Exception as exc:
        return {"status": "error", "error": str(exc)[:300]}
