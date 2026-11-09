"""Single Router loader for the memory_yaiwes package."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from .router import _auth, get_store

ROOT = Path(__file__).resolve().parents[3]
PACKAGE_DIR = ROOT / "chat router" / "04-MEMORIA" / "memoria_yaiwes"
_facade: Any = None
_store_id: int | None = None


def _memory() -> Any:
    global _facade, _store_id
    store = get_store()
    if _facade is None or _store_id != id(store):
        init = PACKAGE_DIR / "__init__.py"
        spec = importlib.util.spec_from_file_location("memoria_yaiwes", init, submodule_search_locations=[str(PACKAGE_DIR)])
        if spec is None or spec.loader is None:
            raise RuntimeError("MEMORIA_PACKAGE_LOAD_FAILED")
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        _facade = module.build_memory(store)
        _store_id = id(store)
    return _facade


class MemorySave(BaseModel):
    scope: str = Field(min_length=1, max_length=80)
    key: str = Field(min_length=1, max_length=200)
    data: Any


def build_memory_router() -> APIRouter:
    router = APIRouter()

    @router.get("/memoria/health")
    def health(_owner: str = Depends(_auth)) -> dict[str, Any]:
        try:
            return _memory().health()
        except Exception as exc:  # noqa: BLE001 - fail closed without taking Router down
            return {"schema": "yaiwes.memory/v1", "fallback": "sqlite", "status": "GAP", "error": type(exc).__name__}

    @router.post("/memoria/save")
    def save(req: MemorySave, _owner: str = Depends(_auth)) -> dict[str, Any]:
        try:
            return _memory().save(req.scope, req.key, req.data)
        except (ValueError, TypeError) as exc:
            raise HTTPException(status_code=400, detail="MEMORY_SAVE_INVALID") from exc
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=503, detail="MEMORY_SAVE_UNAVAILABLE") from exc

    @router.get("/memoria/load")
    def load(scope: str, key: str, _owner: str = Depends(_auth)) -> dict[str, Any]:
        return {"scope": scope, "key": key, "records": _memory().load(scope, key)}

    @router.get("/memoria/search")
    def search(scope: str, query: str, k: int = 10, _owner: str = Depends(_auth)) -> dict[str, Any]:
        return {"scope": scope, "query": query, "results": _memory().search(scope, query, max(1, min(k, 100)))}

    return router
