"""S4 — Cadena de trabajo del staff.

Rowboat recibe la orden -> Ruflo reparte -> Claude Code diseña -> Grok ejecuta -> Claude Code revisa
-> los 4 de Meta mejoran y prueban -> el centinela verifica -> resultado al chat + Crazy Wall.

Cada paso es una llamada por el Router (router_client). Ningún paso llama a un proveedor directamente.

Uso:
  RIU_ROUTER_URL=... RIU_ROUTER_API_KEY=... python3 "chat router/runtime/cadena.py" --orden "..."
  python3 "chat router/runtime/cadena.py" --orden "..." --ensayo   # sin proveedores: solo prueba el cableado
"""
from __future__ import annotations

import argparse
import json
import time
from typing import Any

from router_client import RouterClient, RouterError
from staff_registry import EVIDENCIA, miembro

PASOS: list[tuple[str, str]] = [
    ("rowboat", "Orden del Director:\n{orden}\n\nDivídela en subtareas numeradas con responsable."),
    ("ruflo", "Subtareas de Rowboat:\n{previo}\n\nDevuelve el flujo (nodos con dependencias y responsable)."),
    ("claude_code", "Flujo de Ruflo:\n{previo}\n\nDiseña el cambio mínimo: archivos, funciones y criterio de cierre."),
    ("grok", "Diseño de Claude Code:\n{previo}\n\nEjecuta: devuelve los comandos o el diff exacto."),
    ("claude_code", "Ejecución de Grok:\n{previo}\n\nRevísala: errores, riesgos y veredicto (APRUEBA / CORRIGE)."),
    ("muse_code", "Revisión:\n{previo}\n\nMejora el código donde haga falta."),
    ("muse_glimmer", "Mejora de Muse Code:\n{previo}\n\nDecide qué entra y corrige lo que esté mal."),
    ("metacua", "Cambio final:\n{previo}\n\nDi exactamente qué pantallas y botones hay que navegar y capturar."),
    ("cua_mcp", "Plan de pruebas de MetaCUA:\n{previo}\n\nDi qué pruebas ejecutarías y con qué resultado esperado."),
    ("centinela", "Resultado de la cadena:\n{previo}\n\nVerifica: ¿cierra con prueba real? Si no, escribe GAP: <motivo>."),
]


def ejecutar_cadena(orden: str, *, ensayo: bool = False, cliente: RouterClient | None = None) -> dict[str, Any]:
    cliente = cliente or (None if ensayo else RouterClient())
    previo = ""
    pasos: list[dict[str, Any]] = []
    for agente, plantilla in PASOS:
        mensaje = plantilla.format(orden=orden, previo=previo or "(sin salida previa)")
        inicio = time.time()
        if ensayo:
            salida = f"[ENSAYO] {miembro(agente)['nombre']} recibió {len(mensaje)} caracteres"
            paso = {"agente": agente, "ok": True, "ensayo": True, "salida": salida}
        else:
            try:
                r = cliente.preguntar(agente, mensaje, max_tokens=800)
                salida = r.get("reply") or ""
                paso = {"agente": agente, "ok": bool(salida), "proveedor": r.get("provider"),
                        "modelo": r.get("model"), "degradado": r.get("degradado"), "aviso": r.get("aviso"),
                        "salida": salida}
            except RouterError as exc:
                paso = {"agente": agente, "ok": False, "error": str(exc), "salida": ""}
                pasos.append({**paso, "segundos": round(time.time() - inicio, 2)})
                break
        pasos.append({**paso, "segundos": round(time.time() - inicio, 2)})
        previo = paso["salida"]

    completa = len(pasos) == len(PASOS) and all(p["ok"] for p in pasos)
    return {
        "schema": "yaiwes.evidencia/v1",
        "nodo": "S4_cadena_rowboat_ruflo",
        "generado": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "orden": orden,
        "ensayo": ensayo,
        "cierre": "CERRADO" if completa and not ensayo else "ABIERTO",
        "pasos": pasos,
        "resultado": previo,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--orden", required=True)
    ap.add_argument("--ensayo", action="store_true", help="prueba el cableado sin gastar proveedores")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    data = ejecutar_cadena(args.orden, ensayo=args.ensayo)
    EVIDENCIA.mkdir(parents=True, exist_ok=True)
    destino = args.out or str(EVIDENCIA / ("S4-CADENA-ENSAYO.json" if args.ensayo else "S4-CADENA.json"))
    with open(destino, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    print(json.dumps({"cierre": data["cierre"], "pasos": len(data["pasos"]), "evidencia": destino}, ensure_ascii=False))


if __name__ == "__main__":
    main()
