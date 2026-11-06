# ops/git_push_safe.py
"""Empuje robusto de historiales grandes (rama reescrita).

Reglas:
  - El lease se renueva tras CADA tramo: refs/heads/<branch>:<sha-publicado>.
  - Si la ref no existe, lease vacío (crea solo si no existe).
  - Reintentos con backoff exponencial (15/30/60 s) y subdivisión del tramo.
  - Si el error es de tamaño (500/sideband/disconnect), subdivide SIN esperar.
  - Post-verificación con ls-remote: el push no se declara OK si el SHA remoto no coincide con HEAD.
  - Pre-chequeo de tamaño: si el total de packs supera 1.8 GiB, se fuerza troceo (GitHub corta a 2 GiB).
"""
import os, time, subprocess
from common import sh  # wrapper existente: args, cwd=, check=False

PUSH_LIMIT_KIB = 1_800_000            # ~1.76 GiB, margen bajo los 2 GiB de GitHub
GIT_OPT = ["-c","http.version=HTTP/1.1",
           "-c","http.postBuffer=524288000",
           "-c","http.lowSpeedLimit=0",
           "-c","http.lowSpeedTime=999999"]

def _sh(args, cwd):
    return sh(args, cwd=cwd, check=False)

def _ls_remote_sha(repo, branch):
    r = _sh(["git","ls-remote","origin",f"refs/heads/{branch}"], cwd=repo)
    if r.returncode != 0 or not r.stdout.strip():
        return None
    return r.stdout.split()[0]

def _lease_for(branch, remote_sha):
    return f"refs/heads/{branch}:{remote_sha or ''}"

def _push_once(repo, branch, refspec, lease):
    return _sh(["git"]+GIT_OPT+["push","origin",refspec,f"--force-with-lease={lease}"], cwd=repo)

def _backoff(attempt):
    base = int(os.environ.get("PUSH_BACKOFF_BASE","15"))
    if base <= 0: return
    time.sleep(min(60, base * (2 ** (attempt-1))))

def _is_size_error(msg):
    m = (msg or "").lower()
    return "500" in m or "sideband" in m or "unexpected disconnect" in m

def estimate_pack_kib(repo):
    """Tamaño total de packs en KiB (git count-objects -v, campo size-pack)."""
    out = _sh(["git","count-objects","-v"], cwd=repo).stdout
    for line in out.splitlines():
        if line.startswith("size-pack:"):
            try: return int(line.split(":",1)[1].strip())
            except ValueError: return None
    return None

def _verify(repo, branch):
    head = _sh(["git","rev-parse","HEAD"], cwd=repo).stdout.strip()
    remote = _ls_remote_sha(repo, branch)
    if remote == head:
        return True, f"verificado: {head[:12]}"
    return False, f"HEAD={head[:12]} remoto={(remote or 'None')[:12]}"

def push_in_chunks(repo, branch, chunk_size=None, max_attempts=3):
    """Empuja HEAD a origin/refs/heads/<branch> con lease renovado por tramo."""
    shas = _sh(["git","rev-list","--reverse","HEAD"], cwd=repo).stdout.split()
    if not shas:
        return False, "sin commits"

    kib = estimate_pack_kib(repo) or 0
    over_limit = kib > PUSH_LIMIT_KIB

    if chunk_size is None:
        chunk_size = max(1, len(shas)//10)

    # 1) intento único (rápido si el pack cabe bajo el límite de GitHub)
    if not over_limit:
        lease = _lease_for(branch, _ls_remote_sha(repo, branch))
        r = _push_once(repo, branch, f"HEAD:refs/heads/{branch}", lease)
        if r.returncode == 0:
            ok, det = _verify(repo, branch)
            return (True, "push único OK, "+det) if ok else (False, "push único pero verificación: "+det)

    # 2) troceo adaptativo
    i = 0
    last_detail = ""
    while i < len(shas):
        lote = shas[i:i+chunk_size]
        tip = lote[-1]
        pushed = False
        for attempt in range(1, max_attempts+1):
            lease = _lease_for(branch, _ls_remote_sha(repo, branch))
            r = _push_once(repo, branch, f"{tip}:refs/heads/{branch}", lease)
            if r.returncode == 0:
                pushed = True
                break
            last_detail = (r.stdout + r.stderr)[-300:]
            # si es error de tamaño y hay margen para subdividir, no esperes
            if _is_size_error(last_detail) and len(lote) > 1:
                break
            _backoff(attempt)
        if pushed:
            i += len(lote)
            continue
        if len(lote) > 1:
            chunk_size = max(1, len(lote)//2)
            continue
        return False, last_detail

    ok, det = _verify(repo, branch)
    if ok:
        return True, f"publicado por tramos ({len(shas)} commits, paso {chunk_size})"
    return False, det
