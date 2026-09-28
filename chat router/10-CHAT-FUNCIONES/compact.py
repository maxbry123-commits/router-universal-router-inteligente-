"""Compactación determinista a parche de recuperación."""
from __future__ import annotations
from typing import Any

def compactar(historial: list[Any]) -> dict[str, Any]:
    if not isinstance(historial, list):
        raise TypeError("historial debe ser list")
    objetivo = ""
    decisiones, archivos = [], []
    estado = "UNKNOWN"
    siguiente = ""
    for item in historial:
        if not isinstance(item, dict):
            continue
        objetivo = item.get("objetivo", objetivo)
        estado = item.get("estado", estado)
        siguiente = item.get("siguiente_paso", siguiente)
        decisiones.extend(item.get("decisiones", []) or [])
        archivos.extend(item.get("archivos", []) or [])
    resumen = {
        "objetivo": objetivo,
        "decisiones": list(dict.fromkeys(map(str, decisiones))),
        "archivos": list(dict.fromkeys(map(str, archivos))),
        "estado": estado,
        "siguiente_paso": siguiente,
    }
    resumen["parche_recuperacion"] = (
        f"OBJETIVO={objetivo}; ESTADO={estado}; "
        f"SIGUIENTE={siguiente}; ARCHIVOS={','.join(resumen['archivos'])}"
    )
    return resumen
