"""capa_api.py — Backend de paneles (cola, watchdog, mindmap, motion)."""
import asyncio
import logging
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

logger = logging.getLogger(__name__)
app = FastAPI(title="capa-api")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:7861", "http://127.0.0.1:7861"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

API_KEY = None
_router = None
_queue = None


def configure(router, queue, api_key: str):
    global _router, _queue, API_KEY
    _router, _queue, API_KEY = router, queue, api_key


def _check(key: str):
    if API_KEY and key != API_KEY:
        raise HTTPException(401, "unauthorized")


@app.get("/capa/status")
async def status(x_api_key: str = Header(None)):
    _check(x_api_key)
    snap = {"queued": 0, "running": 0, "high": 0, "normal": 0,
            "low": 0, "ram_pct": 0, "skips_by_ram": 0}
    try:
        from external.hf.space_queue import SPACE_QUEUE
        snap = await SPACE_QUEUE.snapshot()
    except Exception:
        pass
    handoff_total = 0
    wall_lines = 0
    try:
        from external.nct import handoff
        handoff_total = handoff.HANDOFF.snapshot(last_n=1)["total_entries"]
    except Exception:
        pass
    try:
        from external.nct import crazy_wall
        wall_lines = crazy_wall.WALL.size()["lines"]
    except Exception:
        pass
    return {
        "workers": {},
        "queue_size": snap.get("queued", 0),
        "active_tasks": [],
        "high": snap.get("high", 0),
        "normal": snap.get("normal", 0),
        "low": snap.get("low", 0),
        "ram_pct": snap.get("ram_pct", 0),
        "skips_by_ram": snap.get("skips_by_ram", 0),
        "pending_approvals": [],
        "handoff_total": handoff_total,
        "wall_lines": wall_lines,
        "uptime": "ok",
    }


@app.get("/health")
def health():
    return {"status": "ok"}


def run(host: str = "0.0.0.0", port: int = 7861):
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run()
