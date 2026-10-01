"""Single Router loader for the memory_yaiwes package."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from .memory_runtime import memory, scope_for
from .router import _auth, get_store


class MemorySave(BaseModel):
    scope: str = Field(min_length=1, max_length=80)
    key: str = Field(min_length=1, max_length=200)
    data: Any


def build_memory_router() -> APIRouter:
    router = APIRouter()

    @router.get("/memoria/health")
    def health(_owner: str = Depends(_auth)) -> dict[str, Any]:
        try:
            return memory(get_store()).health()
        except Exception as exc:  # noqa: BLE001 - fail closed without taking Router down
            return {"schema": "yaiwes.memory/v1", "fallback": "sqlite", "status": "GAP", "error": type(exc).__name__}

    @router.post("/memoria/save")
    def save(req: MemorySave, owner: str = Depends(_auth)) -> dict[str, Any]:
        try:
            result = memory(get_store()).save(scope_for(owner, req.scope), req.key, req.data)
            return {**result, "scope": req.scope}
        except (ValueError, TypeError) as exc:
            raise HTTPException(status_code=400, detail="MEMORY_SAVE_INVALID") from exc
        except Exception as exc:
            raise HTTPException(status_code=503, detail="MEMORY_SAVE_UNAVAILABLE") from exc

    @router.get("/memoria/load")
    def load(scope: str, key: str, owner: str = Depends(_auth)) -> dict[str, Any]:
        records = memory(get_store()).load(scope_for(owner, scope), key)
        return {"scope": scope, "key": key, "records": [{**row, "scope": scope} for row in records]}

    @router.get("/memoria/search")
    def search(scope: str, query: str, k: int = 10, owner: str = Depends(_auth)) -> dict[str, Any]:
        return {"scope": scope, "query": query, "results": memory(get_store()).search(
            scope_for(owner, scope), query, max(1, min(k, 100)))}

    return router
