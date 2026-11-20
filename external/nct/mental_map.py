"""mental_map.py — 10 vistas + madurez desde handoff (NCT/APEX)"""
import logging
from typing import Dict, Any
from . import handoff as H
from . import crazy_wall as W

logger = logging.getLogger(__name__)

VISTAS = ["arquitectura", "code", "tests", "docs", "seguridad",
          "persistencia", "integracion", "observabilidad", "despliegue", "owner"]

def calcular_madurez() -> Dict[str, Any]:
    snap = H.HANDOFF.snapshot(last_n=50)
    total = snap["total_entries"]
    tainted = len(W.WALL.tainted_entries(limit=200))
    wall_size = W.WALL.size()
    score = 0
    if total >= 5:
        score += 20
    if total >= 20:
        score += 20
    if tainted == 0:
        score += 20
    elif tainted < 5:
        score += 10
    if wall_size["lines"] >= 10:
        score += 20
    if wall_size["lines"] >= 50:
        score += 20
    return {"score": min(score, 100), "handoff_total": total,
            "wall_lines": wall_size["lines"], "tainted_entries": tainted,
            "nivel": ("INICIAL" if score < 30
                      else "BASICO" if score < 60
                      else "AVANZADO" if score < 85 else "MADURO")}

def vista(nombre: str, madurez: Dict[str, Any]) -> Dict[str, Any]:
    if nombre not in VISTAS:
        return {"error": f"vista desconocida: {nombre}", "validas": VISTAS}
    return {"vista": nombre, "score_global": madurez["score"],
            "nivel": madurez["nivel"],
            "datos": {"handoff_total": madurez["handoff_total"],
                      "wall_lines": madurez["wall_lines"],
                      "tainted": madurez["tainted_entries"]}}

def todas_las_vistas() -> Dict[str, Any]:
    mad = calcular_madurez()
    return {"madurez": mad, "vistas": {v: vista(v, mad) for v in VISTAS}}
