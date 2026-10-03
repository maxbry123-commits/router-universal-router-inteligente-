"""MCP server (stdio) = memory plugin for the DeepSeek Harness (mcp-client). No Router edits.
Tools proxy the Router /memoria/* routes (x-api-key) and the HF bridge. Env: RIU_ROUTER_URL, RIU_API_KEY, HF_TOKEN."""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

import httpx
try:
    from mcp.server.mcpserver import MCPServer as FastMCP  # mcp 2.x
except ImportError:  # mcp 1.x
    from mcp.server.fastmcp import FastMCP

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from memoria_yaiwes import hf_bridge  # noqa: E402

mcp = FastMCP("memoria")


def _call(method: str, path: str, **kw: Any) -> Any:
    base = os.environ.get("RIU_ROUTER_URL", "http://127.0.0.1:8000").rstrip("/")
    try:
        r = httpx.request(method, base + path, headers={"x-api-key": os.environ.get("RIU_API_KEY", "")}, timeout=20, **kw)
        return r.json() if r.status_code < 400 else {"status": "GAP", "http": r.status_code}
    except Exception as exc:  # noqa: BLE001
        return {"status": "GAP", "reason": type(exc).__name__}


@mcp.tool()
def memoria_health() -> Any:
    return _call("GET", "/memoria/health")


@mcp.tool()
def memoria_save(scope: str, key: str, data: Any) -> Any:
    return _call("POST", "/memoria/save", json={"scope": scope, "key": key, "data": data})


@mcp.tool()
def memoria_load(scope: str, key: str) -> Any:
    return _call("GET", "/memoria/load", params={"scope": scope, "key": key})


@mcp.tool()
def memoria_search(scope: str, query: str, k: int = 10) -> Any:
    return _call("GET", "/memoria/search", params={"scope": scope, "query": query, "k": k})


@mcp.tool()
def hf_memoria_health() -> Any:
    return hf_bridge.health()


@mcp.tool()
def hf_memoria_snapshot(db_path: str) -> Any:
    return hf_bridge.snapshot(db_path)


@mcp.tool()
def hf_memoria_restore_if_empty(db_path: str) -> Any:
    return hf_bridge.restore_if_empty(db_path)


if __name__ == "__main__":
    mcp.run(transport="stdio")
