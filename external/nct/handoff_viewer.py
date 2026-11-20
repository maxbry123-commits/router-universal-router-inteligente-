"""handoff_viewer.py — Boton HANDOFF solo lectura (NCT/APEX)"""
import json, logging
from typing import Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

def view(path: str = "./state/handoff.json", last_n: int = 50) -> Dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {"exists": False, "entries": []}
    with open(p, "r", encoding="utf-8") as f:
        data = json.load(f)
    entries = data.get("entries", [])
    return {"exists": True, "total": len(entries),
            "last_n": entries[-last_n:],
            "version": data.get("version"),
            "updated_at": data.get("updated_at")}

def export_json(path: str = "./state/handoff.json") -> str:
    p = Path(path)
    if not p.exists():
        return "{}"
    with open(p, "r", encoding="utf-8") as f:
        return f.read()
