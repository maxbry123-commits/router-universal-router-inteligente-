"""Contrato mínimo del adapter MCP App v6."""
from __future__ import annotations

import pytest

from red.conector_mcp_app import ConectorMCPApp
from red.connector_registry import get_connector_class


@pytest.mark.asyncio
async def test_mcp_app_renderiza_html(monkeypatch):
    connector = ConectorMCPApp("mcp-app-test", "https://example.invalid/mcp")

    async def fake_enviar(_payload):
        return {"status": "DONE", "output": {"html": "<p>ok</p>"}}

    monkeypatch.setattr(connector, "enviar", fake_enviar)
    result = await connector.renderizar_ui({"_tool": "ui"})
    assert result == {
        "status": "DONE",
        "output": {"html": "<p>ok</p>", "ui": None},
    }


@pytest.mark.asyncio
async def test_mcp_app_falla_cerrado_sin_ui(monkeypatch):
    connector = ConectorMCPApp("mcp-app-test", "https://example.invalid/mcp")

    async def fake_enviar(_payload):
        return {"status": "DONE", "output": {"other": True}}

    monkeypatch.setattr(connector, "enviar", fake_enviar)
    result = await connector.renderizar_ui({"_tool": "ui"})
    assert result == {"status": "FAIL", "error": "ui_payload_ausente"}


def test_mcp_app_registry_explicit():
    assert get_connector_class("mcp_app") is ConectorMCPApp
