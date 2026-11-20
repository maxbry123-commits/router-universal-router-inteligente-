"""remove_riu_router.py — Crea branch y elimina refs a riu-router de codigo.
Respeta docs (no borra historia). --branch: crea fix/remove-riu-router y commit.

ADAPTACION 4 (el regex del bloque tambien pilla env vars legitimas): el patron
riu[-_]?router case-insensitive coincide con RIU_ROUTER_API_KEY (variable de
entorno real del banco), no con el Space muerto. Sin proteccion, el script
romperia el cableado de credenciales. Se protegen los nombres de env var
(RIU_ROUTER_*) y los 3 scripts de esta misma gap (si no, se reescriben a si
mismos y el regex queda inservible).
"""
import os, sys, re, subprocess
from pathlib import Path

PATTERN = re.compile(r"riu[-_]?router", re.I)
PROTECT = re.compile(r"RIU_ROUTER_[A-Z0-9_]+", re.I)
SELF = {"remove_riu_router.py", "find_old_router.py", "commit_g3.py"}
SKIP = {".git", "node_modules", "__pycache__", ".venv", "venv"}
CODE_EXT = {".py", ".js", ".ts", ".json", ".yaml", ".yml", ".html"}

def run(cmd, check=True):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if check and r.returncode != 0: print(r.stderr); sys.exit(r.returncode)
    return r.stdout

if "--branch" in sys.argv:
    run(["git", "checkout", "-b", "fix/remove-riu-router"])

removed = 0
for root, dirs, files in os.walk("."):
    dirs[:] = [d for d in dirs if d not in SKIP]
    for f in files:
        p = Path(root) / f
        if p.suffix not in CODE_EXT: continue
        if f in SELF: continue
        try: txt = p.read_text(encoding="utf-8")
        except: continue
        if not PATTERN.search(txt): continue
        protected = []
        def _stash(m):
            protected.append(m.group(0)); return "\x00PROT%d\x00" % (len(protected)-1)
        tmp_txt = PROTECT.sub(_stash, txt)
        new = PATTERN.sub("# REMOVED: riu-router ref", tmp_txt)
        for i, val in enumerate(protected):
            new = new.replace("\x00PROT%d\x00" % i, val)
        p.write_text(new, encoding="utf-8")
        removed += 1; print(f"  CLEANED {p}")

print(f"FILES_CLEANED={removed}")
run(["git", "add", "-A"], check=False)
run(["git", "commit", "-m", "chore(router): remove riu-router residual from code (G3)"], check=False)
