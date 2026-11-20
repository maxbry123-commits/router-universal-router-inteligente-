"""patch_agents_real.py — G4: deja los 2 agentes importables con el nombre que
exige la validacion del bloque (ChatA / ChatB).

Los agentes YA son implementaciones reales (ChatAArchitect / ChatBImplementer con
consejo, descomposicion, collector de continuaciones y tool-call validator).
Lo que faltaba era el alias publico que exige el bloque. Idempotente: si el
alias existe, no hace nada. No reescribe la implementacion.
"""
import re, sys
from pathlib import Path

ALIASES = [
    ("router_llm_hf/chat_a_architect.py", "ChatAArchitect", "ChatA",
     '"""G4: alias publico del agente arquitecto (la implementacion no cambia)."""'),
    ("router_llm_hf/chat_b_implementer.py", "ChatBImplementer", "ChatB",
     '"""G4: alias publico del agente implementador (la implementacion no cambia)."""'),
]

def patch(path, cls, alias, doc):
    p = Path(path)
    if not p.exists():
        print(f"  SKIP {path} (no existe)"); return False
    txt = p.read_text(encoding="utf-8")
    if re.search(rf"^{alias}\s*=", txt, re.M):
        print(f"  YA_PATCHED {path}"); return False
    if not re.search(rf"^class {cls}\b", txt, re.M):
        print(f"  SKIP {path} (no hay class {cls})"); return False
    p.write_text(txt.rstrip("\n") + f"\n\n\n{alias} = {cls}\n", encoding="utf-8")
    print(f"  PATCHED {path}: {alias} = {cls}")
    return True

if __name__ == "__main__":
    changed = sum(patch(*a) for a in ALIASES)
    print(f"AGENTS_PATCHED={changed}")
    sys.exit(0)
