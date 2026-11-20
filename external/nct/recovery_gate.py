"""recovery_gate.py — Validacion schema Recovery State (NCT/APEX)"""
import json, logging
from typing import Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)
REQUIRED_FIELDS = {"version", "entries"}

def validate_recovery_state(state: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(state, dict):
        return {"valido": False, "error": "state no es dict"}
    faltantes = REQUIRED_FIELDS - set(state.keys())
    if faltantes:
        return {"valido": False, "faltantes": sorted(faltantes)}
    if not isinstance(state.get("entries"), list):
        return {"valido": False, "error": "entries no es lista"}
    return {"valido": True, "total_entries": len(state["entries"])}

def load_or_default(path: str = "./state/handoff.json") -> Dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {"version": "1.0.0", "entries": []}
    try:
        with open(p, "r", encoding="utf-8") as f:
            state = json.load(f)
        v = validate_recovery_state(state)
        if v["valido"]:
            return state
        logger.warning("State invalido, usando default: %s", v)
    except Exception as e:
        logger.warning("No se pudo cargar state: %s", e)
    return {"version": "1.0.0", "entries": []}
