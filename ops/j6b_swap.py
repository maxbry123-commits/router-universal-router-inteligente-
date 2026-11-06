"""ops/j6b_swap.py — N4 del DAG: intercambio de `main` tras la reescritura de historial.

MODOS
  MODE=swap     : push de la rama reescrita (main-clean) a `main` con --force-with-lease
                  sobre el tag `pre-reorg-<RUN_ID>` (el tag es el punto de rollback).
  MODE=rollback : main <- tag `pre-reorg-<RUN_ID>` con lease sobre el `main` actual.

GATES (FAIL_CLOSED)
  j6_rewrite PASS en el Dataset | el tag existe | main == tag (lease) | el push es accepted
  y `main` remoto == el commit publicado (read-back).

El token de GitHub viaja SOLO en cabeceras de entorno (GIT_CONFIG_* extraheader): nunca en
URL, argv, logs ni ficheros. `lease` = valor esperado de `main`; si `main` movio desde que
se leyo, el push se rechaza solo (no se pierde trabajo ajeno).
"""
from common import *
import json, pathlib

TAG = f"pre-reorg-{RUN_ID}"
SRC = os.environ.get("SWAP_SOURCE", "main-clean")   # rama reescrita por j6_rewrite


def _lsremote(d, ref):
    r = sh(["git", "-C", d, "ls-remote", "origin", ref], check=False)
    parts = r.stdout.split()
    return parts[0] if parts else ""


def main():
    mode = os.environ.get("MODE", "")
    repo = need("GH_REPO")
    # D-108: sin MODE explicito el job NO muta ninguna ref (fail-closed). Antes el valor por
    # defecto era "swap": si MODE noviajaba al contenedor, el job empuja a main sin pedirlo.
    # "swap" exige ademas SWAP_SOURCE explicito y el gate de lease.
    if mode not in ("swap","rollback"):
        check("mode_explicit",False,f"MODE={mode!r} (validos: swap|rollback)")
        finish({"flag":"MODE_INVALID","mode":mode})
        return
    if mode=="swap" and not os.environ.get("SWAP_SOURCE"):
        check("swap_source_explicit",False,"SWAP_SOURCE obligatorio en modo swap")
        finish({"flag":"MODE_INVALID","mode":mode})
        return
    j6 = json.load(open(dl("j6_rewrite", "result.json")))
    check("j6_rewrite_PASS", j6.get("status") == "PASS", j6.get("commit"))
    if mode == "swap" and not all(c["ok"] for c in CHECKS):
        finish({"flag": "PRECONDITION", "mode": mode})
    d = os.path.join(os.environ.get("WORK_DIR", "/workspace/work"), "swap-" + mode)
    pathlib.Path(d).mkdir(parents=True, exist_ok=True)
    if not os.path.isdir(os.path.join(d, ".git")):
        sh(["git", "init", "-q", d])
        sh(["git", "-C", d, "remote", "add", "origin", f"https://github.com/{repo}.git"])
    # La rama reescrita se trae COMPLETA (sin filtro): el push es force (historial reescrito)
    # y git necesita los objetos para enviarlo.
    sh(["git", "-C", d, "fetch", "--force", "origin", f"refs/heads/{SRC}:refs/heads/{SRC}"], check=False)
    sh(["git", "-C", d, "fetch", "--force", "origin", f"refs/tags/{TAG}"], check=False)
    src_sha = sh(["git", "-C", d, "rev-parse", f"refs/heads/{SRC}"], check=False).stdout.strip()
    tag_sha = sh(["git", "-C", d, "rev-parse", f"refs/tags/{TAG}^{{commit}}"], check=False).stdout.strip()
    main_sha = _lsremote(d, "refs/heads/main")
    check("source_branch_present", bool(src_sha), SRC)
    check("tag_exists", bool(tag_sha), TAG)
    if mode == "swap":
        # G9: la lease exige main == tag. Si main ya movio (commits de estado posteriores al
        # tag), la lease NO se puede cumplir con el sha del tag: el tag se re-apunta al HEAD
        # real de main (punto de rollback antes de la reescritura) en un paso previo y
        # explicito. Aqui solo se VERIFICA.
        check("main_equals_tag_lease", bool(tag_sha) and main_sha == tag_sha,
              f"main={main_sha[:12]} tag={tag_sha[:12]}")
        if not all(c["ok"] for c in CHECKS):
            finish({"flag": "LEASE", "mode": mode, "main": main_sha, "tag": tag_sha})
        r = sh(["git", "-C", d, "push", "origin", f"{src_sha}:refs/heads/main",
                f"--force-with-lease=main:{tag_sha}"], check=False)
        check("pushed_main_with_lease", r.returncode == 0, (r.stdout + r.stderr)[-300:])
        after = _lsremote(d, "refs/heads/main")
        check("main_equals_pushed_commit", after == src_sha, f"main={after[:12]} pushed={src_sha[:12]}")
        finish({"mode": mode, "source": SRC, "pushed": src_sha, "main_after": after,
                "tag": TAG, "tag_sha": tag_sha}, commit=src_sha)
    else:  # rollback
        check("tag_exists", bool(tag_sha), TAG)
        r = sh(["git", "-C", d, "push", "origin", f"{tag_sha}:refs/heads/main",
                f"--force-with-lease=main:{main_sha}"], check=False)
        check("rolled_back_to_tag", r.returncode == 0, (r.stdout + r.stderr)[-300:])
        after = _lsremote(d, "refs/heads/main")
        check("main_equals_tag", after == tag_sha, f"main={after[:12]} tag={tag_sha[:12]}")
        finish({"mode": mode, "rolled_back_to": tag_sha, "main_after": after, "tag": TAG},
               commit=tag_sha)


if __name__ == "__main__":
    run(main)
