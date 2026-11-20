#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""auto_pull.py — cada push a GitHub se aplica en los Spaces VIVOS, sin reiniciar.

POR QUE HACE FALTA (investigado):
  Hugging Face NO tiene "pull en caliente" de un repo externo. Solo ofrece:
    · set_space_sleep_time() / hf spaces settings --sleep-time N  -> el Space se DUERME
      tras N s de inactividad y se despierta al llegar una visita (requiere que el
      proceso de arranque vuelva a hacer el clone). Requiere inactividad y el
      primer visitante carga (y en Grupo 2 re-descarga el GGUF).
    · restart_space() -> tira el contenedor (rebuild + re-descarga del modelo).
  La unica via para "aplicar el push en segundos, sin reiniciar el Space" es
  un WATCHER dentro del contenedor que:
    1. sondea GitHub (git fetch --depth 1) cada AUTO_PULL_INTERVAL_S,
    2. si el SHA remoto != HEAD local -> git reset --hard FETCH_HEAD (el entrypoint
       ya dejo el clon en /tmp/repo),
    3. re-aplica los hooks post-reset (p.ej. el parche --reasoning off),
    4. refresca las 3 RAICES de agentes desde su origen real (sha256 verificado),
    5. recarga IN-PLACE: os.execv(sys.executable, [sys.executable] + sys.argv)
       -> el proceso del Space se sustituye a si mismo. NO se reinicia el Space:
       no hay rebuild, no se tira el contenedor y el modelo NO se re-descarga.

FAIL-CLOSED: si el fetch falla no se toca el arbol y se reintenta. Si el reset
falla, se restaura el commit anterior (git reset --hard <sha_previo>).
"""
from __future__ import annotations

import json
import os
import subprocess
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

VERSION = "1.0.0"
DEFAULT_REPO_DIR = "/tmp/repo"
DEFAULT_BRANCH = "ccr-f01c3de9-bmry0s"
DEFAULT_INTERVAL = 20

# Origen REAL de cada raiz (leido de router_llm_hf/AGENTS_REGISTRY.json + scripts/pull_agent_roots.py)
ROOT_SOURCES: Dict[str, Dict[str, Any]] = {
    "ruflo": {"repo": "ruvnet/ruflo", "ref": "main", "kind": "git",
              "path": "chat-router/agentes/ruflo"},
    "rowboat": {"repo": "rowboatlabs/rowboat", "ref": "main", "kind": "git",
                "pinned_commit": "d31c03813451ffab5a1c4e1d5870fbbb90ba6108",
                "path": "chat-router/agentes/rowboat"},
    "donors": {"repo": "", "ref": "", "kind": "manifest",
               "path": "chat-router/agentes/donors"},
}

STATE_FILE = os.getenv("AUTO_PULL_STATE_FILE", "/tmp/autopull_state.json")

STATE: Dict[str, Any] = {
    "version": VERSION,
    "enabled": False,
    "branch": None,
    "repo_dir": None,
    "interval_s": DEFAULT_INTERVAL,
    "started_at": None,
    "last_poll_at": None,
    "last_pull_at": None,
    "head": None,
    "last_applied_sha": None,
    "pulls": 0,
    "reloads": 0,
    "roots": {},
    "errors": [],
}


# ----------------------------------------------------------------------------- estado persistente
def _state_load() -> Dict[str, Any]:
    """El estado sobrevive a la recarga in-place (execv reinicia el proceso)."""
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        if isinstance(data, dict):
            for k in ("pulls", "reloads", "last_pull_at", "last_applied_sha",
                      "last_poll_at", "started_at"):
                if data.get(k) is not None:
                    STATE[k] = data[k]
    except Exception:
        pass
    return STATE


def _state_save() -> None:
    try:
        tmp = STATE_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump({"pulls": STATE.get("pulls"), "reloads": STATE.get("reloads"),
                       "last_pull_at": STATE.get("last_pull_at"),
                       "last_applied_sha": STATE.get("last_applied_sha"),
                       "last_poll_at": STATE.get("last_poll_at"),
                       "started_at": STATE.get("started_at"),
                       "version": VERSION}, fh)
        os.replace(tmp, STATE_FILE)
    except Exception:
        pass


# ----------------------------------------------------------------------------- git
def _git(args: List[str], cwd: Optional[str] = None, timeout: int = 90) -> Tuple[int, str, str]:
    try:
        p = subprocess.run(["git"] + args, cwd=cwd, capture_output=True, text=True, timeout=timeout)
        return p.returncode, p.stdout.strip(), p.stderr.strip()
    except Exception as exc:  # fail-closed: nunca revienta el proceso
        return 1, "", str(exc)[:300]


def _sha256(path: Path) -> str:
    import hashlib
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def repo_root() -> Optional[Path]:
    """Raiz del repo: busca hacia arriba 'external/core/auto_pull.py'."""
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "external" / "core" / "auto_pull.py").is_file():
            return parent
        if (parent / ".git").exists():
            return parent
    return None


# ----------------------------------------------------------------------------- hooks
def _post_reset_hooks(root: Path) -> List[str]:
    """Hooks que el entrypoint aplica tras clonar; hay que re-aplicarlos tras cada reset.

    El entrypoint de Grupo 2 mete --reasoning off con un sed sobre el patron
    '"--n-gpu-layers", "0"]' de 'llm system HF/manager_v2.py'. Un reset --hard
    revierte ese parche: sin el, el 0.8B volveria a generar reasoning.
    """
    done: List[str] = []
    mgr = root / "llm system HF" / "manager_v2.py"
    if mgr.is_file():
        txt = mgr.read_text(encoding="utf-8")
        if '"--reasoning", "off"' not in txt:
            # sed de sistema (NO 'git sed', que no existe)
            try:
                p = subprocess.run(
                    ["sed", "-i",
                     's/"--n-gpu-layers", "0"\\]/"--n-gpu-layers", "0", "--reasoning", "off"]/',
                     "manager_v2.py"], cwd=str(mgr.parent),
                    capture_output=True, text=True, timeout=30)
                done.append("reasoning_off" if p.returncode == 0 else "reasoning_off_FAIL")
            except Exception as exc:
                done.append("reasoning_off_FAIL:%s" % str(exc)[:80])
    return done


# ----------------------------------------------------------------------------- raices
def _remote_head(repo: str, ref: str) -> Optional[str]:
    """SHA remoto de refs/heads/<ref>. FAIL-OPEN si no devuelve esa ref exacta."""
    rc, out, _e = _git(["ls-remote", "--heads", f"https://github.com/{repo}.git", f"refs/heads/{ref}"], timeout=60)
    if rc != 0:
        return None
    for line in (out or "").splitlines():
        parts = line.split()
        if len(parts) == 2 and parts[1] == f"refs/heads/{ref}":
            return parts[0]
    return None


def _apply_git_root(name: str, dest: Path, repo: str, ref: str,
                    pinned: Optional[str] = None) -> Dict[str, Any]:
    """Clona la fuente y copia SOLO los ficheros que cambian (sha256 verificado)."""
    receipt: Dict[str, Any] = {"root": name, "repo": repo, "ref": ref, "copied": [], "errors": []}
    tmp = Path("/tmp/autopull-%s-%s" % (name, os.getpid()))
    try:
        url = f"https://github.com/{repo}.git"
        if pinned:
            rc, _o, err = _git(["init", "-q", str(tmp)])
            if rc != 0:
                receipt["errors"].append("init fallo")
                return receipt
            rc, _o, err = _git(["remote", "add", "origin", url], cwd=str(tmp))
            rc, _o, err = _git(["fetch", "--depth", "1", "origin", pinned], cwd=str(tmp), timeout=180)
            if rc != 0:
                receipt["errors"].append("fetch del commit fijado fallo")
                return receipt
            rc, _o, err = _git(["checkout", "-q", "FETCH_HEAD"], cwd=str(tmp))
        else:
            rc, _o, err = _git(["clone", "--depth", "1", "--filter=blob:none", "--branch", ref, url, str(tmp)], timeout=300)
            if rc != 0:
                receipt["errors"].append("clone fallo")
                return receipt
        rc, sha, _e = _git(["rev-parse", "HEAD"], cwd=str(tmp))
        receipt["remote_commit"] = sha
        for src in sorted(tmp.rglob("*")):
            if not src.is_file() or ".git" in src.parts:
                continue
            rel = src.relative_to(tmp)
            target = dest / rel
            if target.is_file() and _sha256(target) == _sha256(src):
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            try:
                target.write_bytes(src.read_bytes())
            except Exception as exc:
                receipt["errors"].append("copia fallo %s: %s" % (rel, exc))
                continue
            if _sha256(target) != _sha256(src):
                receipt["errors"].append("sha256 no coincide: %s" % rel)
            receipt["copied"].append(str(rel))
    except Exception as exc:
        receipt["errors"].append(str(exc)[:300])
    finally:
        try:
            import shutil
            shutil.rmtree(tmp, ignore_errors=True)
        except Exception:
            pass
    return receipt


def refresh_roots(root: Path) -> Dict[str, Any]:
    """Refresca las 3 raices desde su origen real. Best-effort: un fallo no es fatal."""
    out: Dict[str, Any] = {}
    for name, cfg in ROOT_SOURCES.items():
        dest = root / cfg["path"]
        entry: Dict[str, Any] = {"kind": cfg["kind"], "path": cfg["path"], "state": "SKIP"}
        try:
            if cfg["kind"] == "git" and cfg.get("repo"):
                head = _remote_head(cfg["repo"], cfg["ref"])
                if head is None:
                    entry["state"] = "UNKNOWN"
                    entry["why"] = "no se pudo consultar refs/heads/%s" % cfg["ref"]
                else:
                    entry["remote_head"] = head
                    pinned = cfg.get("pinned_commit")
                    if pinned and head != pinned:
                        entry["state"] = "DRIFT"
                        entry["why"] = "remote %s != commit fijado %s" % (head[:12], pinned[:12])
                    else:
                        rec = _apply_git_root(name, dest, cfg["repo"], cfg["ref"], pinned)
                        entry["copied"] = len(rec["copied"])
                        entry["errors"] = rec["errors"][:5]
                        entry["state"] = "OK" if not rec["errors"] else "ERROR"
            else:  # donors: el origen es el propio repo (manifest por cookbook)
                man = dest / "MANIFEST.json"
                if not man.is_file():
                    entry["state"] = "UNKNOWN"
                    entry["why"] = "sin MANIFEST.json"
                else:
                    try:
                        data = json.loads(man.read_text(encoding="utf-8"))
                        n = sum(1 for v in data.values() if isinstance(v, dict))
                        entry["donors"] = n
                        entry["state"] = "OK"
                    except Exception as exc:
                        entry["state"] = "ERROR"
                        entry["why"] = str(exc)[:160]
        except Exception as exc:
            entry["state"] = "ERROR"
            entry["why"] = str(exc)[:160]
        out[name] = entry
    return out


# ----------------------------------------------------------------------------- pull
def poll_once() -> Dict[str, Any]:
    """Un ciclo: fetch -> (si cambia) reset -> hooks -> raices -> recarga in-place."""
    repo_dir = os.getenv("AUTO_PULL_REPO_DIR", DEFAULT_REPO_DIR)
    branch = os.getenv("AUTO_PULL_BRANCH") or os.getenv("GITHUB_BRANCH") or DEFAULT_BRANCH
    STATE["repo_dir"] = repo_dir
    STATE["branch"] = branch
    res: Dict[str, Any] = {"ok": False, "changed": False, "branch": branch}
    if not (Path(repo_dir) / ".git").is_dir():
        res["error"] = "no hay clon en %s" % repo_dir
        return res
    rc, out, err = _git(["fetch", "--depth", "1", "origin", branch], cwd=repo_dir, timeout=120)
    if rc != 0:
        res["error"] = ("fetch fallo: %s" % err)[:200]
        STATE["errors"].append(res["error"])
        return res
    rc, sha, _e = _git(["rev-parse", "FETCH_HEAD"], cwd=repo_dir)
    if rc != 0 or not sha:
        res["error"] = "no se pudo leer FETCH_HEAD"
        return res
    rc, head, _e = _git(["rev-parse", "HEAD"], cwd=repo_dir)
    STATE["head"] = head
    res["head"] = head
    res["remote"] = sha
    if sha == head:
        res["ok"] = True
        return res
    # ---- hay commit nuevo: reset (con vuelta atras si falla)
    rc, _o, err = _git(["reset", "--hard", sha], cwd=repo_dir, timeout=180)
    if rc != 0:
        _git(["reset", "--hard", head or sha], cwd=repo_dir)
        res["error"] = ("reset fallo: %s" % err)[:200]
        STATE["errors"].append(res["error"])
        return res
    res["changed"] = True
    res["from"] = head
    res["to"] = sha
    root = repo_root() or Path(repo_dir)
    res["hooks"] = _post_reset_hooks(root)
    try:
        res["roots"] = refresh_roots(root)
        STATE["roots"] = res["roots"]
    except Exception as exc:
        res["roots"] = {"error": str(exc)[:200]}
    STATE["pulls"] = int(STATE.get("pulls", 0)) + 1
    STATE["last_applied_sha"] = sha
    STATE["last_pull_at"] = time.time()
    _state_save()
    res["ok"] = True
    return res


# ----------------------------------------------------------------------------- reload
def reload_in_place() -> None:
    """Recarga el proceso SIN reiniciar el Space (execv sustituye la imagen del proceso)."""
    import sys
    STATE["reloads"] = int(STATE.get("reloads", 0)) + 1
    _state_save()
    print("[auto-pull] recarga in-place: %s" % " ".join(sys.argv), flush=True)
    sys.stdout.flush()
    os.execv(sys.executable, [sys.executable] + list(sys.argv))


# ----------------------------------------------------------------------------- hilo
def _loop(interval: int, on_reload) -> None:
    while True:
        try:
            res = poll_once()
            STATE["last_poll_at"] = time.time()
            _state_save()
            if res.get("changed"):
                print("[auto-pull] commit nuevo aplicado: %s -> %s (raices: %s)" % (
                    (res.get("from") or "?")[:12], (res.get("to") or "?")[:12],
                    ",".join("%s=%s" % (k, v.get("state")) for k, v in (res.get("roots") or {}).items())),
                    flush=True)
                if on_reload is not None:
                    on_reload()
                else:
                    reload_in_place()
                return  # el proceso se sustituye: el nuevo proceso arranca otro hilo
        except Exception as exc:  # fail-closed: el watcher nunca tumba el Space
            STATE["errors"].append(str(exc)[:200])
        time.sleep(interval)


def start(on_reload=None, interval: Optional[int] = None) -> bool:
    """Arranca el watcher. Devuelve False si no procede (p.ej. fuera de un Space)."""
    if os.getenv("AUTO_PULL", "1").lower() in ("0", "false", "no", "off"):
        return False
    repo_dir = os.getenv("AUTO_PULL_REPO_DIR", DEFAULT_REPO_DIR)
    if not (Path(repo_dir) / ".git").is_dir():
        return False
    if os.getenv("AUTO_PULL_DISABLE", "") == "1":
        return False
    interval = int(interval or os.getenv("AUTO_PULL_INTERVAL_S", DEFAULT_INTERVAL))
    STATE.update({"enabled": True, "interval_s": interval, "started_at": time.time(),
                  "branch": os.getenv("AUTO_PULL_BRANCH") or os.getenv("GITHUB_BRANCH") or DEFAULT_BRANCH,
                  "repo_dir": repo_dir})
    _state_load()
    rc, head, _e = _git(["rev-parse", "HEAD"], cwd=repo_dir)
    STATE["head"] = head
    t = threading.Thread(target=_loop, args=(interval, on_reload), name="auto-pull", daemon=True)
    t.start()
    print("[auto-pull] watcher ON (rama %s, cada %ss, repo %s)" % (STATE["branch"], interval, repo_dir), flush=True)
    return True


def status() -> Dict[str, Any]:
    out = dict(STATE)
    out["errors"] = (out.get("errors") or [])[-5:]
    return out


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        print(json.dumps(poll_once(), ensure_ascii=False, indent=2))
    elif len(sys.argv) > 1 and sys.argv[1] == "--status":
        print(json.dumps(status(), ensure_ascii=False, indent=2))
    else:
        start()
        while True:
            time.sleep(60)
