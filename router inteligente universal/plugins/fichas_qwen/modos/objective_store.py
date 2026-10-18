#!/usr/bin/env python3
"""objective_store.py - Lee/escribe el objetivo fijado (state/objective.md). Cierra el hueco de leer_objetivo_fijado().
El .md es legible para humanos; el primer bloque ```json contiene el dict que usa el router.
Sin dependencias. FAIL-CLOSED: objetivo invalido o alterado => excepcion."""
import hashlib, json, os, re, tempfile

FENCE = re.compile(r"```json\s*\n(.*?)\n```", re.S)
REQUIRED = ["goal", "done_when", "constraints", "out_of_scope", "deliverables"]
LISTS = ["done_when", "constraints", "out_of_scope", "deliverables"]


class ObjectiveError(Exception):
    pass


def validate(obj: dict) -> list:
    e = []
    for k in REQUIRED:
        if k not in obj or obj[k] in (None, "", []):
            e.append(f"falta o vacio '{k}'")
    for k in LISTS:
        v = obj.get(k)
        if v is not None and (not isinstance(v, list) or not all(isinstance(x, str) and x.strip() for x in v)):
            e.append(f"'{k}' debe ser lista de textos no vacios")
    return e


def objective_hash(obj: dict) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def write_objective(path: str, obj: dict) -> str:
    errs = validate(obj)
    if errs:
        raise ObjectiveError("; ".join(errs))
    def bl(xs): return "\n".join(f"- {x}" for x in xs)
    md = (f"# OBJETIVO\n\n**Meta:** {obj['goal']}\n\n## Hecho cuando\n{bl(obj['done_when'])}\n\n"
          f"## Restricciones\n{bl(obj['constraints'])}\n\n## Fuera de alcance\n{bl(obj['out_of_scope'])}\n\n"
          f"## Entregables\n{bl(obj['deliverables'])}\n\n```json\n"
          f"{json.dumps(obj, ensure_ascii=False, indent=2)}\n```\n")
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(os.path.abspath(path)))
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(md)
    os.replace(tmp, path)          # escritura atomica
    return objective_hash(obj)


def read_objective(path: str):
    """None si no existe (primer turno). ObjectiveError si existe pero esta corrupto."""
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        txt = f.read()
    m = FENCE.search(txt)
    if not m:
        raise ObjectiveError("objetivo sin bloque json")
    try:
        obj = json.loads(m.group(1))
    except json.JSONDecodeError as ex:
        raise ObjectiveError(f"json del objetivo invalido: {ex}")
    errs = validate(obj)
    if errs:
        raise ObjectiveError("; ".join(errs))
    return obj


def assert_unchanged(path: str, expected_hash: str) -> None:
    """Deteccion de deriva: el objetivo fijado no puede mutar durante la ejecucion."""
    cur = read_objective(path)
    if cur is None or objective_hash(cur) != expected_hash:
        raise ObjectiveError("deriva: el objetivo fijado cambio o desaparecio")
