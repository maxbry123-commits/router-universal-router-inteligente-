"""capa_api.py — Backend de paneles (cola, watchdog, mindmap, motion).

Salida 2B (minimax-3-gh-v4B): añade lifespan con imports seguros y los
endpoints de paneles /capa/health, /capa/loop, /capa/watchdog y /capa/cola.
NO se elimina nada de la implementacion previa: configure(), run(),
/capa/status y /health se conservan intactos.
"""
import asyncio
import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/Shutdown con imports seguros: si un modulo opcional no existe,
    la API sigue levantando."""
    app.state.space_queue = None
    try:
        from external.hf.space_queue import SPACE_QUEUE
        app.state.space_queue = SPACE_QUEUE
        logger.info("[capa] SpaceQueue inicializado")
    except Exception as e:
        logger.warning(f"[capa] SpaceQueue no disponible: {e}")
    yield
    sq = getattr(app.state, "space_queue", None)
    if sq is not None:
        try:
            await sq.stop()
        except Exception as e:
            logger.warning(f"[capa] stop falló: {e}")


app = FastAPI(title="capa-api", version="1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
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
        "healthy": __import__("external.core.health_check", fromlist=["probe_all"]).probe_all().get("ok", False),
    }


@app.get("/health")
def health():
    return {"status": "ok"}


# ─── Salida 2B: endpoints de paneles ───────────────────────────────────────
@app.get("/capa/health")
async def capa_health():
    return {"ok": True, "service": "capa-api"}


@app.get("/capa/loop")
async def loop_status(x_api_key: str = Header(None)):
    _check(x_api_key)
    ckpt = os.getenv("CHECKPOINT_DIR", "state/checkpoints")
    checkpoints = os.listdir(ckpt) if os.path.exists(ckpt) else []
    return {"checkpoints": checkpoints}


@app.get("/capa/watchdog")
async def watchdog_status(x_api_key: str = Header(None)):
    _check(x_api_key)
    return {"workers": [], "active_count": 0}


@app.get("/capa/cola")
async def cola_status(x_api_key: str = Header(None)):
    _check(x_api_key)
    return await status(x_api_key)


def run(host: str = "0.0.0.0", port: int = 7861):
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run()


@app.get("/capa/env")
async def env_summary(x_api_key: str = Header(None)):
    _check(x_api_key)
    from external.core.env_config import get_env
    cfg = get_env()
    return {"masked": cfg.masked_summary(), "missing_required": cfg.validate_required()}
