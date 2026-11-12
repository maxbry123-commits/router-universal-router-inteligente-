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
def status(x_api_key: str = Header(default="")):
    _check(x_api_key)
    if _queue is None:
        return {"queue_size": 0, "active_tasks": [], "ram_pct": 0, "skips_by_ram": 0, "high": 0, "normal": 0, "low": 0}
    s = _queue.stats()
    return JSONResponse(s)


@app.get("/health")
def health():
    return {"status": "ok"}


def run(host: str = "0.0.0.0", port: int = 7861):
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run()
