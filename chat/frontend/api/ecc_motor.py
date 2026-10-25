#!/usr/bin/env python3
# Motor del LOOP. Ejecuta un componente de ecc-loop.json. No usa shell ni skills.
import json
from pathlib import Path

SPEC = json.loads(Path(__file__).with_name("ecc-loop.json").read_text(encoding="utf-8"))


def anotar(e, extra):
    item = extra["nota"] + ": " + str(extra.get("disparo") or "")[:80]
    traza = list(e.get("traza") or []) + [item]
    out = dict(e)
    out.update(extra)
    out["traza"] = traza[-4:]
    return out


def paso(e):
    comps = {c["fase"]: c for c in SPEC["componentes"]}
    fase = e.get("fase") if e.get("fase") in comps else "objetivo"
    c = comps[fase]
    tareas = [s.strip() for s in str(e.get("tareas") or "").splitlines() if s.strip()]
    hecho = int(e.get("hecho") or 0)
    if c["op"] == "exigir":
        valor = str(e.get(c["campo"]) or "").strip()
        if not valor:
            return {**e, "on": True, "fase": fase, "nota": c["falta"], "disparo": ""}
        return anotar(e, {"on": True, "fase": c["siguiente"], "nota": c["id"], "disparo": valor[:180]})
    if c["op"] == "tomar":
        if not tareas or hecho >= len(tareas):
            return {**e, "on": True, "fase": fase, "nota": c["falta"], "disparo": ""}
        return anotar(e, {"on": True, "fase": c["siguiente"], "nota": c["id"], "disparo": tareas[hecho][:180]})
    if not e.get("disparo"):
        return {**e, "on": True, "fase": fase, "nota": c["falta"]}
    hecho2 = hecho + 1
    n = int(e.get("paso") or 0) + 1
    if n >= int(SPEC["tope"]):
        return anotar(e, {"on": False, "fase": "apagado", "paso": n, "hecho": hecho2, "nota": "tope", "disparo": e.get("disparo") or ""})
    nota = "vuelta completa" if hecho2 >= len(tareas) else c["id"]
    return anotar(e, {"on": True, "fase": c["siguiente"], "paso": n, "hecho": hecho2, "nota": nota, "disparo": e.get("disparo") or ""})


if __name__ == "__main__":
    print(json.dumps(paso(json.load(__import__("sys").stdin)), ensure_ascii=False))
