"""S2 — Micro-sistema por agente.

Crea, para cada miembro de staff.yaml, su carpeta con CLAUDE.md, MEMORIA.md, SKILLS.md, HANDOFF.md e inbox/.
Idempotente: no pisa lo que ya escribió un humano (solo crea lo que falta) salvo --forzar.

Uso: python3 "chat router/runtime/micro_sistema.py" [--forzar]
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from staff_registry import REPO, STAFF_DIR, miembros

PLANTILLAS = {
    "CLAUDE.md": """# {nombre} — contrato operativo
- id: `{id}` · rol: `{rol}` · componente: `{componente}`
- Ruta de IA: NVIDIA (Kimi) -> Cerebras -> Groq -> DeepSeek V4 Flash. **Sin API de Anthropic.**
- Todas las llamadas salen por el Router (`chat router/runtime/router_client.py`). Prohibido llamar a un proveedor directamente.
- No inventar: lo no resuelto se anota como GAP en HANDOFF.md.
- Un nodo solo cierra con prueba real (respuesta recibida, archivo verificado, captura).

## Prompt de sistema
{prompt}
""",
    "MEMORIA.md": """# Memoria de {nombre}
Hechos verificados (append-only). Respaldo en Memanto/Graphiti/Graphify.

| fecha | hecho | evidencia |
|---|---|---|
""",
    "SKILLS.md": """# Skills de {nombre}
| skill | entrada | salida | cierre |
|---|---|---|---|
| responder_orden | orden en texto | respuesta del Router | respuesta real recibida |
""",
    "HANDOFF.md": """# Handoff de {nombre}
Actualizado: {fecha}

## Estado
- Componente descargado: `{componente}`
- Conectado al Router: pendiente de `registrar_staff.py`

## GAPs
- (vacío)
""",
}


def escribir(path: Path, texto: str, forzar: bool) -> bool:
    if path.exists() and not forzar:
        return False
    path.write_text(texto, encoding="utf-8")
    return True


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--forzar", action="store_true")
    args = ap.parse_args()
    fecha = time.strftime("%Y-%m-%d", time.gmtime())
    creados, saltados = [], []
    for m in miembros():
        base = STAFF_DIR / m["id"]
        (base / "inbox").mkdir(parents=True, exist_ok=True)
        ctx = {**m, "componente": m.get("componente") or "(sin componente propio: corre dentro del Router)", "fecha": fecha}
        for nombre_archivo, plantilla in PLANTILLAS.items():
            destino = base / nombre_archivo
            (creados if escribir(destino, plantilla.format(**ctx), args.forzar) else saltados).append(
                str(destino.relative_to(REPO)))
        gk = base / "inbox" / ".gitkeep"
        if not gk.exists():
            gk.write_text("", encoding="utf-8")
    print(json.dumps({"nodo": "S2_micro_sistema_por_agente", "creados": len(creados), "ya_existian": len(saltados),
                      "carpeta": str(STAFF_DIR.relative_to(REPO))}, ensure_ascii=False))


if __name__ == "__main__":
    main()
