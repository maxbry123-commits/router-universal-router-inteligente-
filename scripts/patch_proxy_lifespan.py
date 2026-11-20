"""patch_proxy_lifespan.py — Patch quirúrgico al proxy:
1. Añade `lifespan=lifespan` a la llamada FastAPI() si no existe.
2. Añade el bloque lifespan como función module-level.
3. Añade 4 endpoints /v1/loop/* si no existen.
NO borra nada existente. Si los cambios ya están, no hace nada (idempotente).
"""
import re
import os
import sys

PROXY = "ROUTER MVP v1/system_prompt_py/openai_compatible_proxy.py"

LIFESPAN_BLOCK = '''
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app):
    """Startup/Shutdown: inicializa y cierra el pool MCP."""
    try:
        from external.core.mcp_pool import get_pool
        get_pool()
    except Exception as e:
        print(f"[lifespan] pool no disponible: {e}")
    try:
        from external.tools.storage_wiring import StorageWiring
        StorageWiring.ensure_bucket()
    except Exception as e:
        print(f"[lifespan] storage_wiring: {e}")
    yield
    try:
        from external.core.mcp_pool import get_pool
        await get_pool().close()
    except Exception as e:
        print(f"[lifespan] shutdown: {e}")
'''

LOOP_ENDPOINTS_BLOCK = '''

# ─── ENDPOINTS /v1/loop/* (para el LOOP del frontend) ───
_LOOP_STATE: dict = {}

@app.get("/v1/loop/config")
async def loop_config():
    return {"max_iterations": int(os.getenv("LOOP_MAX_ITER", "8"))}

@app.post("/v1/loop/start")
async def loop_start(request: Request):
    body = await request.json()
    task_id = body.get("taskId", "default")
    _LOOP_STATE[task_id] = {"iteration": 0, "status": "running"}
    return {"ok": True, "taskId": task_id}

@app.post("/v1/loop/step")
async def loop_step(request: Request):
    body = await request.json()
    task_id = body.get("taskId", "default")
    state = _LOOP_STATE.get(task_id, {})
    if not state:
        raise HTTPException(404, f"Task {task_id} no iniciada")
    state["iteration"] = state.get("iteration", 0) + 1
    return {"ok": True, "iteration": state["iteration"], "state": state}

@app.post("/v1/loop/error")
async def loop_error(request: Request):
    body = await request.json()
    task_id = body.get("taskId", "default")
    if task_id in _LOOP_STATE:
        _LOOP_STATE[task_id]["status"] = "error"
    return {"ok": True, "logged": True}
'''


def main():
    if not os.path.exists(PROXY):
        print(f"FATAL: no existe {PROXY}", file=sys.stderr)
        sys.exit(1)

    with open(PROXY, "r", encoding="utf-8") as f:
        src = f.read()

    original_size = len(src)
    changes = []

    # 1. Añadir el bloque lifespan si no existe
    if "async def lifespan" not in src:
        # Insertar ANTES de la primera llamada FastAPI(): el kwarg lifespan=lifespan
        # se evalua al importar el modulo y necesita que lifespan ya este definida
        # (si se inserta despues -> NameError al arrancar el proxy).
        app_match = re.search(r"^.*FastAPI\(.*$", src, re.MULTILINE)
        if app_match:
            src = src[:app_match.start()] + LIFESPAN_BLOCK.strip("\n") + "\n\n" + src[app_match.start():]
            changes.append("lifespan_block_added")

    # 2. Añadir lifespan=lifespan a FastAPI() si no existe
    if "lifespan=lifespan" not in src:
        # Buscar FastAPI(...) y añadir lifespan
        src = re.sub(
            r'FastAPI\(([^)]*?)\)',
            lambda m: f'FastAPI({m.group(1)}{", " if m.group(1).strip() else ""}lifespan=lifespan)',
            src,
            count=1
        )
        changes.append("lifespan_kwarg_added")

    # 3. Añadir los endpoints /v1/loop/* si no existen
    if '/v1/loop/start' not in src:
        # Insertar antes de la línea de uvicorn.run si existe, si no al final
        uvicorn_match = re.search(r"^if __name__", src, re.MULTILINE)
        if uvicorn_match:
            src = src[:uvicorn_match.start()] + LOOP_ENDPOINTS_BLOCK + "\n\n" + src[uvicorn_match.start():]
        else:
            src = src + "\n" + LOOP_ENDPOINTS_BLOCK
        changes.append("loop_endpoints_added")

    if not changes:
        print("IDEMPOTENTE: ya estaba todo aplicado.")
        return

    with open(PROXY, "w", encoding="utf-8") as f:
        f.write(src)

    print(f"OK: {', '.join(changes)}")
    print(f"Size: {original_size} -> {len(src)} bytes")


if __name__ == "__main__":
    main()
