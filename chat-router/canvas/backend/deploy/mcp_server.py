#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MCP HTTP · shim de compatibilidad · yaiwes.node/v2

POR QUE ESTE FICHERO SIGUE EXISTIENDO: el servidor MCP real ya no es un
http.server de la stdlib en el puerto 8078. Ahora es un APIRouter de FastAPI
(backend/mcp_router.py) montado dentro de backend/api.py: un solo proceso, un
solo CORS, un solo ciclo de vida (refutacion 1 de la auditoria).

Este modulo NO arranca nada: reexporta la API real para que cualquier
importador antiguo (o el arnés de pruebas) siga funcionando, y avisa por stderr
si alguien intenta ejecutarlo como servidor standalone.

    python3 mcp_server.py --port 8078   -> aviso y salida 2 (usa la app FastAPI)
    from mcp_server import handle_rpc    -> funciona (delega en mcp_router)
"""

from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.abspath(os.path.join(HERE, ".."))
for path in (BACKEND_DIR, HERE):
    if path not in sys.path:
        sys.path.insert(0, path)

from mcp_router import (  # noqa: E402,F401  (reexportado a proposito)
    PROTOCOL_VERSION,
    SERVER_NAME,
    SERVER_VERSION,
    TOOL_CATALOG,
    WINDOW_ALLOWLIST,
    WINDOW_NAMES,
    handle_rpc,
    router,
)

__all__ = [
    "PROTOCOL_VERSION", "SERVER_NAME", "SERVER_VERSION", "TOOL_CATALOG",
    "WINDOW_ALLOWLIST", "WINDOW_NAMES", "handle_rpc", "router", "main",
]


def main(argv=None) -> int:
    """El servidor standalone ya no existe: el MCP vive dentro de la app FastAPI."""
    sys.stderr.write(
        "[mcp] AVISO: el servidor MCP standalone esta RETIRADO.\n"
        "[mcp] El MCP ahora es un APIRouter de FastAPI en backend/mcp_router.py,\n"
        "[mcp] montado en backend/api.py. Arranca la app (un solo proceso):\n"
        "[mcp]     python3 -m uvicorn api:app --host 0.0.0.0 --port 7860\n"
        "[mcp] y usa POST /mcp (misma app, mismo origen).\n"
    )
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
