"""RIU Chat MVP app: certified HF gateway routes plus the chat API.

Run: uvicorn integration.chat_mvp.app:app --host 0.0.0.0 --port 7860
"""
from __future__ import annotations

from fastapi import FastAPI

from ..huggingface import fastapi_gateway as gateway
from .router import build_router

app = FastAPI(title="Router Inteligente Universal - Chat MVP", version="0.1.0")
app.include_router(build_router())  # first: its /chat serves the MVP UI
app.include_router(gateway.app.router)  # /health, /v1/models, /v1/chat/completions, /chat/models
