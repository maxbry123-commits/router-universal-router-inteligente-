"""harness_wiring.py — Conecta el Router LLM HF con el Harness y Memoria.
FAIL_CLOSED: si la URL no esta configurada, se lanza el error; nunca se devuelve
un mensaje falso tipo {"error": ...} que el llamante pueda leer como exito.
"""
import os
import logging
from external.core.mcp_pool import MCPPool

logger = logging.getLogger(__name__)

class HarnessClient:
    """Cliente del Harness DeepSeek y del banco de memoria.

    FAIL_CLOSED (contrato del modulo): cualquier fallo de red o de HTTP se
    lanza como RuntimeError. Nunca se devuelve {"error": ...} al llamante,
    que podria leerlo como un exito. MCPPool.post traga las excepciones y
    devuelve {"error": ...}, por eso aqui se usa el cliente del pool
    directamente con raise_for_status.
    """

    def __init__(self):
        self.pool = MCPPool(pool_size=10)
        self.harness_url = os.getenv("AGENT_HARNESS_URL", "")
        self.memory_url = os.getenv("MCP_MEMORY_URL", "")
        self.memory_http_url = os.getenv("MCP_MEMORY_HTTP_URL", "")
        self.api_key = os.getenv("ROUTER_API_KEY", "")

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

    def _memory_endpoint(self) -> str:
        """Endpoint HTTP del banco de memoria ('' si no hay uno usable).

        MCP_MEMORY_URL apunta al bucket (hf://...), que no es HTTP: para el
        POST hace falta MCP_MEMORY_HTTP_URL (o un MCP_MEMORY_URL http/s).
        """
        for candidate in (self.memory_http_url, self.memory_url):
            if candidate and candidate.lower().startswith(("http://", "https://")):
                return candidate.rstrip("/")
        return ""

    async def _post(self, url: str, payload: dict, timeout: float = 30.0) -> dict:
        """POST fail-closed: levanta RuntimeError si algo falla."""
        from external.core.mcp_pool import get_pool

        pool = get_pool()
        try:
            client = await pool.get_client()
            resp = await client.post(url, headers=self._headers(), json=payload, timeout=timeout)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            raise RuntimeError(f"POST {url} fallo: {type(e).__name__}: {e}") from e

    async def send_checkpoint(self, payload: dict) -> dict:
        """Persiste el checkpoint de la conversacion.

        · Con endpoint HTTP (MCP_MEMORY_HTTP_URL, o MCP_MEMORY_URL http/s):
          POST real contra {endpoint}/checkpoint, fail-closed.
        · Sin endpoint HTTP (caso normal: MCP_MEMORY_URL = hf://bucket): se
          guarda en el almacen local durable (state/pending_sync) y se encola
          para sincronizar con la HF cuando este disponible. Se devuelve el
          recibo REAL de donde quedo, nunca un exito inventado.
        """
        endpoint = self._memory_endpoint()
        if endpoint:
            url = f"{endpoint}/checkpoint"
            return await self._post(url, payload)

        import hashlib
        import json
        from pathlib import Path

        raw = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str)
        cid = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
        pending_dir = Path(os.getenv("PENDING_SYNC_DIR", "state/pending_sync"))
        pending_dir.mkdir(parents=True, exist_ok=True)
        target = pending_dir / f"{cid}.json"
        tmp = target.with_suffix(".tmp")
        tmp.write_text(raw, encoding="utf-8")
        os.replace(tmp, target)
        logger.warning(
            "[memoria] MCP_MEMORY_URL no es HTTP: checkpoint encolado en %s. "
            "Define MCP_MEMORY_HTTP_URL para sincronizarlo al banco de HF.", target
        )
        return {
            "stored": "local_pending_sync",
            "path": str(target),
            "synced": False,
            "reason": "MCP_MEMORY_URL no es HTTP: falta MCP_MEMORY_HTTP_URL",
        }

    async def ask_harness(self, payload: dict) -> dict:
        if not self.harness_url:
            raise RuntimeError("AGENT_HARNESS_URL no configurada: Harness DeepSeek obligatorio (fail-closed)")
        url = f"{self.harness_url.rstrip('/')}/execute"
        return await self._post(url, payload)


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

    # FIX (MINIMAX 2E): la mejora m3 de apply_improvements_v5.py habia quitado el
    # fallback a ROUTER_API_KEY, dejando el harness inutilizable en los Spaces
    # (alli solo se inyecta ROUTER_API_KEY). Error y codigo vuelven a cuadrar.
    key = os.getenv("HARNESS_KEY") or os.getenv("ROUTER_API_KEY", "")
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
