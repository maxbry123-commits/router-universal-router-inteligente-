"""Read-only organization projections for the chat Router."""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from pathlib import Path
from typing import Literal

import yaml
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parents[3] / "chat router"
STATE = ROOT / "03-ESTADO"


class OrgResponse(BaseModel):
    status: Literal["ok"]
    data: dict


def _json(path: Path, fallback: object) -> object:
    if not path.is_file():
        return fallback
    return json.loads(path.read_text(encoding="utf-8"))


def _ok(data: dict) -> dict:
    return {"status": "ok", "data": data}


def _error(code: str, status: int) -> JSONResponse:
    return JSONResponse(status_code=status, content={"status": "error", "detail": code})


def build_org_router(auth: Callable, store: Callable, catalog: Callable) -> APIRouter:
    router = APIRouter(prefix="/chat/org", dependencies=[Depends(auth)])

    @router.get("/graph", response_model=OrgResponse)
    def graph() -> dict:
        data = _json(STATE / "AGENT_GRAPH.json", {"nodes": [], "edges": []})
        return _ok({"graph": data, "state": _json(STATE / "STATE.json", {}),
                    "crazy_wall": _json(STATE / "CRAZY_WALL.json", {})})

    @router.get("/queue", response_model=OrgResponse)
    def queue() -> dict:
        queue_dir = ROOT / "EVIDENCIA/cola"
        return _ok({"tasks": _json(queue_dir / "tareas.json", []),
                    "workers": _json(queue_dir / "workers.json", [])})

    @router.get("/bitacora", response_model=OrgResponse)
    def bitacora(limit: int = 50) -> dict:
        if limit < 1 or limit > 200:
            return _error("LIMIT_INVALID", 400)
        path = STATE / "BITACORA.jsonl"
        lines = path.read_text(encoding="utf-8").splitlines() if path.is_file() else []
        return _ok({"events": [json.loads(line) for line in lines[-limit:] if line.strip()]})

    @router.get("/dag/{run_id}", response_model=OrgResponse)
    def dag_run(run_id: str) -> dict:
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}", run_id):
            return _error("DAG_ID_INVALID", 400)
        path = ROOT / "chat_orders/results" / f"{run_id}.result.json"
        if not path.is_file():
            return _error("DAG_NOT_FOUND", 404)
        return _ok({"run": _json(path, {})})

    @router.get("/connectors", response_model=OrgResponse)
    def connectors() -> dict:
        return _ok({"connectors": catalog().list()})

    @router.get("/templates", response_model=OrgResponse)
    def templates() -> dict:
        path = ROOT / "01-PLAN/PLAN-DSL-DAG-UI.yaml"
        plan = yaml.safe_load(path.read_text(encoding="utf-8")) if path.is_file() else {}
        nodes = plan.get("nodes", [])
        return _ok({"templates": [{"id": node["id"], "title": node.get("titulo", node["id"]),
                                   "locked": True} for node in nodes]})

    @router.get("/engineering", response_model=OrgResponse)
    def engineering() -> dict:
        return _ok({"toggles": [], "state": _json(STATE / "STATE.json", {})})

    @router.get("/files", response_model=OrgResponse)
    def files() -> dict:
        storage = store()
        graph = storage.graph_view()
        anchors = [edge for edge in graph["edges"] if edge["src"].startswith("doc:") and edge["dst"].startswith("dag:")]
        return _ok({"files": storage.documents(), "anchors": anchors, "mcp": []})

    return router
