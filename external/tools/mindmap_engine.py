"""mindmap_engine.py — Mapa mental (estructura → HTML interactivo)."""
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class MindmapEngine:
    def __init__(self, out_dir: str = "./artifacts/mindmaps"):
        self.out_dir = Path(out_dir)
        self.out_dir.mkdir(parents=True, exist_ok=True)

    def to_tree(self, root: str, branches: list) -> dict:
        return {"root": root, "branches": branches}

    def to_html(self, tree: dict) -> str:
        def render_branch(b):
            children = b.get("children", [])
            child_html = "".join(
                f'<li>{c.get("label", c) if isinstance(c, dict) else c}</li>'
                for c in children
            )
            return f'<li><strong>{b.get("label", b)}</strong><ul>{child_html}</ul></li>'

        branches_html = "".join(render_branch(b) for b in tree["branches"])
        return f"""<!doctype html><html><head><meta charset="utf-8">
<style>
body{{background:#0d1117;color:#e6edf3;font:13px monospace;padding:16px}}
h3{{color:#58a6ff}}ul{{list-style:none;border-left:2px solid #30363d;padding-left:12px}}
li{{margin:4px 0}}strong{{color:#3fb950}}
</style></head><body>
<h3>{tree["root"]}</h3>
<ul>{branches_html}</ul>
</body></html>"""

    def generate(self, root: str, branches: list, output_name: str = "mindmap") -> str:
        tree = self.to_tree(root, branches)
        html = self.to_html(tree)
        out = self.out_dir / f"{output_name}.html"
        out.write_text(html, encoding="utf-8")
        logger.info(f"[Mindmap] {out}")
        return str(out)
