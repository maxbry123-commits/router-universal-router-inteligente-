"""Adapter MCP App v6: MCP existente + payload UI embebible.

No planifica ni modifica DAGs; solo adapta la salida de un servidor MCP a un
contrato UI explícito y fail-closed.
"""
from __future__ import annotations

from dataclasses import dataclass

from red.conectores import ConectorMCP


@dataclass
class ConectorMCPApp(ConectorMCP):
    """Extiende ConectorMCP con renderizado de UI HTML/JSON validado."""

    async def renderizar_ui(self, payload: dict) -> dict:
        """Ejecuta MCP y devuelve únicamente una representación UI permitida."""
        result = await self.enviar(payload)
        if result.get("status") != "DONE":
            return result

        output = result.get("output", {})
        if not isinstance(output, dict):
            return {"status": "FAIL", "error": "ui_output_debe_ser_objeto"}

        html = output.get("html")
        ui_json = output.get("ui")
        if html is None and ui_json is None:
            return {"status": "FAIL", "error": "ui_payload_ausente"}
        if html is not None and not isinstance(html, str):
            return {"status": "FAIL", "error": "ui_html_debe_ser_texto"}
        if ui_json is not None and not isinstance(ui_json, dict):
            return {"status": "FAIL", "error": "ui_json_debe_ser_objeto"}

        return {
            "status": "DONE",
            "output": {"html": html, "ui": ui_json},
        }
