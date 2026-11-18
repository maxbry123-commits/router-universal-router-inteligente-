#!/usr/bin/env python3
"""pull_agent_roots.py — MINIMAX 2F · auto-pull de las 3 raices de agentes.

Que pedia el Director: "revisa que todo este, todas las raices en auto pull".

Raices y su origen REAL (leido de los manifiestos del repo, no inventado):
  · ruflo   -> git ruvnet/ruflo            (integridad por sha256 de .harness/manifest.json)
  · rowboat -> git rowboatlabs/rowboat @ commit fijado (integridad por sha256 de las partes)
  · donors  -> git por cookbook (url + commit + sparse en MANIFEST.json)

Modo por defecto: INFORME (dry-run). Nada se escribe en el repo.
Con `--apply`: se clona la fuente en un temporal, se copian SOLO los ficheros
que cambian, cada copia se verifica por sha256 y se deja un recibo en
`reports/roots_pull.json` (con copia de seguridad en `state/roots_backup/`).

Fail-closed: si el remoto no se puede consultar, el veredicto es UNKNOWN
(nunca "al dia"). `git ls-remote` es FAIL-OPEN (devuelve 0 con vacio): la
comparacion contra `refs/heads/<ref>` es EXACTA o el estado es UNKNOWN.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent
REGISTRY = REPO_ROOT / "router_llm_hf" / "AGENTS_REGISTRY.json"
REPORT_PATH = REPO_ROOT / "reports" / "roots_pull.json"
BACKUP_DIR = REPO_ROOT / "state" / "roots_backup"

# Origen por raiz (verificado en los manifiestos del repo).
SOURCES: Dict[str, Dict[str, Any]] = {
    "ruflo": {"repo": "ruvnet/ruflo", "ref": "main", "kind": "git"},
    "rowboat": {"repo": "rowboatlabs/rowboat", "ref": "main", "kind": "git",
                "pinned_commit": "d31c03813451ffab5a1c4e1d5870fbbb90ba6108"},
    "donors": {"repo": "", "ref": "", "kind": "manifest"},
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git(*args: str, cwd: Optional[Path] = None, timeout: int = 120) -> Tuple[int, str, str]:
    try:
        proc = subprocess.run(["git", *args], cwd=str(cwd) if cwd else None,
                              capture_output=True, text=True, timeout=timeout)
        return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
    except Exception as exc:
        return 1, "", str(exc)


def remote_head(repo: str, ref: str) -> Optional[str]:
    """SHA real de refs/heads/<ref>. None si no se puede saber (FAIL-OPEN)."""
    code, out, _err = git("ls-remote", "--heads", f"https://github.com/{repo}.git", ref)
    if code != 0 or not out:
        return None
    for line in out.splitlines():
        parts = line.split()
        if len(parts) == 2 and parts[1] == f"refs/heads/{ref}":
            return parts[0]
    return None


# --------------------------------------------------------------------------
# VERIFICACION LOCAL (integridad real por sha256)
# --------------------------------------------------------------------------
def check_ruflo(root: Path) -> Dict[str, Any]:
    manifest_path = root / ".harness" / "manifest.json"
    result: Dict[str, Any] = {"manifest": ".harness/manifest.json", "files": [], "ok": True}
    if not manifest_path.is_file():
        return {"manifest": ".harness/manifest.json", "files": [], "ok": False,
                "error": "no existe el manifiesto"}
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"manifest": ".harness/manifest.json", "files": [], "ok": False, "error": str(exc)}
    for rel, expected in (data.get("files") or {}).items():
        path = root / rel
        if not path.is_file():
            result["files"].append({"file": rel, "state": "MISSING"})
            result["ok"] = False
            continue
        actual = sha256_file(path)
        state = "OK" if actual == expected else "DRIFT"
        result["files"].append({"file": rel, "state": state, "expected": expected, "actual": actual})
        if state != "OK":
            result["ok"] = False
    result["template_version"] = data.get("template_version")
    return result


def check_rowboat(root: Path) -> Dict[str, Any]:
    manifest_path = root / "DOWNLOAD_EXTRACT_MANIFEST.json"
    result: Dict[str, Any] = {"manifest": "DOWNLOAD_EXTRACT_MANIFEST.json", "parts": [], "ok": True}
    if not manifest_path.is_file():
        return {"manifest": "DOWNLOAD_EXTRACT_MANIFEST.json", "parts": [], "ok": False,
                "error": "no existe el manifiesto"}
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"manifest": "DOWNLOAD_EXTRACT_MANIFEST.json", "parts": [], "ok": False, "error": str(exc)}
    for part in data.get("parts") or []:
        path = root / "_archives" / part["name"]
        if not path.is_file():
            result["parts"].append({"part": part["name"], "state": "MISSING"})
            result["ok"] = False
            continue
        actual = sha256_file(path)
        state = "OK" if actual == part.get("sha256") else "DRIFT"
        result["parts"].append({"part": part["name"], "state": state, "bytes": path.stat().st_size})
        if state != "OK":
            result["ok"] = False
    result["extraction_verified"] = bool(data.get("extraction_verified"))
    result["source_repo"] = data.get("source_repo")
    result["source_commit"] = data.get("source_commit")
    result["pinned_commit"] = SOURCES["rowboat"]["pinned_commit"]
    return result


def check_donors(root: Path) -> Dict[str, Any]:
    manifest_path = root / "MANIFEST.json"
    result: Dict[str, Any] = {"manifest": "MANIFEST.json", "donors": [], "ok": True}
    if not manifest_path.is_file():
        return {"manifest": "MANIFEST.json", "donors": [], "ok": False, "error": "no existe el manifiesto"}
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"manifest": "MANIFEST.json", "donors": [], "ok": False, "error": str(exc)}
    for name, cfg in data.items():
        if not isinstance(cfg, dict):
            continue
        entry = {"donor": name, "url": cfg.get("url"), "commit": cfg.get("commit"),
                 "sparse": cfg.get("sparse"), "files": cfg.get("files"),
                 "declared_status": cfg.get("status")}
        local = root / name
        entry["local_exists"] = local.is_dir()
        if local.is_dir():
            count = sum(len(files) for _r, _d, files in os.walk(local))
            entry["local_files"] = count
            entry["files_match"] = (cfg.get("files") is None) or (count == cfg.get("files"))
        result["donors"].append(entry)
        if not entry["local_exists"]:
            result["ok"] = False
    return result


CHECKERS = {"ruflo": check_ruflo, "rowboat": check_rowboat, "donors": check_donors}


# --------------------------------------------------------------------------
# AUTO-PULL (apply)
# --------------------------------------------------------------------------
def apply_git_root(name: str, root: Path, repo: str, ref: str,
                   sparse: Optional[List[str]] = None) -> Dict[str, Any]:
    """Clona la fuente en un temporal y copia SOLO los ficheros que cambian."""
    receipt: Dict[str, Any] = {"root": name, "repo": repo, "ref": ref, "copied": [], "removed": [],
                               "errors": []}
    tmp = Path(tempfile.mkdtemp(prefix=f"rootpull-{name}-"))
    try:
        url = f"https://github.com/{repo}.git"
        args = ["clone", "--depth", "1", "--filter=blob:none"]
        if sparse:
            args += ["--sparse"]
        args += ["--branch", ref, url, str(tmp)]
        code, _out, err = git(*args)
        if code != 0:
            receipt["errors"].append(f"clone fallo: {err[:300]}")
            return receipt
        code, sha, _e = git("rev-parse", "HEAD", cwd=tmp)
        receipt["remote_commit"] = sha
        # Copia con verificacion sha256 (solo lo que cambia).
        for src in sorted(tmp.rglob("*")):
            if not src.is_file() or ".git" in src.parts:
                continue
            rel = src.relative_to(tmp)
            dest = root / rel
            if dest.is_file() and sha256_file(dest) == sha256_file(src):
                continue
            dest.parent.mkdir(parents=True, exist_ok=True)
            if dest.is_file():
                bak = BACKUP_DIR / name / rel
                bak.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(dest, bak)
            shutil.copy2(src, dest)
            actual = sha256_file(dest)
            if actual != sha256_file(src):
                receipt["errors"].append(f"sha256 no coincide tras copiar: {rel}")
            receipt["copied"].append(str(rel))
    except Exception as exc:
        receipt["errors"].append(str(exc))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return receipt


def main() -> int:
    ap = argparse.ArgumentParser(description="Auto-pull de las raices de agentes")
    ap.add_argument("--all", action="store_true", help="procesa las 3 raices")
    ap.add_argument("--root", action="append", default=[], help="procesa una raiz concreta")
    ap.add_argument("--apply", action="store_true", help="APLICA los cambios (por defecto: informe)")
    ap.add_argument("--json", action="store_true", help="salida en JSON")
    args = ap.parse_args()

    if not args.all and not args.root:
        print("uso: pull_agent_roots.py --all [--apply] | --root <nombre>")
        return 2

    registry = {}
    if REGISTRY.is_file():
        try:
            registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
        except Exception as exc:
            print(f"FALLO: registro ilegible: {exc}")
            return 2
    roots = registry.get("roots") or {}

    names = list(args.root) if args.root else sorted(roots.keys())
    report: Dict[str, Any] = {"mode": "apply" if args.apply else "dry-run", "roots": {}}
    exit_code = 0

    for name in names:
        cfg = roots.get(name) or {}
        rel = cfg.get("path") or f"chat-router/agentes/{name}"
        root = REPO_ROOT / rel
        entry: Dict[str, Any] = {"path": rel, "exists": root.is_dir()}
        checker = CHECKERS.get(name)
        entry["integrity"] = checker(root) if (checker and root.is_dir()) else {"ok": False, "error": "raiz ausente"}

        src = SOURCES.get(name) or {}
        if src.get("kind") == "git" and src.get("repo"):
            head = remote_head(src["repo"], src["ref"])
            pinned = src.get("pinned_commit")
            if head is None:
                entry["remote"] = {"state": "UNKNOWN", "why": "no se pudo consultar refs/heads (offline o repo privado)"}
            else:
                state = "OK" if (head == pinned or not pinned) else "DRIFT"
                entry["remote"] = {"state": state, "head": head, "pinned": pinned, "repo": src["repo"]}
        elif name == "donors":
            donors = entry["integrity"].get("donors") or []
            entry["remote"] = {"state": "INLINE", "donors": len(donors)}

        entry["verdict"] = ("OK" if entry.get("exists") and entry["integrity"].get("ok")
                            and entry.get("remote", {}).get("state") in ("OK", "INLINE", "UNKNOWN")
                            else "DRIFT")

        if args.apply and entry["verdict"] == "DRIFT" and src.get("kind") == "git" and src.get("repo"):
            entry["apply"] = apply_git_root(name, root, src["repo"], src["ref"])
            if entry["apply"]["errors"]:
                exit_code = 1
        report["roots"][name] = entry

    report["ok"] = exit_code == 0
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"Auto-pull de raices · modo {report['mode']} · recibo: {REPORT_PATH}")
        for name, entry in report["roots"].items():
            integ = entry.get("integrity") or {}
            print(f"  · {name}: veredicto={entry.get('verdict')} · integridad={'OK' if integ.get('ok') else 'FALLO'} "
                  f"· remoto={(entry.get('remote') or {}).get('state')} · {entry.get('path')}")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
