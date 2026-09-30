#!/usr/bin/env python3
"""Generate a hardened app.py for the Claude <-> Hugging Face MCP bridge.

Goals:
- keep Streamable HTTP stateless so Space restarts cannot invalidate session IDs;
- answer Claude's optional GET/SSE listener with HTTP 200 instead of FastMCP's
  stateless default 405;
- preserve the two existing secret routes;
- add four isolated URL slots under MCP_SECRET_HF for separate long-lived
  Claude sessions;
- remove the unused HuggingFace OAuth provider that was instantiated but never
  attached to FastMCP;
- add a non-secret /healthz endpoint for external monitoring.

This script only generates /tmp/app.py. Publishing is handled by the OIDC
workflow.
"""

from __future__ import annotations

import argparse
import py_compile
import urllib.request
from pathlib import Path

SOURCE_URL = (
    "https://huggingface.co/spaces/"
    "COMAND-CENTER-1/claude-github-mcp-backup/resolve/main/app.py"
)


def fetch_source() -> str:
    with urllib.request.urlopen(SOURCE_URL, timeout=30) as response:
        return response.read().decode("utf-8")


def remove_unused_oauth(source: str) -> str:
    source = source.replace("from fastmcp.server.auth import AuthContext\n", "")
    source = source.replace(
        "from fastmcp.server.auth.providers.huggingface import HuggingFaceProvider\n",
        "",
    )
    source = source.replace("from fastmcp.server.middleware import AuthMiddleware\n", "")

    auth_start = source.find("def _require_hf_owner(")
    mcp_start = source.find("mcp = FastMCP(")
    if auth_start != -1:
        if mcp_start == -1 or mcp_start <= auth_start:
            raise RuntimeError("OAuth removal markers are inconsistent")
        source = source[:auth_start] + source[mcp_start:]

    return source.replace(
        '"mcp_auth": "huggingface_oauth"',
        '"mcp_auth": "secret_path_stateless"',
    )


HEALTH_ROUTE = r'''
from starlette.responses import JSONResponse as _HealthJSONResponse

@mcp.custom_route("/healthz", methods=["GET"])
async def _healthz(_request):
    primary = bool(os.getenv("MCP_SECRET_PATH", "").strip())
    secondary = bool(os.getenv("MCP_SECRET_HF", "").strip())
    return _HealthJSONResponse({
        "ok": True,
        "server": "Maxbry GitHub Backup",
        "transport": "streamable-http",
        "stateless": True,
        "mcp_paths_active": int(primary) + int(secondary),
        "github_secret_present": bool(os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")),
    })

'''


MAIN_BLOCK = r'''if __name__ == "__main__":
    import asyncio
    import uvicorn
    from starlette.responses import StreamingResponse

    port = int(os.getenv("PORT", os.getenv("GRADIO_SERVER_PORT", "7860")))

    primary_secret = os.getenv("MCP_SECRET_PATH", "").strip().strip("/")
    secondary_secret = os.getenv("MCP_SECRET_HF", "").strip().strip("/")

    if len(primary_secret) < 20:
        raise RuntimeError(
            "MCP_SECRET_PATH requerido y debe tener al menos 20 caracteres"
        )
    if secondary_secret and len(secondary_secret) < 20:
        raise RuntimeError(
            "MCP_SECRET_HF debe tener al menos 20 caracteres"
        )

    primary_path = f"/{primary_secret}/mcp"

    alias_paths = []
    if secondary_secret and secondary_secret != primary_secret:
        # Existing recovery bridge.
        alias_paths.append(f"/{secondary_secret}/mcp")

        # Separate URLs for separate long-lived Claude sessions. Anthropic has
        # documented/reported cases where one remote MCP session can disturb
        # another session using the same server identity.
        for slot in range(1, 5):
            alias_paths.append(f"/{secondary_secret}/slot-{slot}/mcp")

    mcp_http_app = mcp.http_app(
        path=primary_path,
        stateless_http=True,
    )

    class _ClaudeMCPCompat:
        """Stateless MCP with GET/SSE compatibility and isolated URL aliases."""

        def __init__(self, app, aliases, target):
            self.app = app
            self.aliases = set(aliases)
            self.target = target
            self.mcp_paths = {target, *self.aliases}

        async def __call__(self, scope, receive, send):
            if scope.get("type") == "http":
                path = scope.get("path", "")
                trailing = path.endswith("/")
                normalized = (
                    path[:-1]
                    if trailing and len(path) > 1
                    else path
                )

                # Some Claude/Anthropic remote MCP clients open the optional
                # GET listening stream. FastMCP 3.4.7 stateless mode returns
                # 405 for GET, and affected Claude versions can treat that 405
                # as a fatal disconnect. Answer with a harmless SSE keepalive.
                if (
                    scope.get("method") == "GET"
                    and normalized in self.mcp_paths
                ):
                    async def _events():
                        yield b": connected\n\n"
                        while True:
                            await asyncio.sleep(15)
                            yield b": keepalive\n\n"

                    response = StreamingResponse(
                        _events(),
                        status_code=200,
                        media_type="text/event-stream",
                        headers={
                            "Cache-Control": "no-cache, no-transform",
                            "X-Accel-Buffering": "no",
                        },
                    )
                    await response(scope, receive, send)
                    return

                if normalized in self.aliases:
                    scope = dict(scope)
                    rewritten = self.target + ("/" if trailing else "")
                    scope["path"] = rewritten
                    scope["raw_path"] = rewritten.encode("utf-8")

            await self.app(scope, receive, send)

    app = _ClaudeMCPCompat(
        mcp_http_app,
        alias_paths,
        primary_path,
    )

    print(f"MCP_PATHS_ACTIVE={1 + len(alias_paths)}")
    print("CLAUDE_GET_SSE_COMPAT=enabled")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        timeout_keep_alive=120,
    )
'''


def build(source: str) -> str:
    source = remove_unused_oauth(source)

    marker = 'if __name__ == "__main__":'
    if marker not in source:
        raise RuntimeError("main block not found")

    head = source.split(marker, 1)[0]
    if '@mcp.custom_route("/healthz"' not in head:
        head += HEALTH_ROUTE

    patched = head + MAIN_BLOCK

    required = (
        "stateless_http=True",
        "MCP_SECRET_PATH",
        "MCP_SECRET_HF",
        "_ClaudeMCPCompat",
        "StreamingResponse",
        '@mcp.custom_route("/healthz"',
    )
    for item in required:
        if item not in patched:
            raise RuntimeError(f"missing expected marker: {item}")

    if "HuggingFaceProvider" in patched:
        raise RuntimeError("unused OAuth provider still present")

    return patched


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="/tmp/app.py")
    args = parser.parse_args()

    patched = build(fetch_source())
    output = Path(args.output)
    output.write_text(patched, encoding="utf-8")
    py_compile.compile(str(output), doraise=True)

    print("PATCH_OK")
    print("STATELESS=1")
    print("CLAUDE_GET_SSE_COMPAT=1")
    print("ISOLATED_SLOTS=4")
    print("UNUSED_OAUTH_REMOVED=1")
    print(f"OUTPUT={output}")


if __name__ == "__main__":
    main()
