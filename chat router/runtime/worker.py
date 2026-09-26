"""Worker de la cola: toma tareas y las hace pasar por la cadena del staff.

Se apaga solo tras RIU_WORKER_IDLE (def. 900 s = 15 min) sin tareas, como pide el plan.
Uso: python3 "chat router/runtime/worker.py" --clase 32gb
"""
from __future__ import annotations

import argparse
import os
import time

import cola
from cadena import ejecutar_cadena


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--clase", default="16gb", choices=["16gb", "32gb"])
    ap.add_argument("--idle", type=float, default=float(os.getenv("RIU_WORKER_IDLE", "900")))
    args = ap.parse_args()
    wid = f"local-{os.getpid()}"
    ultima = time.time()
    while time.time() - ultima < args.idle:
        t = cola.tomar(wid, args.clase)
        if not t:
            time.sleep(2.0)
            continue
        ultima = time.time()
        try:
            resultado = ejecutar_cadena(t.orden)
            cola.cerrar(t.id, resultado, ok=resultado["cierre"] == "CERRADO")
        except Exception as exc:  # noqa: BLE001 — el worker nunca muere por una tarea
            cola.cerrar(t.id, {"error": f"{type(exc).__name__}: {exc}"}, ok=False)


if __name__ == "__main__":
    main()
