"""Tiny adapter for the existing nct_loop plugin: no new HTTP server or database.

Host injects async callbacks load_cb(scope,key) and save_cb(scope,key,data)
from the EXISTING memory provider, after authenticated plugin authorization.
"""
from __future__ import annotations
import inspect
from .canvas_graph import validate_graph, from_loop_dag, valid_id, CanvasGraphError

async def _await(result):
    return await result if inspect.isawaitable(result) else result

def _latest(data):
    if isinstance(data,dict) and isinstance(data.get("records"),list):
        items=data["records"]
        if not items:return None
        newest=max(items,key=lambda x:int(x.get("id",0)))
        return newest.get("data")
    return data

async def handle_canvas(action,payload,*,load_cb=None,save_cb=None):
    """Only user-selected graphs, no tool execution, no shells, no arbitrary fetch."""
    try:
        if not isinstance(payload,dict):raise CanvasGraphError("INVALID_REQUEST")
        if action=="canvas_validate":return validate_graph(payload.get("graph"))
        if action=="canvas_from_dag":return from_loop_dag(payload)
        if action not in {"canvas_save","canvas_load"}:raise CanvasGraphError("UNKNOWN_ACTION")
        project_id=valid_id(payload.get("project_id"),"project_id")
        graph_id=valid_id(payload.get("graph_id"),"graph_id")
        scope="canvas:"+project_id
        if not callable(load_cb):raise CanvasGraphError("BACKEND_PERSISTENCE_MISSING")
        existing=_latest(await _await(load_cb(scope,graph_id)))
        if action=="canvas_load":
            if not isinstance(existing,dict) or "graph" not in existing:
                raise CanvasGraphError("GRAPH_NOT_FOUND")
            val=validate_graph(existing["graph"])
            if existing.get("sha256")!=val["sha256"]:
                raise CanvasGraphError("PERSISTED_HASH_MISMATCH")
            return {"ok":True,"graph":val["graph"],"sha256":val["sha256"],
                    "revision":int(existing.get("revision",1))}
        if not callable(save_cb):raise CanvasGraphError("BACKEND_PERSISTENCE_MISSING")
        result=validate_graph(payload.get("graph"))
        graph=result["graph"]
        if graph["graph_id"]!=graph_id or graph["project_id"]!=project_id:
            raise CanvasGraphError("GRAPH_SCOPE_MISMATCH")
        actualrev=int(existing.get("revision",0)) if isinstance(existing,dict) else 0
        expected=payload.get("expected_revision")
        if type(expected)!=int or expected!=actualrev:raise CanvasGraphError("REVISION_CONFLICT")
        value={"revision":actualrev+1,"graph":graph,"sha256":result["sha256"]}
        ack=await _await(save_cb(scope,graph_id,value))
        if not isinstance(ack,dict) or ack.get("ok") is not True:
            raise CanvasGraphError("PERSISTENCE_NOT_CONFIRMED")
        # Host may require explicit read-back. Re-read actual storage to claim PASS.
        reloaded=_latest(await _await(load_cb(scope,graph_id)))
        if not isinstance(reloaded,dict) or reloaded.get("sha256")!=result["sha256"] or reloaded.get("revision")!=value["revision"]:
            raise CanvasGraphError("READBACK_MISMATCH")
        checked=validate_graph(reloaded.get("graph"))
        if checked["sha256"]!=result["sha256"]:
            raise CanvasGraphError("READBACK_MISMATCH")
        return {"ok":True,"sha256":result["sha256"],"revision":value["revision"],"verified":True}
    except (CanvasGraphError,TypeError,ValueError,OverflowError) as exc:
        return {"ok":False,"error":getattr(exc,"code","INVALID_INPUT"),"detail":str(exc)[:180]}
