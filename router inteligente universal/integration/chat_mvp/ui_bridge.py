"""UI bridge for the Vercel chat: GitHub accounts, control panel (pause / resume / emergency), scheduled orders and agent groups.

Mounted in app.py. Every route needs X-API-Key == RIU_ROUTER_API_KEY (when that variable is set).
Flags and the order queue live in the repo (GitHub contents API) so the Job, the agents and Opus all see the same state.
Stdlib only (urllib). No secrets in code: tokens come from environment variables.
"""
from __future__ import annotations

import base64
import json
import os
import time
import urllib.request
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Header, HTTPException

REPO = os.getenv("RIU_REPO", "maxbry123-commits/router-universal-router-inteligente-")
AGENTS_DIR = "router inteligente universal/agents-yaiwes"
ROUTER_FLAG = f"{AGENTS_DIR}/ROUTER_JOB_PAUSE.flag"
AGENTS_FLAG = f"{AGENTS_DIR}/AGENTS_PAUSE.flag"
ORDERS = "Claude notas/ORDENES.json"
GROUPS_FILE = Path(os.getenv("RIU_GROUPS_FILE", "/tmp/riu_groups.json"))
TOKEN_VARS = ("RIU_GITHUB_PAT_FULL_ACCESO", "GH_JOB_PUSH_TOKEN", "GH_PAT_FINE_FULL", "GITHUB_TOKEN")


def _auth(key: str | None) -> None:
    want = os.getenv("RIU_ROUTER_API_KEY", "")
    if want and key != want:
        raise HTTPException(status_code=401, detail="X-API-Key inválida")


def _token() -> str:
    for v in TOKEN_VARS:
        if os.getenv(v):
            return os.environ[v]
    raise HTTPException(status_code=503, detail="sin token de GitHub en el Router")


def _gh(method: str, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
    url = f"https://api.github.com/repos/{REPO}/contents/{urllib.request.quote(path)}"
    req = urllib.request.Request(url, method=method, data=json.dumps(body).encode() if body else None,
                                 headers={"Authorization": f"Bearer {_token()}", "Accept": "application/vnd.github+json"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return {}
        raise HTTPException(status_code=502, detail=f"GitHub {e.code}")


def _read(path: str) -> tuple[str, str | None]:
    d = _gh("GET", path)
    if not d:
        return "", None
    return base64.b64decode(d["content"]).decode("utf-8"), d["sha"]


def _write(path: str, text: str, msg: str) -> None:
    _, sha = _read(path)
    body: dict[str, Any] = {"message": msg, "content": base64.b64encode(text.encode()).decode()}
    if sha:
        body["sha"] = sha
    _gh("PUT", path, body)


def _set_flag(path: str, paused: bool) -> None:
    text, _ = _read(path)
    lines = [ln for ln in text.splitlines() if ln and not ln.startswith("PAUSED=")]
    _write(path, "\n".join([f"PAUSED={'true' if paused else 'false'}"] + lines) + "\n", f"panel: PAUSED={paused} {path.rsplit('/', 1)[-1]}")


def build_ui_bridge_router() -> APIRouter:
    r = APIRouter()

    @r.get("/gh/accounts")
    def accounts(x_api_key: str | None = Header(None)) -> dict[str, Any]:
        _auth(x_api_key)
        return {"accounts": [f"GH_ACCOUNT_{i}" for i in range(1, 6) if os.getenv(f"GH_ACCOUNT_{i}")] or ["principal"]}

    @r.get("/control/status")
    def status(x_api_key: str | None = Header(None)) -> dict[str, Any]:
        _auth(x_api_key)
        return {"router": _read(ROUTER_FLAG)[0], "agents": _read(AGENTS_FLAG)[0] or "PAUSED=false\n"}

    @r.post("/control/{action}")
    def control(action: str, body: dict[str, Any] | None = None, x_api_key: str | None = Header(None)) -> dict[str, Any]:
        _auth(x_api_key)
        if action == "pause-agents":
            _set_flag(AGENTS_FLAG, True)
        elif action == "resume-agents":
            _set_flag(AGENTS_FLAG, False)
        elif action == "pause-router":
            _set_flag(ROUTER_FLAG, True)
        elif action == "resume-router":
            _set_flag(ROUTER_FLAG, False)
        elif action == "emergency-stop":
            _set_flag(AGENTS_FLAG, True)
            _set_flag(ROUTER_FLAG, True)
        elif action == "order":
            b = body or {}
            if not b.get("agente") or not b.get("orden"):
                raise HTTPException(status_code=400, detail="faltan agente u orden")
            text, _ = _read(ORDERS)
            queue = json.loads(text) if text.strip() else []
            queue.append({"id": f"ORD-{int(time.time())}", "hora": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                          "agente": b["agente"], "orden": b["orden"], "prioridad": b.get("prioridad", "normal"),
                          "programada_para": b.get("programada_para"), "estado": "PENDIENTE"})
            _write(ORDERS, json.dumps(queue, ensure_ascii=False, indent=1), "panel: nueva orden")
        else:
            raise HTTPException(status_code=404, detail="acción desconocida")
        return {"ok": True, "action": action}

    @r.get("/groups")
    def groups_get(x_api_key: str | None = Header(None)) -> dict[str, Any]:
        _auth(x_api_key)
        return json.loads(GROUPS_FILE.read_text()) if GROUPS_FILE.exists() else {}

    @r.post("/groups")
    def groups_set(body: dict[str, Any], x_api_key: str | None = Header(None)) -> dict[str, Any]:
        _auth(x_api_key)
        name = body.get("grupo")
        if not name:
            raise HTTPException(status_code=400, detail="falta grupo")
        data = json.loads(GROUPS_FILE.read_text()) if GROUPS_FILE.exists() else {}
        data[name] = {"orquestador": body.get("orquestador"), "agentes": body.get("agentes", []),
                      "api_origen": body.get("api_origen", "deepseek"), "modelo": body.get("modelo")}
        GROUPS_FILE.write_text(json.dumps(data, ensure_ascii=False))
        return {"ok": True, "grupos": list(data)}

    return r
