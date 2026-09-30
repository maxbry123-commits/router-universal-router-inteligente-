"""FastAPI surface for the HF elastic worker pool."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from .chat_mvp.router import _auth
from .hf_worker_pool import POOL


def build_hf_control_router() -> APIRouter:
    r = APIRouter(prefix="/control/hf", tags=["hf-control-plane"])

    @r.get("/status")
    def status(_owner: str = Depends(_auth)) -> dict[str, Any]:
        return POOL.status()

    @r.get("/workers")
    def workers(_owner: str = Depends(_auth)) -> dict[str, Any]:
        return {"workers": POOL.status()["workers"]}

    @r.post("/workers/ensure")
    def ensure(payload: dict[str, Any] | None = None, _owner: str = Depends(_auth)) -> dict[str, Any]:
        payload = payload or {}
        flavor = str(payload.get("flavor") or "cpu-basic")
        if flavor not in {"cpu-basic", "cpu-upgrade"}:
            raise HTTPException(status_code=400, detail="flavor debe ser cpu-basic o cpu-upgrade")
        existing = POOL.choose()
        if existing:
            return {"status": "ready", "worker": existing.public()}
        try:
            worker = POOL.launch(flavor, "manual ensure")
        except Exception as exc:
            raise HTTPException(status_code=503, detail=f"{type(exc).__name__}: {str(exc)[:200]}")
        return {"status": "starting", "worker": worker.public()}

    @r.post("/invoke")
    async def invoke(payload: dict[str, Any], _owner: str = Depends(_auth)) -> dict[str, Any]:
        try:
            return await POOL.invoke(payload)
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"{type(exc).__name__}: {str(exc)[:200]}")

    return r


def install_hf_control_plane(app) -> None:  # noqa: ANN001
    app.include_router(build_hf_control_router())

    @app.on_event("startup")
    def _start() -> None:
        POOL.start()

    @app.on_event("shutdown")
    def _stop() -> None:
        POOL.stop()
