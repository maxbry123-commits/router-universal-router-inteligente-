#!/usr/bin/env python3
"""VENTANA GAPS — store de gaps con validación de evidencia (fail-closed).

Esquema de cada gap (el owner es la ley):

    {
      "id": "GAP-0001",
      "tipo": "GAP|ERROR|DRIFT|BROKEN_CANDIDATE|HUÉRFANO",
      "severidad": "P0|P1|P2|P3",
      "titulo": "...",
      "evidencia": "ruta:línea + sha256",
      "componente": "...",
      "estado": "OPEN|IN_PROGRESS|FIXED|WONTFIX",
      "notas": "<= 500 chars",
      "creado": "ISO-8601",
      "resuelto": null|ISO-8601
    }

Flujo: captura -> validar evidencia (ruta:línea debe existir en INVENTORY.json)
-> guardar -> V2 muestra contador -> el auditor lo recoge en GAPS.md ->
NEXT_ACTIONS lo prioriza P0-P3.

Regla dura: si la evidencia no valida -> error (400 en la capa API) y el gap
NO se crea. No hay gaps inventados.

Rutas: las rutas por defecto son relativas a la raiz del propio script
(Path(__file__).parent), NO al CWD. La escritura es atomica (temp + replace).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_STORE = SCRIPT_DIR / "gaps.json"
DEFAULT_INVENTORY = SCRIPT_DIR / "INVENTORY.json"

GAP_TYPES = ("GAP", "ERROR", "DRIFT", "BROKEN_CANDIDATE", "HUÉRFANO")
SEVERITIES = ("P0", "P1", "P2", "P3")
GAP_STATES = ("OPEN", "IN_PROGRESS", "FIXED", "WONTFIX")

EVIDENCE_RE = re.compile(r"^(?P<path>[^:\s]+):(?P<line>\d+)\s*(?P<rest>.*)$")
SHA_RE = re.compile(r"sha256:([0-9a-f]{64})")

MAX_NOTES = 500
MAX_TITLE = 200


class GapsStoreError(ValueError):
    """Error fail-closed del store. `code` es estable para la capa HTTP (400)."""

    def __init__(self, code: str, detail: str = ""):
        super().__init__(code + (": " + detail if detail else ""))
        self.code = code
        self.detail = detail


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


# --------------------------------------------------------------------------- #
# Utilidades de IO (atomico)
# --------------------------------------------------------------------------- #


def atomic_write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8") + b"\n"
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".gaps-tmp-", suffix=path.name)
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
        os.chmod(tmp, 0o644)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


# --------------------------------------------------------------------------- #
# Inventario
# --------------------------------------------------------------------------- #


def load_inventory(inventory_path: Path) -> dict:
    """Carga INVENTORY.json -> {ruta: {sha256, bytes, lines, language}}."""
    data = load_json(Path(inventory_path))
    if not isinstance(data, dict) or not isinstance(data.get("files"), list):
        raise GapsStoreError("INVENTARIO_ILEGIBLE", str(inventory_path))
    out = {}
    for entry in data["files"]:
        if not isinstance(entry, dict) or "path" not in entry:
            continue
        out[entry["path"]] = entry
    if not out:
        raise GapsStoreError("INVENTARIO_VACIO", str(inventory_path))
    return out


# --------------------------------------------------------------------------- #
# Validacion de evidencia
# --------------------------------------------------------------------------- #


def parse_evidence(evidence: str):
    """Parsea 'ruta:línea [+ sha256:...]' -> (ruta, linea, sha|None)."""
    if not isinstance(evidence, str) or not evidence.strip():
        raise GapsStoreError("EVIDENCIA_INVALIDA", "evidencia vacia")
    m = EVIDENCE_RE.match(evidence.strip())
    if not m:
        raise GapsStoreError("EVIDENCIA_INVALIDA",
                             "formato esperado 'ruta:línea' -> %r" % evidence[:80])
    path = m.group("path")
    line = int(m.group("line"))
    sha = SHA_RE.search(m.group("rest") or "")
    if path.startswith("/") or ".." in path.split("/") or ":" in path[1:3]:
        raise GapsStoreError("EVIDENCIA_INVALIDA", "ruta fuera de alcance: %r" % path[:80])
    return path, line, (sha.group(1) if sha else None)


def validate_evidence(evidence: str, inventory: dict):
    """Valida la evidencia contra INVENTORY. Devuelve (ruta, linea, sha256).

    Lanza GapsStoreError si la ruta no existe o la linea no existe.
    """
    path, line, declared_sha = parse_evidence(evidence)
    meta = inventory.get(path)
    if meta is None:
        raise GapsStoreError("EVIDENCIA_INVALIDA",
                             "ruta no presente en INVENTORY.json: %s" % path)
    total = int(meta.get("lines") or 0)
    if line < 1 or (total and line > total):
        raise GapsStoreError("EVIDENCIA_INVALIDA",
                             "linea %d fuera de rango en %s (lineas=%d)" % (line, path, total))
    real_sha = meta.get("sha256")
    if declared_sha and real_sha and declared_sha != real_sha:
        raise GapsStoreError("EVIDENCIA_INVALIDA",
                             "sha256 de la evidencia no coincide con INVENTORY.json: %s" % path)
    return path, line, real_sha


# --------------------------------------------------------------------------- #
# Store
# --------------------------------------------------------------------------- #


def load_gaps(store_path: Path) -> list:
    data = load_json(Path(store_path))
    if isinstance(data, dict) and isinstance(data.get("gaps"), list):
        return data["gaps"]
    if isinstance(data, list):
        return data
    return []


def next_gap_id(gaps: list) -> str:
    used = set()
    for gap in gaps:
        gid = str(gap.get("id", ""))
        if re.fullmatch(r"GAP-\d{4,}", gid):
            used.add(int(gid.split("-")[1]))
    n = 1
    while n in used:
        n += 1
    return "GAP-%04d" % n


def normalize_gap(gap: dict, inventory: dict, created: str = None) -> dict:
    """Valida y normaliza un gap. Lanza GapsStoreError si algo no valida."""
    if not isinstance(gap, dict):
        raise GapsStoreError("GAP_ILEGIBLE", "se esperaba un objeto JSON")
    tipo = gap.get("tipo")
    if tipo not in GAP_TYPES:
        raise GapsStoreError("TIPO_INVALIDO", "tipo=%r admitidos=%s" % (tipo, "|".join(GAP_TYPES)))
    severidad = gap.get("severidad")
    if severidad not in SEVERITIES:
        raise GapsStoreError("SEVERIDAD_INVALIDA",
                             "severidad=%r admitidos=%s" % (severidad, "|".join(SEVERITIES)))
    estado = gap.get("estado", "OPEN")
    if estado not in GAP_STATES:
        raise GapsStoreError("ESTADO_INVALIDO",
                             "estado=%r admitidos=%s" % (estado, "|".join(GAP_STATES)))
    titulo = gap.get("titulo")
    if not isinstance(titulo, str) or not titulo.strip():
        raise GapsStoreError("TITULO_INVALIDO", "titulo vacio")
    if len(titulo) > MAX_TITLE:
        raise GapsStoreError("TITULO_INVALIDO", "titulo > %d chars" % MAX_TITLE)
    componente = gap.get("componente")
    if not isinstance(componente, str) or not componente.strip():
        raise GapsStoreError("COMPONENTE_INVALIDO", "componente vacio")
    notas = gap.get("notas", "") or ""
    if not isinstance(notas, str):
        raise GapsStoreError("NOTAS_INVALIDAS", "notas deben ser texto")
    if len(notas) > MAX_NOTES:
        raise GapsStoreError("NOTAS_INVALIDAS", "notas > %d chars" % MAX_NOTES)
    ruta, linea, sha = validate_evidence(gap.get("evidencia", ""), inventory)
    record = {
        "id": str(gap.get("id") or "").strip() or None,
        "tipo": tipo,
        "severidad": severidad,
        "titulo": titulo.strip(),
        "evidencia": "%s:%d sha256:%s" % (ruta, linea, sha),
        "componente": componente.strip(),
        "estado": estado,
        "notas": notas[:MAX_NOTES],
        "creado": gap.get("creado") or created or utcnow(),
        "resuelto": gap.get("resuelto"),
    }
    return record


def add_gap(gap: dict, store_path: Path = None, inventory_path: Path = None) -> dict:
    """Añade un gap validando su evidencia. Si la evidencia no valida, NO se crea nada."""
    store_path = Path(store_path or DEFAULT_STORE)
    inventory_path = Path(inventory_path or DEFAULT_INVENTORY)
    inventory = load_inventory(inventory_path)
    existing = load_gaps(store_path)
    record = normalize_gap(gap, inventory)
    if not record["id"]:
        record["id"] = next_gap_id(existing)
    if any(str(g.get("id")) == record["id"] for g in existing):
        raise GapsStoreError("ID_DUPLICADO", record["id"])
    existing.append(record)
    payload = {
        "schema": "xray-gaps-store/1",
        "updated_at": utcnow(),
        "count": len(existing),
        "gaps": existing,
    }
    atomic_write_json(store_path, payload)
    return record


def count_gaps(gaps: list) -> dict:
    """Contador para la V2 (Progress)."""
    by_state = {s: 0 for s in GAP_STATES}
    by_type = {t: 0 for t in GAP_TYPES}
    by_sev = {s: 0 for s in SEVERITIES}
    for gap in gaps:
        if gap.get("estado") in by_state:
            by_state[gap["estado"]] += 1
        if gap.get("tipo") in by_type:
            by_type[gap["tipo"]] += 1
        if gap.get("severidad") in by_sev:
            by_sev[gap["severidad"]] += 1
    return {
        "total": len(gaps),
        "abiertos": by_state.get("OPEN", 0),
        "by_state": by_state,
        "by_type": by_type,
        "by_severity": by_sev,
    }


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #


def parse_args(argv):
    ap = argparse.ArgumentParser(prog="gaps_store.py",
                                 description="Store de gaps con validacion de evidencia")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_add = sub.add_parser("add", help="crea un gap (valida la evidencia)")
    p_add.add_argument("--file", help="fichero JSON con el gap")
    p_add.add_argument("--json", dest="inline", help="gap en linea (JSON)")
    p_add.add_argument("--store", default=str(DEFAULT_STORE))
    p_add.add_argument("--inventory", default=str(DEFAULT_INVENTORY))

    p_list = sub.add_parser("list", help="lista los gaps del store")
    p_list.add_argument("--store", default=str(DEFAULT_STORE))

    p_count = sub.add_parser("count", help="contador para la V2")
    p_count.add_argument("--store", default=str(DEFAULT_STORE))

    sub.add_parser("paths", help="resuelve las rutas por defecto (relativas al script)")
    return ap.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])
    try:
        if args.cmd == "paths":
            print(json.dumps({
                "store": str(DEFAULT_STORE),
                "inventory": str(DEFAULT_INVENTORY),
                "script_dir": str(SCRIPT_DIR),
                "cwd": os.getcwd(),
            }, ensure_ascii=False, indent=2))
            return 0
        if args.cmd == "list":
            gaps = load_gaps(Path(args.store))
            print(json.dumps({"count": len(gaps), "gaps": gaps}, ensure_ascii=False, indent=2))
            return 0
        if args.cmd == "count":
            gaps = load_gaps(Path(args.store))
            print(json.dumps(count_gaps(gaps), ensure_ascii=False, indent=2))
            return 0
        if args.cmd == "add":
            if args.inline:
                payload = json.loads(args.inline)
            elif args.file:
                payload = json.loads(Path(args.file).read_text(encoding="utf-8"))
            else:
                raise GapsStoreError("ENTRADA_INVALIDA", "usa --file o --json")
            record = add_gap(payload, Path(args.store), Path(args.inventory))
            print(json.dumps({"ok": True, "gap": record}, ensure_ascii=False, indent=2))
            return 0
    except GapsStoreError as exc:
        print(json.dumps({"ok": False, "error": exc.code, "detail": exc.detail},
                         ensure_ascii=False, indent=2))
        return 2
    except (OSError, ValueError) as exc:
        print(json.dumps({"ok": False, "error": "IO_O_JSON_INVALIDO", "detail": str(exc)[:200]},
                         ensure_ascii=False, indent=2))
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
