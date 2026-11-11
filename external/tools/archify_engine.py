"""archify_engine.py — Motor de diagramación (texto/código → JSON IR → HTML)."""
import json
import logging
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)


class ArchifyEngine:
    """Convierte descripción en JSON IR y lo renderiza a HTML."""

    def __init__(self, out_dir: str = "./artifacts/diagrams"):
        self.out_dir = Path(out_dir)
        self.out_dir.mkdir(parents=True, exist_ok=True)

    def to_ir(self, description: str, nodes: list = None, edges: list = None) -> Dict[str, Any]:
        nodes = nodes or [{"id": "n1", "label": "start"}]
        edges = edges or []
        return {
            "version": "1.0",
            "type": "diagram",
            "description": description,
            "nodes": nodes,
            "edges": edges,
        }

    def to_html(self, ir: Dict[str, Any]) -> str:
        node_html = "".join(
            f'<div class="node" id="{n["id"]}">{n.get("label","")}</div>'
            for n in ir["nodes"]
        )
        edge_html = "".join(
            f'<div class="edge" data-from="{e["from"]}" data-to="{e["to"]}"></div>'
            for e in ir["edges"]
        )
        return f"""<!doctype html><html><head><meta charset="utf-8">
<style>
body{{background:#0d1117;color:#e6edf3;font:13px monospace;margin:0;padding:12px}}
.node{{background:#161b22;border:1px solid #30363d;border-radius:6px;padding:8px;margin:4px;display:inline-block}}
.edge{{width:40px;height:2px;background:#58a6ff;display:inline-block;vertical-align:middle}}
</style></head><body>
<h3>Archify — {ir["description"]}</h3>
{node_html}
{edge_html}
</body></html>"""

    def generate(self, description: str, output_name: str = "diagram") -> str:
        ir = self.to_ir(description)
        html = self.to_html(ir)
        out = self.out_dir / f"{output_name}.html"
        out.write_text(html, encoding="utf-8")
        logger.info(f"[Archify] {out}")
        return str(out)
