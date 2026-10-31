#!/usr/bin/env python3
"""Auto-evolucion de SWE CODE / SWEN CODE free: el agente deja una leccion por cada arreglo; lo que se repite se vuelve propuesta de mejora.
Solo propone cambios dentro de SWE CODE y SWE CODE free (nunca lo protegido del cableado). Uso: evolucion.py registrar '{json}' | proponer | md"""
import collections, json, os, posixpath, re, sys, time

RAIZ = os.path.dirname(os.path.abspath(__file__))
MINIMO = 3  # veces que se repite el mismo (codigo, accion) para proponerlo
DESTINOS = ("SWE CODE free/", "SWE CODE/")
POR_TIPO = {"promover_a_runbook": "SWE CODE free/INSTRUCCIONES.md", "cambiar_estrategia": "SWE CODE/web-bridge/src/sites.js"}


def _dir():
    bridge = os.environ.get("BRIDGE_STATE_DIR")  # el bridge registra aqui lo que repara solo
    d = os.environ.get("SWE_EVOLUCION_DIR") or (os.path.join(bridge, "evolucion") if bridge else os.path.join(RAIZ, "salidas", "evolucion"))
    os.makedirs(d, exist_ok=True)
    return d


def permitido(ruta):
    """Solo archivos de SWE CODE / SWE CODE free, sin saltos con .. ni rutas absolutas."""
    r = posixpath.normpath(str(ruta).replace("\\", "/"))
    return not r.startswith(("/", "..")) and ".." not in r.split("/") and r.startswith(DESTINOS) and "cableado.manifest" not in r


_SALTOS = re.compile(r"[\x00-\x1f\x7f\u0085\u2028\u2029]+")


def _limpia(v):
    """Una sola linea: saltos de linea y controles -> espacio (evita inyectar lineas en los .md)."""
    return _SALTOS.sub(" ", str(v)).strip()


def registrar(leccion):
    if not isinstance(leccion, dict):
        raise ValueError("la leccion debe ser un objeto")
    for k in ("codigo", "accion"):
        if not isinstance(leccion.get(k), str) or not _limpia(leccion[k]):
            raise ValueError("la leccion necesita %s (texto no vacio)" % k)
    fila = {"ts": int(time.time())}
    for k in ("codigo", "accion", "resultado", "modelo", "sintoma", "evidencia"):
        if k in leccion and leccion[k] is not None:
            fila[k] = _limpia(leccion[k])
    with open(os.path.join(_dir(), "lecciones.jsonl"), "a", encoding="utf-8") as f:
        f.write(json.dumps(fila, ensure_ascii=False) + "\n")
    return fila


def lecciones():
    """Lee el jsonl saltando lineas truncadas/corruptas o de forma rara (no deben tumbar proponer)."""
    try:
        with open(os.path.join(_dir(), "lecciones.jsonl"), encoding="utf-8", errors="replace") as f:
            lineas = f.read().splitlines()
    except OSError:
        return []
    out = []
    for x in lineas:
        try:
            l = json.loads(x)
            if not (isinstance(l, dict) and isinstance(l.get("codigo"), str) and isinstance(l.get("accion"), str)
                    and l["codigo"].strip() and l["accion"].strip()):
                continue
            ts = l.get("ts")
            l["ts"] = int(ts) if isinstance(ts, (int, float)) and not isinstance(ts, bool) else 0
            time.gmtime(l["ts"])  # ts absurdo -> se descarta la linea
            out.append(l)
        except (ValueError, TypeError, OverflowError, OSError):
            continue
    return out


def proponer():
    cuenta = collections.Counter((_limpia(l["codigo"]), _limpia(l["accion"]), l.get("resultado") == "PASS") for l in lecciones())
    props = []
    for (codigo, accion, ok), n in sorted(cuenta.items()):
        tipo = "promover_a_runbook" if ok else "cambiar_estrategia"
        if n >= MINIMO and permitido(POR_TIPO[tipo]):
            props.append({"tipo": tipo, "codigo": codigo, "accion": accion, "veces": n, "archivo": POR_TIPO[tipo]})
    return props


def escribir_md():
    d, ls, ps = _dir(), lecciones(), proponer()
    with open(os.path.join(d, "LECCIONES.md"), "w", encoding="utf-8") as f:
        f.write("# Lecciones registradas\n\n" + "\n".join("- %s · %s · %s → %s" % (time.strftime("%Y-%m-%d %H:%M", time.gmtime(l["ts"])), _limpia(l["codigo"]), _limpia(l["accion"]), _limpia(l.get("resultado", "?"))) for l in ls) + "\n")
    with open(os.path.join(d, "PROPUESTAS.md"), "w", encoding="utf-8") as f:
        f.write("# Propuestas de mejora (el agente las aplica con commit propio; nada protegido)\n\n" + ("\n".join("- **%(tipo)s** `%(archivo)s`: «%(accion)s» para %(codigo)s (%(veces)d veces)" % p for p in ps) or "Sin propuestas todavia.") + "\n")
    return ps


if __name__ == "__main__":
    a = sys.argv[1:2]
    if a == ["registrar"]:
        print(json.dumps(registrar(json.loads(sys.argv[2])), ensure_ascii=False))
    elif a == ["proponer"]:
        print(json.dumps(proponer(), ensure_ascii=False, indent=2))
    elif a == ["md"]:
        print(json.dumps(escribir_md(), ensure_ascii=False))
    else:
        sys.exit("uso: evolucion.py registrar '{json}' | proponer | md")
