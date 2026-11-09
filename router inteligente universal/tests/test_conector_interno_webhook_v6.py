import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from red.connector_registry import get_connector_class
from red.conectores import ConectorInterno, ConectorWebhook


def test_registry_resuelve_interno_y_webhook():
    assert get_connector_class("interno") is ConectorInterno
    assert get_connector_class("webhook") is ConectorWebhook


@pytest.mark.asyncio
async def test_interno_envuelve_salida_sin_status():
    async def handler(payload):
        return {"echo": payload["value"]}

    conector = ConectorInterno("interno-test", handler)
    result = await conector.enviar({"value": 7})
    assert result == {"status": "DONE", "output": {"echo": 7}}


@pytest.mark.asyncio
async def test_webhook_falla_cerrado_sin_env(monkeypatch):
    monkeypatch.delenv("ROUTER_WEBHOOK_URL", raising=False)
    conector = ConectorWebhook("webhook-test", "ROUTER_WEBHOOK_URL")
    result = await conector.enviar({"event": "test"})
    assert result == {"status": "FAIL", "error": "env_faltante:ROUTER_WEBHOOK_URL"}
    assert await conector.sondear() is False
