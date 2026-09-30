"""espejo_equipo — genera un ESPEJO (copia de puesta en marcha) del equipo, separado y no monolitico.

Modos (datos, ver MODOS): hermes_openclaw | equipo_completo. Las rutas salen de AGENTES.yaml
(carpeta/codigo de cada entrada); no se inventa ninguna: lo que falta se lista como MISSING.
Copia real de ficheros (nunca symlinks), sin red ni git. Por defecto DRY-RUN.
Uso: python espejo_equipo.py --modo hermes_openclaw|equipo_completo --destino DIR [--origen DIR] [--aplicar]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path

import yaml

MANIFIESTO = "chat router/05-AGENTES/AGENTES.yaml"
SECCIONES = ("jerarquia", "colmena_ingenieria", "apoyo")
MAX_BYTES = 5 * 1024 * 1024

# Modos como datos. ids=None -> todas las entradas del manifiesto.
# puente: ficheros de puente/config de Hermes+OpenClaw nombrados en INVENTARIO-PRIORIDAD2 (item 3),
# relativos a la carpeta del manifiesto; si no existen se listan MISSING.
PUENTE = ("asistentes/hermes.md", "asistentes/hermes_config.yaml", "asistentes/openclaw_config.yaml",
          "asistentes/puente_asistentes.py", "asistentes/heartbeat.py", "asistentes/arrancar_asistentes.sh")
MODOS = {
    "hermes_openclaw": {"ids": ("hermes", "openclaw"), "puente": PUENTE},
    "equipo_completo": {"ids": None, "puente": PUENTE},
}

EXCL_DIRS = {"__pycache__", ".git", "node_modules", "Banco de claves"}
EXCL_GLOBS = ("*.enc", ".env*", "*.pem", "*.key", "*.b64")
SECRETOS = re.compile(rb"nvapi-[A-Za-z0-9_\-]{10,}|gsk_[A-Za-z0-9]{10,}|hf_[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9_\-]{20,}")


def _limpia(ruta: str, prefijo: str) -> str:
    ruta = ruta.replace("Componente…/", prefijo.rstrip("/") + "/")
    return re.sub(r"\s*\(.*\)\s*$", "", ruta).strip().rstrip("/")


def _entradas(man: dict) -> list[dict]:
    return [e for s in SECCIONES for e in man.get(s, []) if isinstance(e, dict) and e.get("id")]


def _rutas_de(e: dict, man: dict) -> list[tuple[str, str]]:
    """Devuelve (base, ruta) declaradas por la entrada: carpeta -> base 'manifiesto'; codigo -> base 'origen'."""
    out = []
    if e.get("carpeta"):
        out.append(("manifiesto", str(e["carpeta"]).rstrip("/")))
    cod = e.get("codigo")
    for c in ([cod] if isinstance(cod, str) else cod or []):
        out.append(("origen", _limpia(c, man.get("codigo_descargado", ""))))
    return out


def _excluido(rel: Path, p: Path) -> str | None:
    if any(part in EXCL_DIRS for part in rel.parts):
        return "dir_excluido"
    if any(rel.name == g or rel.match(g) for g in EXCL_GLOBS):
        return "patron_secreto_nombre"
    if p.is_symlink():
        return "symlink"
    if p.stat().st_size > MAX_BYTES:
        return "mayor_5MB"
    if SECRETOS.search(p.read_bytes()):
        return "contenido_tipo_secreto"
    return None


def planificar(modo: str, origen: str | Path) -> dict:
    origen = Path(origen).resolve()
    man_path = origen / MANIFIESTO
    man = yaml.safe_load(man_path.read_text(encoding="utf-8"))
    base_man = man_path.parent
    cfg = MODOS[modo]
    plan = {"modo": modo, "origen": str(origen), "archivos": [], "excluidos": [], "missing": [], "refused": [], "referencias": []}
    vistos: set[str] = set()

    def _agrega(p: Path, agente: str) -> None:
        rel = p.relative_to(origen)
        if str(rel) in vistos:
            return
        vistos.add(str(rel))
        razon = _excluido(rel, p)
        (plan["excluidos"].append({"path": rel.as_posix(), "razon": razon}) if razon
         else plan["archivos"].append({"path": rel.as_posix(), "agente": agente}))

    def _resuelve(base: Path, ruta: str, agente: str, alt: tuple[Path, ...] = ()) -> None:
        if Path(ruta).is_absolute() or ".." in Path(ruta).parts:
            plan["refused"].append({"agente": agente, "ruta": ruta, "razon": "path_traversal"})
            return
        for b in (base, *alt):
            p = (b / ruta)
            if p.exists() or p.is_symlink():
                real = p.resolve()
                if origen not in real.parents and real != origen:
                    plan["refused"].append({"agente": agente, "ruta": ruta, "razon": "fuera_del_origen"})
                    return
                if p.is_dir():
                    for f in sorted(x for x in p.rglob("*") if x.is_file() or x.is_symlink()):
                        _agrega(f, agente)
                else:
                    _agrega(p, agente)
                return
        plan["missing"].append({"agente": agente, "ruta": ruta})

    _agrega(man_path, "manifiesto")
    for e in _entradas(man):
        if cfg["ids"] is not None and e["id"] not in cfg["ids"]:
            continue
        rutas = _rutas_de(e, man)
        if e.get("fork"):
            plan["referencias"].append({"agente": e["id"], "fork": e["fork"], "nota": "repo externo, no se copia"})
        if not rutas:
            plan["missing"].append({"agente": e["id"], "ruta": None, "nota": "el manifiesto no declara carpeta ni codigo"})
        alt = (origen, origen / Path(man.get("codigo_descargado", "")).parent)
        for base, ruta in rutas:
            _resuelve(base_man if base == "manifiesto" else origen, ruta, e["id"], alt if base == "origen" else ())
    for ruta in cfg["puente"]:
        _resuelve(base_man, ruta, "puente")
    return plan


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def aplicar(plan: dict, destino: str | Path, commit: str | None = None) -> dict:
    origen, destino = Path(plan["origen"]), Path(destino).resolve()
    destino.mkdir(parents=True, exist_ok=True)
    files = []
    for f in plan["archivos"]:
        dst = (destino / f["path"]).resolve()
        if destino not in dst.parents:
            raise ValueError(f"escritura fuera de destino refusada: {f['path']}")
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(origen / f["path"], dst)  # copia real, nunca symlink
        files.append({"path": f["path"], "sha256": _sha(dst), "bytes": dst.stat().st_size})
    mm = {"modo": plan["modo"], "source_commit": commit, "files": files, "excluded": plan["excluidos"],
          "missing": plan["missing"], "refused": plan["refused"]}
    (destino / "MIRROR-MANIFEST.json").write_text(json.dumps(mm, indent=2, ensure_ascii=False), encoding="utf-8")
    return mm


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--modo", required=True, choices=sorted(MODOS))
    ap.add_argument("--destino", required=True)
    ap.add_argument("--origen", default=str(Path(__file__).resolve().parents[3]))
    ap.add_argument("--aplicar", action="store_true", help="sin esto es DRY-RUN")
    a = ap.parse_args(argv)
    plan = planificar(a.modo, a.origen)
    print(f"modo={plan['modo']} archivos={len(plan['archivos'])} excluidos={len(plan['excluidos'])} "
          f"MISSING={len(plan['missing'])} refused={len(plan['refused'])}")
    for m in plan["missing"]:
        print("MISSING", m["agente"], m.get("ruta"))
    for r in plan["refused"]:
        print("REFUSED", r["agente"], r["ruta"], r["razon"])
    if a.aplicar:
        aplicar(plan, a.destino)
        print("copiado a", a.destino)
    else:
        print("DRY-RUN: no se copio nada (usa --aplicar)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
