#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Validador de la COLA local (router_llm_hf/local_pool.py). FAIL_CLOSED.

Simula los 3 Spaces de Grupo 2 y comprueba las reglas del owner (paso 1):
  V1  1 peticion en vuelo por Space (nunca 2 a la vez)
  V2  si el Space preferido esta ocupado -> salta al SIGUIENTE (espejo)
  V3  si los 3 estan ocupados -> la peticion ESPERA en cola y sale cuando uno se libera
  V4  un Space que responde 503 "Loading model" se REINTENTA (no se cambia de modelo)
  V5  si un Space falla de verdad -> se penaliza y se pasa al siguiente
  V6  si los 3 fallan -> LocalPoolError (nunca un falso OK)
  V7  el estado expone libre/ocupado/cola/espejos y 1 modelo por Space
"""
import asyncio
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from router_llm_hf.local_pool import LocalPool, LocalPoolError, SPACES  # noqa: E402

FALLOS = []


def check(nombre, cond, detalle=""):
    print("  %-42s %s %s" % (nombre, "PASS" if cond else "FAIL", detalle))
    if not cond:
        FALLOS.append(nombre)


async def main():
    # ---------------- V1 + V2: 4 peticiones concurrentes, 3 Spaces
    pool = LocalPool()
    inflight = {}
    max_in_flight = {}
    en_curso = {"n": 0, "max": 0}
    served = []

    async def call(space):
        # concurrencia REAL por Space (contador que sube y baja)
        inflight[space] = inflight.get(space, 0) + 1
        en_curso["n"] += 1
        en_curso["max"] = max(en_curso["max"], en_curso["n"])
        max_in_flight[space] = max(max_in_flight.get(space, 0), inflight[space])
        await asyncio.sleep(0.25)
        inflight[space] -= 1
        en_curso["n"] -= 1
        served.append(space)
        return {"ok": True, "json": {"choices": [{"message": {"content": "ok"}}]}}

    tareas = [asyncio.ensure_future(pool.execute(call, preferred="space-grupo-2-router-llm-hf-1"))
              for _ in range(4)]
    await asyncio.sleep(0.05)
    snap = pool.snapshot()
    check("V2 el 4to espera en cola (waiting>0)", snap["waiting"] >= 1,
          "waiting=%s busy=%s" % (snap["waiting"], snap["busy"]))
    res = await asyncio.gather(*tareas)
    check("V3 los 4 exits bien", all(r.get("ok") for r in res))
    check("V1 maximo 1 en vuelo por Space", en_curso["max"] <= 3 and max(
        max_in_flight.values()) <= 1, "max_concurrente=%s por_space=%s" % (en_curso["max"], max_in_flight))
    check("V3b se repartieron los 3 Spaces", len(set(served)) == 3, "servidos=%s" % sorted(set(served)))
    check("V3c uno de ellos fue por espejo", any(r.get("mirror") for r in res))

    # ---------------- V4: 503 Loading model -> se reintenta el mismo Space
    pool2 = LocalPool()
    intentos = {"n": 0}

    async def call_cargando(space):
        intentos["n"] += 1
        if intentos["n"] < 3:
            return {"ok": False, "error": 'HTTP 503: {"error":{"message":"Loading model"}}',
                    "retryable": True}
        return {"ok": True, "json": {"choices": []}}

    r = await pool2.execute(call_cargando, preferred=SPACES[0])
    check("V4 503 Loading model se reintenta", r.get("ok") and intentos["n"] == 3
          and r.get("space") == SPACES[0],
          "intentos=%s space=%s (debe ser el PREFERIDO, no un espejo)" % (intentos["n"], r.get("space")))

    # ---------------- V5: fallo real -> penaliza y pasa al siguiente
    pool3 = LocalPool()

    async def call_malo(space):
        if space == SPACES[0]:
            return {"ok": False, "error": "HTTP 500: muerto"}
        return {"ok": True, "json": {"choices": []}}

    r = await pool3.execute(call_malo, preferred=SPACES[0])
    check("V5 Space roto -> se usa el siguiente", r.get("ok") and r.get("space") == SPACES[1],
          "space=%s mirror=%s" % (r.get("space"), r.get("mirror")))

    # ---------------- V6: los 3 fallan -> error explicito
    pool4 = LocalPool()

    async def call_todo_malo(space):
        return {"ok": False, "error": "HTTP 500: muerto"}

    try:
        await pool4.execute(call_todo_malo, preferred=SPACES[0])
        check("V6 los 3 fallan -> LocalPoolError", False, "no lanzo")
    except LocalPoolError as e:
        check("V6 los 3 fallan -> LocalPoolError", True, str(e)[:70])

    # ---------------- V7: estado
    s = pool.snapshot()
    check("V7 estado con 3 Spaces y espejos", s["total_spaces"] == 3
          and all(len(x["mirrors"]) == 2 for x in s["spaces"]), "free=%s busy=%s" % (s["free"], s["busy"]))
    check("V7b 1 modelo por Space", all(x["model"] for x in s["spaces"])
          and len({x["model"] for x in s["spaces"]}) == 3)

    if FALLOS:
        print("LOCAL_POOL_VERIFY FAIL: %s" % ",".join(FALLOS))
        return 1
    print("LOCAL_POOL_VERIFY OK (9 checks)")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
