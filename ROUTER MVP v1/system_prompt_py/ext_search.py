"""Ficha 017 · búsqueda y exportación del histórico del chat. Aditivo."""
from __future__ import annotations
import json, os
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import PlainTextResponse

_ART = Path(os.environ.get("ARTIFACT_DIR", "artifacts"))
_ROOT = _ART.parent if str(_ART.parent) else Path(".")
_TASKS = _ROOT / ".tasks"

ext_search = APIRouter()

def _iter_messages():
    if not _TASKS.exists():
        return
    for p in sorted(_TASKS.glob("t-*.json")):
        try:
            rec = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        payload = rec.get("payload") or {}
        for m in (payload.get("messages") or []):
            content = m.get("content") or ""
            if not isinstance(content, str):
                continue
            yield {
                "task_id": rec.get("task_id") or p.stem,
                "created_at": rec.get("created_at"),
                "status": rec.get("status"),
                "role": m.get("role") or "user",
                "content": content,
            }

@ext_search.get("/v1/chat/search")
async def chat_search(
    q: str = Query(..., min_length=1, description="texto a buscar"),
    limit: int = Query(50, ge=1, le=500),
    task_id: Optional[str] = Query(None, description="filtrar por task"),
    role: Optional[str] = Query(None, description="user|assistant|system"),
):
    ql = q.lower()
    hits = []
    for m in _iter_messages():
        if task_id and m["task_id"] != task_id:
            continue
        if role and m["role"] != role:
            continue
        if ql in (m["content"] or "").lower():
            hits.append(m)
    return {"q": q, "count": len(hits), "items": hits[:limit],
            "filters": {"task_id": task_id, "role": role}}

@ext_search.get("/v1/chat/export.md", response_class=PlainTextResponse)
async def chat_export(
    task_id: Optional[str] = Query(None),
    role: Optional[str] = Query(None),
):
    msgs = []
    for m in _iter_messages():
        if task_id and m["task_id"] != task_id:
            continue
        if role and m["role"] != role:
            continue
        msgs.append(m)
    if task_id and not msgs:
        raise HTTPException(404, f"task {task_id} no tiene mensajes")
    lines = ["# Conversación exportada", ""]
    if task_id:
        lines.append(f"- task_id: `{task_id}`")
    lines.append(f"- mensajes: **{len(msgs)}**")
    lines.append("")
    for m in msgs:
        lines.append(f"### {m['role']}")
        if m.get("created_at"):
            lines.append(f"_(task {m['task_id']}, ts {m['created_at']})_")
        lines.append("")
        lines.append(m["content"])
        lines.append("")
        lines.append("---")
        lines.append("")
    return "\n".join(lines)
