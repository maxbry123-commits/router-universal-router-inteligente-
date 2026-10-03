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
    from mcp.server.mcpserver import Context
    from mcp.server.mcpserver import MCPServer as _Server
except ImportError:  # mcp 1.x
    from mcp.server.fastmcp import Context
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
    async def ficha_create(ficha: dict[str, Any], base_id: str = "", ctx: Context = None) -> dict[str, Any]:
        """Crea una ficha (o espejo de base_id con cambios). Solo con la clave del Director (cabecera X-Director-Key)."""
        if not _director(ctx):
            return {"status": "DENEGADO", "detail": "CLAVE_DIRECTOR_REQUERIDA"}
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
    async def memoria_save(scope: str, key: str, data: Any, ctx: Context = None) -> dict[str, Any]:
        """Guarda en la memoria del Router."""
        return memory(get_store()).save(_scope(ctx, scope), key, data)

    @mcp.tool()
    async def memoria_load(scope: str, key: str, ctx: Context = None) -> list[dict[str, Any]]:
        """Lee de la memoria del Router."""
        return memory(get_store()).load(_scope(ctx, scope), key)

    @mcp.tool()
    async def memoria_search(scope: str, query: str, k: int = 10, ctx: Context = None) -> Any:
        """Busca en la memoria del Router."""
        return memory(get_store()).search(_scope(ctx, scope), query, k)

    @mcp.tool()
    async def almacenamiento_sync() -> dict[str, Any]:
        """Copia ya el almacenamiento del Router al bucket HF permanente."""
        bucket, token = os.getenv("HF_BUCKET_ID"), os.getenv("HF_WRITE_TOKEN") or os.getenv("HF_TOKEN") or ""
        if not bucket or not token:
            return {"status": "GAP", "reason": "HF_BUCKET_ID o token ausente"}
        return await asyncio.to_thread(sync_to_bucket, get_store(), bucket, token)

    @mcp.tool()
    async def hf_compute_run(command: list[str], image: str = "python:3.12", flavor: str = "cpu-basic", timeout: str = "30m",
                             ctx: Context = None) -> dict[str, Any]:
        """Computo HF pagado: token con permiso "computo" o clave del Director."""
        if not (_director(ctx) or "computo" in _permisos(ctx)):
            return {"status": "DENEGADO", "detail": "PERMISO_COMPUTO_REQUERIDO"}
        cp._check_flavor(flavor)  # noqa: SLF001
        job = cp._api().run_job(namespace=cp.JOB_NS, image=image, command=command, flavor=flavor, timeout=timeout)  # noqa: SLF001
        return {"job_id": job.id, "flavor": flavor}

    @mcp.tool()
    async def hf_job_status(job_id: str) -> dict[str, Any]:
        """Estado de un HF Job."""
        j = cp._api().inspect_job(namespace=cp.JOB_NS, job_id=job_id)  # noqa: SLF001
        return {"job_id": job_id, "stage": str(getattr(j.status, "stage", ""))}

    @mcp.tool()
    async def quien_soy(ctx: Context = None) -> dict[str, Any]:
        """Con que token/clave estoy conectado y que permisos tengo."""
        return {"dueno": _owner(ctx), "permisos": _permisos(ctx)}

    @mcp.tool()
    async def secciones_listar() -> dict[str, Any]:
        """Fichas montadas como secciones (carpeta fichas/ del Router)."""
        from .secciones import SECCIONES

        return {"secciones": SECCIONES.lista()}

    @mcp.tool()
    async def seccion_run(nombre: str, input: str, ctx: Context = None) -> dict[str, Any]:  # noqa: A002
        """Pasa un texto por todos los pasos de una seccion."""
        from .secciones import ejecutar

        return await asyncio.to_thread(ejecutar, nombre, input, _owner(ctx))

    @mcp.tool()
    async def espacio_guardar(ruta: str, texto: str, ctx: Context = None) -> dict[str, Any]:
        """Guarda un archivo de texto en el almacenamiento propio de este token."""
        from .tokens import _fs, _ruta_espacio

        await asyncio.to_thread(_fs().pipe_file, _ruta_espacio(_owner(ctx), ruta), texto.encode("utf-8"))
        return {"guardado": ruta}

    @mcp.tool()
    async def espacio_leer(ruta: str, ctx: Context = None) -> dict[str, Any]:
        """Lee un archivo de texto del almacenamiento propio de este token."""
        from .tokens import _fs, _ruta_espacio

        data = await asyncio.to_thread(_fs().cat_file, _ruta_espacio(_owner(ctx), ruta))
        return {"ruta": ruta, "texto": data.decode("utf-8", errors="replace")}

    @mcp.tool()
    async def ventana_estado() -> dict[str, Any]:
        """Estado vivo del Router: conectados, banco (sin claves), laboratorio, secciones, tokens."""
        from . import ventana

        return await asyncio.to_thread(ventana.todo)

    return mcp


def _state(ctx: Any) -> dict[str, Any]:
    try:
        return ctx.request_context.request.scope.get("state") or {}
    except Exception:  # noqa: BLE001
        return {}


def _owner(ctx: Any) -> str:
    return str(_state(ctx).get("riu_owner") or "mcp")


def _director(ctx: Any) -> bool:
    return bool(_state(ctx).get("riu_director"))


def _permisos(ctx: Any) -> list[str]:
    from .tokens import registro_de_dueno

    rec = registro_de_dueno(_owner(ctx))
    return list((rec or {}).get("permisos") or [])


def _scope(ctx: Any, scope: str) -> str:
    from .memory_runtime import scope_for

    return scope_for(_owner(ctx), scope)


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
    try:  # the public door (hf.space) and the Job URL (*.hf.jobs) are not localhost: the SDK host check would answer
        # "Invalid Host header". Off on purpose: _KeyGate below requires a Router key on every request.
        from mcp.server.transport_security import TransportSecuritySettings

        sub = mcp.streamable_http_app(streamable_http_path="/", stateless_http=True,
                                      transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False))
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
