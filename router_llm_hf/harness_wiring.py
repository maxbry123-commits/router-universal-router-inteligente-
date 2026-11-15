"""harness_wiring.py — Conecta el Router LLM HF con el Harness y Memoria."""
import os
import logging
from external.core.mcp_pool import MCPPool

logger = logging.getLogger(__name__)

class HarnessClient:
    def __init__(self):
        self.pool = MCPPool(pool_size=10)
        self.harness_url = os.getenv("AGENT_HARNESS_URL", "")
        self.memory_url = os.getenv("MCP_MEMORY_URL", "")
        self.api_key = os.getenv("ROUTER_API_KEY", "")

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

    async def send_checkpoint(self, payload: dict) -> dict:
        if not self.memory_url:
            return {"error": "MCP_MEMORY_URL no configurada"}
        url = f"{self.memory_url.rstrip('/')}/checkpoint"
        return await self.pool.post(url, headers=self._headers(), payload=payload)

    async def ask_harness(self, payload: dict) -> dict:
        if not self.harness_url:
            return {"error": "AGENT_HARNESS_URL no configurada"}
        url = f"{self.harness_url.rstrip('/')}/execute"
        return await self.pool.post(url, headers=self._headers(), payload=payload)
