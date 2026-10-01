"""UI bridge for the chat: control panel (pause / resume / emergency), scheduled orders, agent groups and workflows.

Mounted in app.py. Every route needs X-API-Key == RIU_ROUTER_API_KEY (when that variable is set).
Flags, orders, groups and workflows live in the repo (GitHub contents API): they survive Router restarts and the Job, the agents
and Opus all see the same state. Orders are also written as yaiwes.instruction/v1 files in the agent's inbox/.
Stdlib only (urllib). No secrets in code: tokens come from environment variables.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import threading
import time
import urllib.error
import urllib.request
import uuid
from typing import Any

from fastapi import APIRouter, Header, HTTPException

REPO = os.getenv("RIU_REPO", "maxbry123-commits/router-universal-router-inteligente-")
AGENTS_DIR = "router inteligente universal/agents-yaiwes"
ROUTER_FLAG = f"{AGENTS_DIR}/ROUTER_JOB_PAUSE.flag"
AGENTS_FLAG = f"{AGENTS_DIR}/AGENTS_PAUSE.flag"
DATA = "chat router/03-ESTADO/data"
ORDERS = f"{DATA}/ordenes.json"
GROUPS = f"{DATA}/grupos.json"
WORKFLOWS = f"{DATA}/workflows.json"
STATE_DIR = "chat router/03-ESTADO"
BITACORA = f"{STATE_DIR}/BITACORA.jsonl"
STATE = f"{STATE_DIR}/STATE.json"
CRAZY_WALL = f"{STATE_DIR}/CRAZY_WALL.json"
HANDOFF = f"{STATE_DIR}/HANDOFF.md"
_STATE_LOCK = threading.RLock()
_STATE_EVENT_TYPES = {"TASK_CLAIMED", "FILES_CHANGED", "CHECKPOINT_RECORDED", "TASK_BLOCKED", "TASK_COMPLETED", "TASK_RELEASED", "RESOURCE_READ"}
_SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
_SECRET_LIKE = re.compile(r"\b(?:hf_[A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9_-]{20,})\b")
_HANDOFF_START = "<!-- YAIWES STATE HUB START -->"
_HANDOFF_END = "<!-- YAIWES STATE HUB END -->"
TOKEN_VARS = ("RIU_GITHUB_PAT_FULL_ACCESO", "GH_JOB_PUSH_TOKEN", "GH_PAT_FINE_FULL", "GITHUB_TOKEN")


def _auth(key: str | None) -> None:
    want = os.getenv("RIU_ROUTER_API_KEY", "")
    if want and key != want:
        raise HTTPException(status_code=401, detail="X-API-Key inválida")


def _state_auth(key: str | None) -> None:
    want = os.getenv("RIU_ROUTER_API_KEY", "")
    if not want:
        raise HTTPException(status_code=503, detail="STATE_HUB_AUTH_NOT_CONFIGURED")
    if key != want:
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


def _state_events(text: str) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    last_seq = 0
    seen_ids: set[str] = set()
    versioned = False
    for line_no, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=409, detail=f"STATE_BITACORA_INVALID_JSON:{line_no}") from exc
        if not isinstance(event, dict) or type(event.get("seq")) is not int or event["seq"] <= last_seq:
            raise HTTPException(status_code=409, detail=f"STATE_BITACORA_INVALID_SEQUENCE:{line_no}")
        if event.get("type") not in _STATE_EVENT_TYPES:
            raise HTTPException(status_code=409, detail=f"STATE_BITACORA_UNKNOWN_EVENT:{line_no}")
        if event.get("schema") == "yaiwes.state-event/v2":
            versioned = True
            event_id = event.get("event_id")
            digest = event.get("payload_hash")
            if (
                not isinstance(event_id, str)
                or not re.fullmatch(r"[0-9a-f]{32}", event_id)
                or event_id in seen_ids
                or not isinstance(digest, str)
                or digest != _event_hash(event)
            ):
                raise HTTPException(status_code=409, detail=f"STATE_BITACORA_INVALID_HASH:{line_no}")
            seen_ids.add(event_id)
        elif versioned or "event_id" in event or "payload_hash" in event or "schema" in event:
            raise HTTPException(status_code=409, detail=f"STATE_BITACORA_INVALID_SCHEMA:{line_no}")
        last_seq = event["seq"]
        events.append(event)
    return events


def _state_event(body: dict[str, Any], seq: int) -> dict[str, Any]:
    kind = str(body.get("type") or "")
    if kind not in _STATE_EVENT_TYPES:
        raise HTTPException(status_code=400, detail="STATE_EVENT_TYPE_INVALID")
    event: dict[str, Any] = {"seq": seq, "type": kind, "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    for key in ("project", "task", "actor"):
        value = str(body.get(key) or "").strip()
        if not _SAFE_ID.fullmatch(value):
            raise HTTPException(status_code=400, detail=f"STATE_EVENT_{key.upper()}_INVALID")
        event[key] = value
    for key in ("phase", "next", "status"):
        value = " ".join(str(body.get(key) or "").split())
        if value:
            if len(value) > 80 or _SECRET_LIKE.search(value):
                raise HTTPException(status_code=400, detail=f"STATE_EVENT_{key.upper()}_INVALID")
            if key == "status" and value not in {"PENDING", "CLAIMED", "RUNNING", "BLOCKED", "COMPLETED"}:
                raise HTTPException(status_code=400, detail="STATE_EVENT_STATUS_INVALID")
            event[key] = value
    summary = " ".join(str(body.get("summary") or "").split())
    if len(summary) > 600 or _SECRET_LIKE.search(summary):
        raise HTTPException(status_code=400, detail="STATE_EVENT_SUMMARY_INVALID")
    if summary:
        event["summary"] = summary
    if "files_changed" in body:
        try:
            count = int(body["files_changed"])
        except (TypeError, ValueError) as exc:
            raise HTTPException(status_code=400, detail="STATE_EVENT_FILES_CHANGED_INVALID") from exc
        if count < 0 or count > 10000:
            raise HTTPException(status_code=400, detail="STATE_EVENT_FILES_CHANGED_INVALID")
        event["files_changed"] = count
    event["schema"] = "yaiwes.state-event/v2"
    event["event_id"] = uuid.uuid4().hex
    event["payload_hash"] = _event_hash(event)
    return event


def _event_hash(event: dict[str, Any]) -> str:
    payload = {key: value for key, value in event.items() if key != "payload_hash"}
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _state_projection(events: list[dict[str, Any]]) -> tuple[dict[str, Any], dict[str, Any]]:
    nodes: dict[str, dict[str, Any]] = {}
    active_project = None
    last_functional_event = None
    for event in events:
        if event["type"] == "RESOURCE_READ":
            continue
        last_functional_event = event
        project, task = event["project"], event["task"]
        active_project = project
        node = nodes.setdefault(task, {"node_id": task, "task": task, "project": project, "status": "PENDING"})
        if event["type"] == "TASK_CLAIMED":
            node.update(status="CLAIMED", agent_name=event["actor"], claimed_at=event["at"])
        elif event["type"] == "TASK_BLOCKED":
            node["status"] = "BLOCKED"
        elif event["type"] == "TASK_COMPLETED":
            node["status"] = "COMPLETED"
        elif event["type"] == "TASK_RELEASED":
            node["status"] = "PENDING"
        elif event["type"] in {"FILES_CHANGED", "CHECKPOINT_RECORDED"} and node["status"] == "PENDING":
            node["status"] = "RUNNING"
        for key in ("phase", "next", "summary", "files_changed"):
            if key in event:
                node[key] = event[key]
        if "status" in event:
            node["status"] = event["status"]
        node["updated_at"] = event["at"]
        node["last_event_seq"] = event["seq"]

    projects: dict[str, dict[str, Any]] = {}
    for node in nodes.values():
        project = projects.setdefault(node["project"], {"status": "RUNNING", "progress": 0, "active_tasks": [], "blocked_tasks": []})
        if node["status"] in {"CLAIMED", "RUNNING"}:
            project["active_tasks"].append(node["task"])
        elif node["status"] == "BLOCKED":
            project["blocked_tasks"].append(node["task"])
    for project in projects.values():
        if not project["active_tasks"] and not project["blocked_tasks"]:
            project["status"] = "COMPLETED"

    revision = last_functional_event["seq"] if last_functional_event else 0
    updated_at = last_functional_event["at"] if last_functional_event else None
    state = {"schema": "yaiwes.state/v1", "revision": revision, "updated_at": updated_at,
             "active_project": active_project, "projects": projects}
    crazy_wall = {"schema": "yaiwes.crazy-wall/v1", "nodes": nodes}
    return state, crazy_wall


def _render_handoff(existing: str, state: dict[str, Any], crazy_wall: dict[str, Any], events: list[dict[str, Any]]) -> str:
    before = existing.split(_HANDOFF_START, 1)[0].rstrip()
    if _HANDOFF_END in existing:
        after = existing.split(_HANDOFF_END, 1)[1].lstrip()
    else:
        after = ""
    sections = [before] if before else []
    lines = [_HANDOFF_START, "## Estado operativo generado por State Hub", f"Revisión: {state['revision']}"]
    if events:
        node = max(crazy_wall["nodes"].values(), key=lambda item: item.get("last_event_seq", 0))
        lines.extend([f"Proyecto/tarea: `{node['project']}` / `{node['task']}`", f"Estado: **{node['status']}**"])
        if node.get("phase"):
            lines.append(f"Fase: `{node['phase']}`")
        if node.get("summary"):
            lines.extend(["", "### Último checkpoint", node["summary"]])
        if node.get("next"):
            lines.extend(["", "### Siguiente", node["next"]])
    else:
        lines.append("Sin eventos.")
    lines.append(_HANDOFF_END)
    sections.append("\n".join(lines))
    if after:
        sections.append(after)
    return "\n\n".join(sections).rstrip() + "\n"


def _regenerate_state(events: list[dict[str, Any]]) -> dict[str, Any]:
    state, crazy_wall = _state_projection(events)
    old_handoff, _ = _read(HANDOFF)
    state_text = json.dumps(state, ensure_ascii=False, indent=2) + "\n"
    wall_text = json.dumps(crazy_wall, ensure_ascii=False, indent=2) + "\n"
    handoff_text = _render_handoff(old_handoff, state, crazy_wall, events)
    _write(STATE, state_text, "state hub: regenerate STATE")
    _write(CRAZY_WALL, wall_text, "state hub: regenerate CRAZY_WALL")
    _write(HANDOFF, handoff_text, "state hub: regenerate HANDOFF section")
    return {"revision": state["revision"], "state_sha256": hashlib.sha256(state_text.encode()).hexdigest(),
            "crazy_wall_sha256": hashlib.sha256(wall_text.encode()).hexdigest()}


def _emit_state_event(body: dict[str, Any]) -> dict[str, Any]:
    if body.get("type") == "RESOURCE_READ":
        raise HTTPException(status_code=400, detail="STATE_AUDIT_ONLY_FROM_GET")
    with _STATE_LOCK:
        current, _ = _read(BITACORA)
        events = _state_events(current)
        event = _state_event(body, (events[-1]["seq"] + 1) if events else 1)
        log = current.rstrip() + ("\n" if current.strip() else "") + json.dumps(event, ensure_ascii=False, separators=(",", ":")) + "\n"
        _write(BITACORA, log, f"state hub: {event['type']} {event['task']}")
        persisted, _ = _read(BITACORA)
        if persisted != log:
            raise HTTPException(status_code=503, detail="STATE_EVENT_READBACK_FAILED")
        projection = _regenerate_state(events + [event])
        return {"ok": True, "event": event, **projection}


def _emit_state_audit_event(resource: str, http_status: int) -> dict[str, Any]:
    if resource not in {"graph", "queue", "bitacora", "dag", "connectors", "templates", "engineering", "files", "visual-references"}:
        raise HTTPException(status_code=400, detail="STATE_AUDIT_RESOURCE_INVALID")
    if http_status not in {200, 400, 404, 503}:
        raise HTTPException(status_code=400, detail="STATE_AUDIT_STATUS_INVALID")
    with _STATE_LOCK:
        current, _ = _read(BITACORA)
        events = _state_events(current)
        event = _state_event({
            "type": "RESOURCE_READ", "project": "chat-yaiwes", "task": "UI-T-05",
            "actor": "router", "summary": f"GET /chat/org/{resource} HTTP {http_status}",
        }, (events[-1]["seq"] + 1) if events else 1)
        log = current.rstrip() + ("\n" if current.strip() else "") + json.dumps(event, ensure_ascii=False, separators=(",", ":")) + "\n"
        _write(BITACORA, log, f"state hub: audit GET /chat/org/{resource}")
        persisted, _ = _read(BITACORA)
        if persisted != log:
            raise HTTPException(status_code=503, detail="STATE_AUDIT_READBACK_FAILED")
        return event


def _rebuild_state() -> dict[str, Any]:
    with _STATE_LOCK:
        current, _ = _read(BITACORA)
        return {"ok": True, **_regenerate_state(_state_events(current))}


def build_ui_bridge_router() -> APIRouter:
    r = APIRouter()

    @r.post("/state/events")
    def state_emit(body: dict[str, Any], x_api_key: str | None = Header(None)) -> dict[str, Any]:
        _state_auth(x_api_key)
        return _emit_state_event(body)

    @r.post("/state/rebuild")
    def state_rebuild(x_api_key: str | None = Header(None)) -> dict[str, Any]:
        _state_auth(x_api_key)
        return _rebuild_state()

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
