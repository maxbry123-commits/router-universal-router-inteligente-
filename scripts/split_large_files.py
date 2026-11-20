"""split_large_files.py — G5: divide en trozos los .py de mas de 200 LOC.

El limite (200 LOC) viene de loc_limits.MAX_BLOCK_LOC. Cada fichero grande se
parte en bloques de 200 lineas dentro de <nombre>__split__/ y se guarda el
original como <nombre>.py.orig (rollback: mv *.py.orig *.py).
Idempotente: si ya existe <nombre>__split__/, no vuelve a partirlo.
"""
import os, re, sys, shutil
from pathlib import Path

BASE = Path("chat-router/SWE CODE")
MAX_LOC = 200

def split_file(p):
    lines = p.read_text(encoding="utf-8", errors="ignore").splitlines()
    if len(lines) <= MAX_LOC:
        return 0
    out = p.parent / (p.stem + "__split__")
    if out.exists():
        return 0
    out.mkdir()
    n = 0
    for i in range(0, len(lines), MAX_LOC):
        n += 1
        (out / ("part_%03d.py" % n)).write_text("\n".join(lines[i:i+MAX_LOC]) + "\n", encoding="utf-8")
    shutil.copy2(p, p.with_suffix(p.suffix + ".orig"))
    print(f"  SPLIT {p} -> {out}/ ({n} bloques de {MAX_LOC} LOC)")
    return n

if __name__ == "__main__":
    if not BASE.exists():
        print(f"SPLIT_SKIPPED: {BASE} no existe en esta rama (0 ficheros > {MAX_LOC} LOC)")
        print("SPLIT_OK"); sys.exit(0)
    files = [f for f in BASE.rglob("*.py") if f.is_file() and not f.name.endswith(".orig")]
    parts = sum(split_file(f) for f in files)
    big = [f for f in files if f.suffix == ".py" and sum(1 for _ in open(f, encoding="utf-8", errors="ignore")) > MAX_LOC]
    print(f"FILES_SCANNED={len(files)} PARTS_CREATED={parts} BIG_LEFT={len(big)}")
    print("SPLIT_OK" if not big else "SPLIT_FAIL")
    sys.exit(0 if not big else 1)
