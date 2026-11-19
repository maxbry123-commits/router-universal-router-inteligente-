"""Endpoints aditivos Salida 2. No modifica código existente."""
from __future__ import annotations
import json, time, uuid, os, re
from pathlib import Path
from threading import Lock
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

_ART = Path(os.environ.get("ARTIFACT_DIR", "artifacts"))
_ROOT = _ART.parent if str(_ART.parent) else Path(".")
_TASKS = _ROOT / ".tasks"; _TASKS.mkdir(parents=True, exist_ok=True)
_FEEDBACK = _ROOT / ".feedback.jsonl"

class TaskStore:
    def __init__(s): s._lock = Lock(); s._mem = {}
    def _p(s, tid): return _TASKS / f"{tid}.json"
    def create(s, kind="chat", payload=None, status="sending"):
        tid = f"t-{uuid.uuid4().hex[:8]}"
        rec = {"task_id": tid, "kind": kind, "payload": payload or {},
               "status": status, "created_at": time.time(),
               "updated_at": time.time(), "cancel_requested": False,
               "retry": {"count": 0, "max": 2, "reason": None},
               "progress": {"step": 0, "total": 1, "label": status},
               "lease_expires_at": time.time() + 96,
               "handoff": None, "error": None}
        with s._lock:
            s._mem[tid] = rec; s._p(tid).write_text(json.dumps(rec))
        return rec
    def get(s, tid):
        with s._lock:
            if tid in s._mem: return s._mem[tid]
            p = s._p(tid)
            if not p.exists(): return None
            rec = json.loads(p.read_text()); s._mem[tid] = rec; return rec
    def update(s, tid, **kw):
        rec = s.get(tid)
        if not rec: return None
        rec.update(kw); rec["updated_at"] = time.time()
        with s._lock:
            s._mem[tid] = rec; s._p(tid).write_text(json.dumps(rec))
        return rec
    def cancel(s, tid):
        return s.update(tid, status="cancelled", cancel_requested=True,
                        progress={"step":0,"total":1,"label":"cancelled"})
    def resume(s, tid):
        r = s.get(tid)
        if not r: return None
        cnt = r.get("retry",{}).get("count",0) + 1
        mx = r.get("retry",{}).get("max",2)
        if cnt > mx:
            return s.update(tid, status="failed",
                error={"code":"RETRIES_EXHAUSTED","message":f"max {mx} alcanzado"},
                progress={"step":0,"total":1,"label":"failed"})
        return s.update(tid, status="queued", cancel_requested=False,
                        retry={"count":cnt,"max":mx,"reason":"resume"},
                        progress={"step":0,"total":1,"label":"queued"})
    def list(s, status=None, limit=100):
        with s._lock: items = list(s._mem.values())
        if status: items = [x for x in items if x.get("status")==status]
        return sorted(items, key=lambda x: x.get("created_at",0), reverse=True)[:limit]

class FeedbackStore:
    def __init__(s): s._lock = Lock()
    def record(s, mid, val, cmt=""):
        line = json.dumps({"message_id":mid,"value":val,"comment":cmt,"ts":time.time()})+"\n"
        with s._lock, open(_FEEDBACK,"a",encoding="utf-8") as f: f.write(line)

class QueueBridge:
    def __init__(s):
        s._closed = False; s._qm = None
        try:
            from router_llm_hf import queue_manager as _qm
            s._qm = _qm
        except Exception: pass
    def snapshot(s):
        if s._qm is not None:
            for n in ("snapshot","status"):
                fn = getattr(s._qm, n, None)
                if callable(fn):
                    try: return fn()
                    except Exception: pass
        return {"running":[],"queued":[],"concurrency":1,"ram_pct":0,
                "closed":s._closed,"state":"closed" if s._closed else "open",
                "lanes":[],"metrics":{"wait_avg_s":0,"abandoned":0},
                "source":"queue_manager" if s._qm else "unavailable"}
    def dead_letter(s):
        if s._qm:
            for n in ("dead_letter","dlq"):
                fn = getattr(s._qm, n, None)
                if callable(fn):
                    try: return fn()
                    except Exception: pass
        return []
    def stop(s):
        s._closed = True
        if s._qm:
            for n in ("stop","close"):
                fn = getattr(s._qm, n, None)
                if callable(fn):
                    try: fn(); break
                    except Exception: pass
    def reopen(s): s._closed = False

class VersionsStore:
    def __init__(s, art): s.art = Path(art)
    def list_versions(s, name):
        safe = Path(name).name
        if not safe or safe in (".",".."): raise ValueError("nombre inválido")
        base = s.art / safe
        out = []
        if base.exists():
            st = base.stat()
            out.append({"version": 1, "path": str(base),
                        "mtime": st.st_mtime, "size": st.st_size})
        for f in sorted(s.art.glob(f"{safe}.v*")):
            m = re.search(r"\.v(\d+)$", f.name)
            if m:
                st = f.stat()
                out.append({"version": int(m.group(1))+1, "path": str(f),
                            "mtime": st.st_mtime, "size": st.st_size})
        return out

task_store = TaskStore()
feedback_store = FeedbackStore()
queue_bridge = QueueBridge()
versions_store = VersionsStore(_ART)
ext_router = APIRouter()

class FeedbackBody(BaseModel):
    message_id: str; value: str; comment: str = ""

@ext_router.post("/v1/feedback")
async def post_feedback(b: FeedbackBody):
    if b.value not in ("up","down"):
        raise HTTPException(400, "value debe ser up|down")
    feedback_store.record(b.message_id, b.value, b.comment)
    return {"ok": True, "message_id": b.message_id, "value": b.value}

@ext_router.get("/v1/tasks/{task_id}")
async def get_task(task_id: str):
    t = task_store.get(task_id)
    if not t: raise HTTPException(404, "task not found")
    return t

@ext_router.post("/v1/tasks/{task_id}/cancel")
async def cancel_task(task_id: str):
    t = task_store.cancel(task_id)
    if not t: raise HTTPException(404, "task not found")
    return t

@ext_router.post("/v1/tasks/{task_id}/resume")
async def resume_task(task_id: str):
    t = task_store.resume(task_id)
    if not t: raise HTTPException(404, "task not found")
    return t

@ext_router.get("/v1/tasks")
async def list_tasks(status: Optional[str] = None, limit: int = 100):
    return {"items": task_store.list(status, limit)}

@ext_router.get("/v1/queue")
async def get_queue(): return queue_bridge.snapshot()

@ext_router.get("/v1/queue/dead-letter")
async def get_dlq(): return {"items": queue_bridge.dead_letter()}

@ext_router.post("/v1/queue/stop")
async def stop_queue():
    queue_bridge.stop(); return {"ok": True, "state": "closed"}

@ext_router.post("/v1/queue/reopen")
async def reopen_queue():
    queue_bridge.reopen(); return {"ok": True, "state": "open"}

@ext_router.get("/v1/artifacts/{name}/versions")
async def get_versions(name: str):
    try: return {"name": name, "versions": versions_store.list_versions(name)}
    except ValueError as e: raise HTTPException(400, str(e))
