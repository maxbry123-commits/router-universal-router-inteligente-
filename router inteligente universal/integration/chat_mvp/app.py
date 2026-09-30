"""RIU Chat MVP app: certified HF gateway routes plus the chat API, Secret Bank, Wordflow fleet, parallel jobs and policy routing.

Run: uvicorn integration.chat_mvp.app:app --host 0.0.0.0 --port 7860
CORS: RIU_CORS_ORIGINS (comma-separated, default "*") lets the static chat (a Hugging Face Static Space) call this API from the browser; the API key
header (X-API-Key) still protects every route except the public pages.
2026-09-25 (Opus, autorizado por el Director): ui_bridge montado para el chat de Vercel (/gh/accounts, /control/*, /groups).
2026-09-26 (Opus, orden del Director): puerta /omniroute hacia OmniRoute dentro de la misma máquina HF 16 GB.
Ambos se montan dentro de try: si fallan, el Router sigue arriba sin esas rutas.
2026-09-29 (orden del Director): plugin_host montado UNA vez (/plugins) y compuerta del chat (503 "plugin chat apagado" si el plugin chat esta apagado); dentro de try.
"""
from __future__ import annotations

import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ..huggingface import fastapi_gateway as gateway
from . import wordflow_agents
from .jobs import build_jobs_router
from .route_api import build_route_router
from .router import build_router, get_store
from .vault_api import build_vault_router

app = FastAPI(title="Router Inteligente Universal - Chat MVP", version="0.3.3")
app.add_middleware(CORSMiddleware, allow_origins=[o.strip() for o in os.getenv("RIU_CORS_ORIGINS", "*").split(",") if o.strip()],
                   allow_methods=["*"], allow_headers=["*"], allow_credentials=False)


@app.on_event("startup")
def _seed_wordflow_fleet() -> None:
    wordflow_agents.seed(get_store())


_chat_deps: list = []
try:
    from ..plugin_host.api import build_plugin_router, chat_gate_dependencies

    _chat_deps = chat_gate_dependencies()  # the chat is the first plugin: its routers below get this gate
    app.include_router(build_plugin_router())  # /plugins, /plugins/{id}/enable|disable
except Exception as exc:  # never take the Router down for the Plugin Host
    _chat_deps = []
    logging.getLogger("riu").warning("plugin_host no montado: %s", exc)

app.include_router(build_router(), dependencies=_chat_deps)  # first: its /chat serves the MVP UI
app.include_router(build_vault_router())  # /vault: Secret Bank unlock in memory
app.include_router(build_jobs_router(), dependencies=_chat_deps)  # /chat/jobs/run: parallel agent jobs
app.include_router(build_route_router(), dependencies=_chat_deps)  # /chat/route + /chat/router/status: resilient policy routing
try:
    from .ui_bridge import build_ui_bridge_router

    app.include_router(build_ui_bridge_router())  # /gh/accounts, /control/*, /groups: Vercel chat
except Exception as exc:  # never take the Router down for the UI bridge
    logging.getLogger("riu").warning("ui_bridge no montado: %s", exc)
try:
    from .omniroute_proxy import build_omniroute_router
    app.include_router(build_omniroute_router())  # /omniroute/*: OmniRoute en la misma máquina
except Exception as exc:  # never take the Router down for OmniRoute
    logging.getLogger("riu").warning("omniroute_proxy no montado: %s", exc)
try:
    from .memoria_loader import build_memory_router
    app.include_router(build_memory_router())  # /memoria/*: memoria_yaiwes con fallback SQLite
except Exception as exc:  # never take the Router down for memory GAPs
    logging.getLogger("riu").warning("memoria_yaiwes no montada: %s", exc)
try:
    from ..hf_control_api import install_hf_control_plane

    install_hf_control_plane(app)  # /control/hf/*: autoscaler + pool temporal 16/32 GB
except Exception as exc:  # never take the Router down for HF control plane
    logging.getLogger("riu").warning("hf_control_plane no montado: %s", exc)

app.include_router(gateway.app.router)  # /health, /v1/models, /v1/chat/completions, /chat/models
