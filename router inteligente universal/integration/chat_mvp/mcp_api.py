"""MCP del Router (Director 2026-10-03): cualquier agente/software se conecta al UNICO Router por MCP sin tocar su codigo.

URL: <Router>/mcp/  (streamable HTTP, sin estado). Auth: X-API-Key o Authorization: Bearer <clave del Router> (misma que /chat).
Herramientas: chat por grupo o proveedor:modelo, catalogo, fichas (listar/crear/correr), laboratorio, memoria,
almacenamiento HF y computo HF (Jobs). Todo llama las mismas funciones internas que las rutas HTTP.
"""
from __future__ import annotations

import asyncio
import contextlib
import os
from typing import Any

try:  # mcp 2.x
    from mcp.server.mcpserver import MCPServer as _Server
except ImportError:  # mcp 1.x
    from mcp.server.fastmcp import FastMCP as _Server


def build_mcp():  # noqa: ANN201
    from . import control_plane as cp
    from .memory_runtime import memory
    from .openai_route import run_chat
    from .router import get_store, sync_to_bucket

    mcp = _Server("riu-router")

    @mcp.tool()
    async def router_chat(prompt: str, model: str = "auto", system: str = "", max_tokens: int = 1024) -> dict[str, Any]:
        """Pregunta al Router. model: auto | grupo | proveedor:modelo (ver router_catalog)."""
        msgs = ([{"role": "system", "content": system}] if system else []) + [{"role": "user", "content": prompt}]
        out = await asyncio.to_thread(run_chat, model, msgs, max_tokens, None, None)
        return {"route": out["route"], "content": out["message"].get("content")}

    @mcp.tool()
    async def router_catalog() -> dict[str, Any]:
        """Grupos y modelos disponibles ahora (banco + entorno)."""
        return await asyncio.to_thread(cp.catalog)

    @mcp.tool()
    async def fichas_list() -> list[dict[str, Any]]:
        """Fichas vivas guardadas."""
        store = get_store()
        cp._ftable(store)  # noqa: SLF001
        return store._all("SELECT id, version, parent, created FROM fichas ORDER BY created DESC LIMIT 200")  # noqa: SLF001

    @mcp.tool()
    async def ficha_create(ficha: dict[str, Any], base_id: str = "") -> dict[str, Any]:
        """Crea una ficha (o espejo de base_id con cambios). mode: single|queue|parallel|council; members: 1-20."""
        return cp.ficha_save(get_store(), cp.FichaReq(base_id=base_id or None, ficha=ficha))

    @mcp.tool()
    async def ficha_run(ficha_id: str, text: str) -> dict[str, Any]:
        """Ejecuta una ficha con un texto de entrada."""
        return await asyncio.to_thread(cp.ficha_run, get_store(), ficha_id, text)

    @mcp.tool()
    async def lab_run() -> dict[str, Any]:
        """Prueba todas las API/SDK del banco (3 pruebas cada una, sin mostrar claves) y guarda el informe."""
        return await asyncio.to_thread(cp.lab_run)

    @mcp.tool()
    async def lab_last() -> dict[str, Any]:
        """Ultimo informe del laboratorio."""
        return cp.lab_last() or {"status": "SIN_INFORMES"}

    @mcp.tool()
    async def memoria_save(scope: str, key: str, data: Any) -> dict[str, Any]:
        """Guarda en la memoria del Router."""
        return memory(get_store()).save("mcp:" + scope, key, data)

    @mcp.tool()
    async def memoria_load(scope: str, key: str) -> list[dict[str, Any]]:
        """Lee de la memoria del Router."""
        return memory(get_store()).load("mcp:" + scope, key)

    @mcp.tool()
    async def memoria_search(scope: str, query: str, k: int = 10) -> Any:
        """Busca en la memoria del Router."""
        return memory(get_store()).search("mcp:" + scope, query, k)

    @mcp.tool()
    async def almacenamiento_sync() -> dict[str, Any]:
        """Copia ya el almacenamiento del Router al bucket HF permanente."""
        bucket, token = os.getenv("HF_BUCKET_ID"), os.getenv("HF_WRITE_TOKEN") or os.getenv("HF_TOKEN") or ""
        if not bucket or not token:
            return {"status": "GAP", "reason": "HF_BUCKET_ID o token ausente"}
        return await asyncio.to_thread(sync_to_bucket, get_store(), bucket, token)

    @mcp.tool()
    async def hf_compute_run(command: list[str], image: str = "python:3.12", flavor: str = "cpu-basic", timeout: str = "30m") -> dict[str, Any]:
        """Computo HF para cualquier cosa conectada al Router (HF Job pagado)."""
        cp._check_flavor(flavor)  # noqa: SLF001
        job = cp._api().run_job(image=image, command=command, flavor=flavor, timeout=timeout)  # noqa: SLF001
        return {"job_id": job.id, "flavor": flavor}

    @mcp.tool()
    async def hf_job_status(job_id: str) -> dict[str, Any]:
        """Estado de un HF Job."""
        j = cp._api().inspect_job(job_id=job_id)  # noqa: SLF001
        return {"job_id": job_id, "stage": str(getattr(j.status, "stage", ""))}

    return mcp


class _KeyGate:
    """ASGI wrapper: only callers with a valid Router key reach the MCP app."""

    def __init__(self, app) -> None:  # noqa: ANN001
        self.app = app

    async def __call__(self, scope, receive, send):  # noqa: ANN001
        if scope.get("type") == "http":
            from ..huggingface.api_key_auth import authenticate_api_key

            headers = {k.decode().lower(): v.decode() for k, v in scope.get("headers", [])}
            auth = headers.get("authorization", "")
            cand = headers.get("x-api-key") or (auth[7:].strip() if auth.lower().startswith("bearer ") else "")
            try:
                authenticate_api_key(cand or None)
            except Exception:  # noqa: BLE001
                from starlette.responses import JSONResponse

                await JSONResponse({"detail": "RIU_API_KEY_REQUIRED"}, status_code=401)(scope, receive, send)
                return
        await self.app(scope, receive, send)


_STACK: contextlib.AsyncExitStack | None = None


def install_mcp(app) -> None:  # noqa: ANN001
    mcp = build_mcp()
    try:
        sub = mcp.streamable_http_app(streamable_http_path="/", stateless_http=True)
    except TypeError:  # mcp 1.x: settings live on the server
        mcp.settings.streamable_http_path = "/"
        mcp.settings.stateless_http = True
        sub = mcp.streamable_http_app()
    app.mount("/mcp", _KeyGate(sub))

    @app.on_event("startup")
    async def _mcp_start() -> None:
        global _STACK
        _STACK = contextlib.AsyncExitStack()
        await _STACK.enter_async_context(mcp.session_manager.run())

    @app.on_event("shutdown")
    async def _mcp_stop() -> None:
        if _STACK is not None:
            await _STACK.aclose()
