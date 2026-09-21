"""RIU Chat MVP app: certified HF gateway routes plus the chat API, Secret Bank, Wordflow fleet, parallel jobs and policy routing.

Run: uvicorn integration.chat_mvp.app:app --host 0.0.0.0 --port 7860
"""
from __future__ import annotations

from fastapi import FastAPI

from ..huggingface import fastapi_gateway as gateway
from . import wordflow_agents
from .jobs import build_jobs_router
from .route_api import build_route_router
from .router import build_router, get_store
from .vault_api import build_vault_router

app = FastAPI(title="Router Inteligente Universal - Chat MVP", version="0.3.0")


@app.on_event("startup")
def _seed_wordflow_fleet() -> None:
    wordflow_agents.seed(get_store())


app.include_router(build_router())  # first: its /chat serves the MVP UI
app.include_router(build_vault_router())  # /vault: Secret Bank unlock in memory
app.include_router(build_jobs_router())  # /chat/jobs/run: parallel agent jobs
app.include_router(build_route_router())  # /chat/route + /chat/router/status: resilient policy routing
app.include_router(gateway.app.router)  # /health, /v1/models, /v1/chat/completions, /chat/models
