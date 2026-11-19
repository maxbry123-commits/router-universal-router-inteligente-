"""find_old_router.py — Reporta referencias a riu-router. NO bloquea.
--report: lista matches y sale 0 si quedan <= 2 (docs), 1 si > 2 en codigo.
"""
import os, sys, re
from pathlib import Path

PATTERN = re.compile(r"riu[-_]?router", re.I)
SKIP = {".git", "node_modules", "__pycache__", ".venv", "venv"}
CODE_EXT = {".py", ".js", ".ts", ".json", ".yaml", ".yml", ".html"}
DOC_EXT = {".md", ".txt", ".rst"}

code_hits, doc_hits = [], []
for root, dirs, files in os.walk("."):
    dirs[:] = [d for d in dirs if d not in SKIP]
    for f in files:
        p = Path(root) / f
        if p.suffix not in CODE_EXT | DOC_EXT: continue
        try: txt = p.read_text(encoding="utf-8", errors="ignore")
        except: continue
        if PATTERN.search(txt):
            (code_hits if p.suffix in CODE_EXT else doc_hits).append(str(p))

print(f"CODE_HITS={len(code_hits)} DOC_HITS={len(doc_hits)}")
for h in code_hits: print(f"  CODE {h}")
for h in doc_hits:  print(f"  DOC  {h}")

if "--report" in sys.argv and len(code_hits) > 2:
    print("RIU_RESIDUAL"); sys.exit(1)
print("RIU_CLEAN"); sys.exit(0)
