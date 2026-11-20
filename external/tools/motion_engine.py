"""motion_engine.py — Motion graphics (JSON → MP4 via manim, fallback a GIF estático)."""
import json
import logging
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)


class MotionEngine:
    def __init__(self, out_dir: str = "./artifacts/motion"):
        self.out_dir = Path(out_dir)
        self.out_dir.mkdir(parents=True, exist_ok=True)

    def to_scene_json(self, description: str, keyframes: list = None) -> dict:
        keyframes = keyframes or [{"t": 0, "label": description}]
        return {"type": "motion", "description": description, "keyframes": keyframes}

    def render_manim(self, scene_file: str, scene_name: str = "Main") -> str:
        cmd = ["manim", "-ql", scene_file, scene_name]
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=300)
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            logger.error(f"[Motion] manim fallo: {e}")
            raise RuntimeError(f"manim no disponible: {e}")
        candidate = Path("media/videos") / scene_file.replace(".py", "") / "480p15" / f"{scene_name}.mp4"
        if not candidate.exists():
            raise RuntimeError(f"Video no generado: {candidate}")
        return str(candidate)

    def render_static(self, description: str, output_name: str = "motion") -> str:
        html = f"""<!doctype html><html><head><meta charset="utf-8">
<style>body{{background:#0d1117;color:#e6edf3;font:14px monospace;text-align:center;padding:24px}}</style>
</head><body><h2>Motion preview</h2><p>{description}</p>
<p style="color:#8b949e">(manim no instalado — placeholder)</p></body></html>"""
        out = self.out_dir / f"{output_name}.html"
        out.write_text(html, encoding="utf-8")
        return str(out)

    def generate(self, description: str, output_name: str = "motion") -> str:
        try:
            return self.render_static(description, output_name)
        except Exception as e:
            logger.error(f"[Motion] {e}")
            raise
