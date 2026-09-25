"""UI bridge for the chat: control panel (pause / resume / emergency), scheduled orders, agent groups and workflows.

Mounted in app.py. Every route needs X-API-Key == RIU_ROUTER_API_KEY (when that variable is set).
Flags, orders, groups and workflows live in the repo (GitHub contents API): they survive Router restarts and the Job, the agents
and Opus all see the same state. Orders are also written as yaiwes.instruction/v1 files in the agent's inbox/.
Stdlib only (urllib). No secrets in code: tokens come from environment variables.
"""
from __future__ import annotations

import base64
import json
import os
import time
import urllib.error
import urllib.request
from typing import Any

from fastapi import APIRouter, Header, HTTPException

REPO = os.getenv("RIU_REPO", "maxbry123-commits/router-universal-router-inteligente-")
AGENTS_DIR = "router inteligente universal/agents-yaiwes"
ROUTER_FLAG = f"{AGENTS_DIR}/ROUTER_JOB_PAUSE.flag"
AGENTS_FLAG = f"{AGENTS_DIR}/AGENTS_PAUSE.flag"
DATA = "chat router/data"
ORDERS = f"{DATA}/ordenes.json"
GROUPS = f"{DATA}/grupos.json"
WORKFLOWS = f"{DATA}/workflows.json"
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


def _load(path: str, default: Any) -> Any:
    text, _ = _read(path)
    try:
        return json.loads(text) if text.strip() else default
    except json.JSONDecodeError:
        return default


def _set_flag(path: str, paused: bool) -> None:
    text, _ = _read(path)
    lines = [ln for ln in text.splitlines() if ln and not ln.startswith("PAUSED=")]
    _write(path, "\n".join([f"PAUSED={'true' if paused else 'false'}"] + lines) + "\n", f"panel: PAUSED={paused} {path.rsplit('/', 1)[-1]}")


def build_ui_bridge_router() -> APIRouter:
    r = APIRouter()

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
            agent, order = str(b.get("agente") or "").strip(), str(b.get("orden") or "").strip()
            if not agent or not order:
                raise HTTPException(status_code=400, detail="faltan agente u orden")
            oid = f"ORD-{int(time.time())}"
            queue = _load(ORDERS, [])
            queue.append({"id": oid, "hora": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "agente": agent, "orden": order,
                          "prioridad": b.get("prioridad", "normal"), "programada_para": b.get("programada_para"), "estado": "PENDIENTE"})
            _write(ORDERS, json.dumps(queue, ensure_ascii=False, indent=1), f"chat: orden {oid} para {agent}")
            instr = {"schema": "yaiwes.instruction/v1", "task_id": oid, "target_agent": agent, "instruction": order,
                     "programada_para": b.get("programada_para"), "checks": [{"kind": "no_secrets"}]}
            _write(f"{AGENTS_DIR}/{agent}/inbox/{oid}.json", json.dumps(instr, ensure_ascii=False, indent=1), f"chat: inbox {agent} {oid}")
            return {"ok": True, "action": action, "id": oid}
        else:
            raise HTTPException(status_code=404, detail="acción desconocida")
        return {"ok": True, "action": action}

    @r.get("/groups")
    def groups_get(x_api_key: str | None = Header(None)) -> dict[str, Any]:
        _auth(x_api_key)
        return _load(GROUPS, {})

    @r.post("/groups")
    def groups_set(body: dict[str, Any], x_api_key: str | None = Header(None)) -> dict[str, Any]:
        _auth(x_api_key)
        name = str(body.get("grupo") or "").strip()
        if not name:
            raise HTTPException(status_code=400, detail="falta grupo")
        data = _load(GROUPS, {})
        data[name] = {"orquestador": body.get("orquestador"), "agentes": body.get("agentes", []),
                      "api_origen": body.get("api_origen", "hf"), "modelo": body.get("modelo")}
        _write(GROUPS, json.dumps(data, ensure_ascii=False, indent=1), f"chat: grupo {name}")
        return {"ok": True, "grupos": list(data)}

    @r.get("/workflows")
    def workflows_get(x_api_key: str | None = Header(None)) -> dict[str, Any]:
        _auth(x_api_key)
        return {"workflows": _load(WORKFLOWS, [])}

    @r.post("/workflows")
    def workflows_add(body: dict[str, Any], x_api_key: str | None = Header(None)) -> dict[str, Any]:
        _auth(x_api_key)
        wf = {k: str(body.get(k) or "").strip() for k in ("nombre", "repo", "plan", "orquestador")}
        if not wf["nombre"] or not wf["repo"]:
            raise HTTPException(status_code=400, detail="faltan nombre o repo")
        data = [w for w in _load(WORKFLOWS, []) if w.get("nombre") != wf["nombre"]] + [wf]
        _write(WORKFLOWS, json.dumps(data, ensure_ascii=False, indent=1), f"chat: workflow {wf['nombre']}")
        return {"ok": True, "workflows": data}

    return r
