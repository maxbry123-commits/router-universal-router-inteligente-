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

import base64
import binascii
import hmac
import logging
import os
from pathlib import Path

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from ..huggingface import fastapi_gateway as gateway
from . import wordflow_agents
from .jobs import build_jobs_router
from .route_api import build_route_router
from .router import build_router, get_store
from .vault_api import build_vault_router

app = FastAPI(title="Router Inteligente Universal - Chat MVP", version="0.3.3")
app.mount("/chat/ui", StaticFiles(directory=Path(__file__).resolve().parents[3] / "chat router/ui"), name="chat-organization-ui")
app.add_middleware(CORSMiddleware, allow_origins=[o.strip() for o in os.getenv("RIU_CORS_ORIGINS", "*").split(",") if o.strip()],
                   allow_methods=["*"], allow_headers=["*"], allow_credentials=False)


@app.middleware("http")
async def browser_auth(request: Request, call_next):
    expected = os.getenv("RIU_ROUTER_API_KEY", "")
    authorization = request.headers.get("authorization", "")
    challenge = {"WWW-Authenticate": 'Basic realm="Router"'}
    if expected and authorization.lower().startswith("basic "):
        try:
            user, password = base64.b64decode(authorization[6:].strip(), validate=True).decode("utf-8").split(":", 1)
        except (ValueError, UnicodeDecodeError, binascii.Error):
            return Response(status_code=401, headers=challenge)
        if user != "router" or not hmac.compare_digest(password, expected):
            return Response(status_code=401, headers=challenge)
        request.scope["headers"] = [
            (name, value) for name, value in request.scope["headers"] if name.lower() != b"x-api-key"
        ] + [(b"x-api-key", expected.encode("utf-8"))]
    elif expected and request.url.path.startswith("/chat/ui/"):
        return Response(status_code=401, headers=challenge)
    response = await call_next(request)
    if expected and response.status_code == 401:
        response.headers["WWW-Authenticate"] = challenge["WWW-Authenticate"]
    return response


@app.on_event("startup")
def _seed_wordflow_fleet() -> None:
    wordflow_agents.seed(get_store())


@app.on_event("startup")
def _bucket_autosync() -> None:
    from .router import start_bucket_autosync

    start_bucket_autosync()  # HF bucket = almacenamiento permanente (restore en get_store, sync al cambiar)


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
    from .openai_route import build_openai_router

    app.include_router(build_openai_router(), dependencies=_chat_deps)  # /v1/router/*: OpenAI-compatible door for Hermes/OpenClaw (base_url=<Router>/v1/router)
except Exception as exc:  # never take the Router down for the OpenAI door
    logging.getLogger("riu").warning("openai_route no montado: %s", exc)
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

try:
    from .control_plane import build_control_router, vault_autounlock

    app.include_router(build_control_router())  # /lab/*, /fichas/*, /hf/*, /vault/autounlock: control maestro (Director 2026-10-03)

    @app.on_event("startup")
    def _vault_autounlock() -> None:
        logging.getLogger("riu").warning("banco: %s", vault_autounlock().get("status"))  # never logs values
except Exception as exc:  # never take the Router down for the control plane
    logging.getLogger("riu").warning("control_plane no montado: %s", exc)
try:
    from .mcp_api import install_mcp

    install_mcp(app)  # /mcp: MCP del Router (streamable HTTP, misma clave)
except Exception as exc:  # never take the Router down for MCP
    logging.getLogger("riu").warning("mcp no montado: %s", exc)

try:  # Conexion universal + candado + ventana status (Director 2026-10-03)
    from starlette.middleware import Middleware

    from . import secciones, tokens, ventana
    from .candado import Candado
    from .router import _auth as _riu_auth

    app.user_middleware.append(Middleware(Candado))  # el mas interno: despues de CORS y del login del navegador
    app.include_router(tokens.build_tokens_router(_riu_auth))  # /tokens, /espacio, /terminal
    app.include_router(secciones.build_secciones_router(_riu_auth))  # /secciones (fichas = secciones vivas)
    app.include_router(ventana.build_ventana_router(_riu_auth))  # /ventana

    @app.on_event("startup")
    async def _conexion_universal() -> None:
        import asyncio
        import concurrent.futures

        import anyio.to_thread

        hilos = int(os.getenv("RIU_HILOS", "1000"))
        asyncio.get_running_loop().set_default_executor(concurrent.futures.ThreadPoolExecutor(max_workers=hilos))
        anyio.to_thread.current_default_thread_limiter().total_tokens = hilos
        tokens.iniciar()
        secciones.iniciar()
        ventana.iniciar()
        from .control_plane import iniciar_banco_vivo

        iniciar_banco_vivo()
except Exception as exc:  # never take the Router down for the universal connection layer
    logging.getLogger("riu").warning("conexion universal no montada: %s", exc)

app.include_router(gateway.app.router)  # /health, /v1/models, /v1/chat/completions, /chat/models
