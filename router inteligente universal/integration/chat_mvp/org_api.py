"""Read-only organization projections for the chat Router."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Callable
from pathlib import Path
from typing import Literal

import yaml
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from . import ui_bridge

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


def _audited(resource: str, response: dict | JSONResponse, status: int = 200) -> dict | JSONResponse:
    try:
        ui_bridge._emit_state_audit_event(resource, status)
    except (HTTPException, OSError, ValueError):
        return _error("STATE_AUDIT_UNAVAILABLE", 503)
    return response


def build_org_router(auth: Callable, store: Callable, catalog: Callable) -> APIRouter:
    router = APIRouter(prefix="/chat/org", dependencies=[Depends(auth)])

    @router.get("/graph", response_model=OrgResponse)
    def graph() -> dict:
        data = _json(STATE / "AGENT_GRAPH.json", {"nodes": [], "edges": []})
        return _audited("graph", _ok({"graph": data, "state": _json(STATE / "STATE.json", {}),
                                     "crazy_wall": _json(STATE / "CRAZY_WALL.json", {})}))

    @router.get("/queue", response_model=OrgResponse)
    def queue() -> dict:
        queue_dir = ROOT / "EVIDENCIA/cola"
        return _audited("queue", _ok({"tasks": _json(queue_dir / "tareas.json", []),
                                     "workers": _json(queue_dir / "workers.json", [])}))

    @router.get("/bitacora", response_model=OrgResponse)
    def bitacora(limit: str = "50") -> dict:
        if not re.fullmatch(r"[0-9]{1,3}", limit) or not 1 <= int(limit) <= 200:
            return _audited("bitacora", _error("LIMIT_INVALID", 400), 400)
        try:
            log, _ = ui_bridge._read(ui_bridge.BITACORA)
            lines = log.splitlines()
        except (HTTPException, OSError, ValueError):
            return _error("STATE_AUDIT_UNAVAILABLE", 503)
        return _audited("bitacora", _ok({"events": [json.loads(line) for line in lines[-int(limit):] if line.strip()]}))

    @router.get("/dag/{run_id}", response_model=OrgResponse)
    def dag_run(run_id: str) -> dict:
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}", run_id):
            return _audited("dag", _error("DAG_ID_INVALID", 400), 400)
        path = ROOT / "chat_orders/results" / f"{run_id}.result.json"
        if not path.is_file():
            return _audited("dag", _error("DAG_NOT_FOUND", 404), 404)
        return _audited("dag", _ok({"run": _json(path, {})}))

    @router.get("/connectors", response_model=OrgResponse)
    def connectors() -> dict:
        return _audited("connectors", _ok({"connectors": catalog().list()}))

    @router.get("/visual-references", response_model=OrgResponse)
    def visual_references() -> dict:
        images = ROOT / "01-PLAN/REFERENCIAS-UI"
        items = []
        seen_ids: set[str] = set()
        catalogs = (
            ("CATALOGO-REFERENCIAS-UI.json", "yaiwes.visual-reference-catalog/v1"),
            ("CATALOGO-ANEXOS-VISUALES.json", "yaiwes.visual-annex-catalog/v1"),
        )
        for name, schema in catalogs:
            path = ROOT / "01-PLAN" / name
            if not path.is_file():
                return _audited("visual-references", _error("VISUAL_CATALOG_MISSING", 503), 503)
            try:
                catalog_data = _json(path, {})
                if (not isinstance(catalog_data, dict) or catalog_data["schema"] != schema
                        or not isinstance(catalog_data["items"], list)):
                    raise TypeError("VISUAL_CATALOG_INVALID")
                for item in catalog_data["items"]:
                    if (not isinstance(item, dict) or not isinstance(item["id"], str)
                            or not isinstance(item["file"], str) or not isinstance(item["function"], str)
                            or not isinstance(item["sha256"], str)
                            or not re.fullmatch(r"[0-9a-f]{64}", item["sha256"])
                            or item["id"] in seen_ids):
                        raise ValueError("VISUAL_CATALOG_ITEM_INVALID")
                    seen_ids.add(item["id"])
                    image = (ROOT.parent / item["file"]).resolve()
                    if not image.is_relative_to(images.resolve()) or not image.is_file():
                        return _audited("visual-references", _error("VISUAL_SOURCE_MISSING", 503), 503)
                    if hashlib.sha256(image.read_bytes()).hexdigest() != item["sha256"]:
                        return _audited("visual-references", _error("VISUAL_HASH_MISMATCH", 503), 503)
                    items.append({"id": item["id"], "function": item["function"], "sha256": item["sha256"],
                                  "duplicate_of": item["duplicate_of"], "classification": "REFERENCE_ONLY",
                                  "backend": "CATALOG_METADATA_ONLY"})
                if type(catalog_data["count"]) is not int or catalog_data["count"] != len(catalog_data["items"]):
                    raise ValueError("VISUAL_CATALOG_COUNT_INVALID")
            except (OSError, ValueError, TypeError, KeyError):
                return _audited("visual-references", _error("VISUAL_CATALOG_INVALID", 503), 503)
        return _audited("visual-references", _ok({"count": len(items), "items": items}))

    @router.get("/templates", response_model=OrgResponse)
    def templates() -> dict:
        path = ROOT / "01-PLAN/PLAN-DSL-DAG-UI.yaml"
        plan = yaml.safe_load(path.read_text(encoding="utf-8")) if path.is_file() else {}
        nodes = plan.get("nodes", [])
        return _audited("templates", _ok({"templates": [{"id": node["id"], "title": node.get("titulo", node["id"]),
                                            "locked": True} for node in nodes]}))

    @router.get("/engineering", response_model=OrgResponse)
    def engineering() -> dict:
        return _audited("engineering", _ok({"toggles": [], "state": _json(STATE / "STATE.json", {})}))

    @router.get("/files", response_model=OrgResponse)
    def files() -> dict:
        storage = store()
        graph = storage.graph_view()
        anchors = [edge for edge in graph["edges"] if edge["src"].startswith("doc:") and edge["dst"].startswith("dag:")]
        return _audited("files", _ok({"files": storage.documents(), "anchors": anchors, "mcp": []}))

    return router
