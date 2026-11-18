"""harness_wiring.py — Conecta el Router LLM HF con el Harness y Memoria.
FAIL_CLOSED: si la URL no esta configurada, se lanza el error; nunca se devuelve
un mensaje falso tipo {"error": ...} que el llamante pueda leer como exito.
"""
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
            raise RuntimeError("MCP_MEMORY_URL no configurada: checkpoint al banco de memoria obligatorio (fail-closed)")
        url = f"{self.memory_url.rstrip('/')}/checkpoint"
        return await self.pool.post(url, headers=self._headers(), payload=payload)

    async def ask_harness(self, payload: dict) -> dict:
        if not self.harness_url:
            raise RuntimeError("AGENT_HARNESS_URL no configurada: Harness DeepSeek obligatorio (fail-closed)")
        url = f"{self.harness_url.rstrip('/')}/execute"
        return await self.pool.post(url, headers=self._headers(), payload=payload)


# ─── Salida 2A: helpers de llamada al Harness (fail-closed) ───────────────
# ADAPTACION sobre el codigo del owner: el pool real del repo es
# external.core.mcp_pool.MCPPool, que NO expone `.client` (expone
# `await get_client()`) y NO tiene `get_pool()` en su version original
# (añadido en esta misma salida). Se conserva la semántica exacta:
# fail-closed si falta AGENT_HARNESS_URL o la clave, raise_for_status y
# RuntimeError en cualquier fallo (nunca un {"error": ...} leido como éxito).

async def call_harness(payload: dict, timeout: float = 60.0) -> dict:
    """Llama al Harness DeepSeek usando el pool MCP."""
    from external.core.mcp_pool import get_pool

    url = os.getenv("AGENT_HARNESS_URL")
    if not url:
        raise RuntimeError(
            "AGENT_HARNESS_URL no configurada. "
            "Configura el secret en HF o desactiva harness_wiring."
        )

    key = os.getenv("HARNESS_KEY", "")
    if not key:
        raise RuntimeError("HARNESS_KEY/ROUTER_API_KEY no configurada.")

    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }

    pool = get_pool()
    try:
        client = await pool.get_client()
        resp = await client.post(url, json=payload, headers=headers, timeout=timeout)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error(f"[harness] error: {type(e).__name__}: {e}")
        raise RuntimeError(f"Harness falló: {e}") from e


async def health_harness() -> dict:
    """Health check del Harness. No lanza excepción."""
    try:
        result = await call_harness({"messages": [{"role": "user", "content": "ping"}], "max_tokens": 5})
        return {"ok": True, "response": result}
    except Exception as e:
        return {"ok": False, "error": str(e)}
