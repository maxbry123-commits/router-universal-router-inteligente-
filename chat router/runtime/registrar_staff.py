"""S3 — Registrar todo el staff en el Router (/chat/agents) y probar una orden real por agente.

Uso:
  RIU_ROUTER_URL=http://127.0.0.1:8000 RIU_ROUTER_API_KEY=... \
  python3 "chat router/runtime/registrar_staff.py" [--probar] [--orden "texto"]

Sin --probar solo registra (no consume proveedores). Con --probar envía una orden por agente y escribe la
evidencia en chat router/EVIDENCIA/S3-CONEXION-STAFF.json. El nodo S3 solo cierra si cada agente respondió.
"""
from __future__ import annotations

import argparse
import json
import time

from router_client import RouterClient, RouterError
from staff_registry import EVIDENCIA, REPO, miembros

ORDEN_DEFECTO = "Preséntate en una frase y di cuál es tu rol en la cadena de trabajo."


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--probar", action="store_true", help="enviar una orden real por agente")
    ap.add_argument("--orden", default=ORDEN_DEFECTO)
    args = ap.parse_args()

    cliente = RouterClient()
    salud = cliente.salud()
    configurados = cliente.configurados()
    filas = []
    for m in miembros():
        fila: dict[str, object] = {"agente": m["id"], "rol": m["rol"]}
        try:
            cliente.registrar_agente(m["id"], m["nombre"], m["rol"], m["prompt"])
            fila["registrado"] = True
        except RouterError as exc:
            fila["registrado"] = False
            fila["error_registro"] = str(exc)
        if args.probar and fila["registrado"]:
            try:
                r = cliente.preguntar(m["id"], args.orden, max_tokens=120)
                fila |= {"respondio": bool(r.get("reply")), "proveedor": r.get("provider"),
                         "modelo": r.get("model"), "degradado": r.get("degradado"),
                         "respuesta": (r.get("reply") or "")[:300]}
            except RouterError as exc:
                fila |= {"respondio": False, "error_prueba": str(exc)}
        filas.append(fila)

    registrados = sum(1 for f in filas if f.get("registrado"))
    respondieron = sum(1 for f in filas if f.get("respondio"))
    data = {
        "schema": "yaiwes.evidencia/v1",
        "nodo": "S3_conectar_al_router",
        "generado": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "router": {"url": cliente.base, "health": salud, "proveedores_configurados": configurados},
        "resumen": {"agentes": len(filas), "registrados": registrados,
                    "respondieron": respondieron if args.probar else None,
                    "cierre": "CERRADO" if args.probar and respondieron == len(filas) else "ABIERTO"},
        "agentes": filas,
    }
    EVIDENCIA.mkdir(parents=True, exist_ok=True)
    destino = EVIDENCIA / "S3-CONEXION-STAFF.json"
    destino.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(data["resumen"], ensure_ascii=False))
    print("evidencia:", destino.relative_to(REPO))


if __name__ == "__main__":
    main()
