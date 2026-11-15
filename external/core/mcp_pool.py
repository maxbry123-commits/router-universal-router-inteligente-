"""mcp_pool.py — Pool de conexiones HTTP para el Harness DeepSeek y MCP Memory."""
import os
import httpx
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

class MCPPool:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(MCPPool, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, pool_size: int = 10):
        if getattr(self, "_initialized", False):
            return
        self.pool_size = pool_size
        self.limits = httpx.Limits(max_connections=pool_size, max_keepalive_connections=pool_size)
        self.timeout = httpx.Timeout(60.0, connect=10.0)
        self._client: Optional[httpx.AsyncClient] = None
        self._initialized = True

    async def get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(limits=self.limits, timeout=self.timeout)
        return self._client

    async def close(self):
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()

    async def post(self, url: str, headers: Dict[str, str], payload: Dict[str, Any]) -> Dict[str, Any]:
        client = await self.get_client()
        try:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"MCPPool POST failed to {url}: {e}")
            return {"error": str(e)}
