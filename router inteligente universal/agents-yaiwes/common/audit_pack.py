"""Builds the auditor's evidence packs (deterministic, no LLM):
 - packs/pack-1..4.md: the Director's LITERAL words of every `Claude notas/INPUT-VERBATIM-2026-09-2*.md` (his message only: from the first `---`
   to the queue; pasted external documents are cut), split in 4 packs;
 - packs/agents_state.md: what each agent's Crazy Wall says (steps, status, gaps, route).
Run (from anywhere): python audit_pack.py"""
from __future__ import annotations

import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]  # agents-yaiwes
REPO = HERE.parents[1]
NOTES = REPO / "Claude notas"
OUT = HERE / "agent-5-auditor" / "packs"
PER_FILE, PACKS = 3500, 4


def director_text(path: Path) -> str:
    t = path.read_text(encoding="utf-8", errors="ignore")
    a, b = t.find("\n---\n"), t.find("\n## Cola")
    body = t[a + 5: b if b > a else None] if a >= 0 else t
    m = re.search(r"\n## (Documento|Adjunto)", body)
    if m:
        body = body[: m.start()]
    return body.strip()[:PER_FILE]


def agents_state() -> str:
    rows = []
    for d in sorted(HERE.glob("agent-*")):
        if not d.is_dir() or d.name == "agent-5-auditor":
            continue
        top = json.loads((d / "crazy_wall.state.json").read_text(encoding="utf-8")) if (d / "crazy_wall.state.json").exists() else {}
        rows.append(f"## {d.name}: estado={top.get('status', '?')} marco={top.get('framework', '?')} pasos_cerrados={top.get('completed', [])} ruta={top.get('route', '?')}")
        for s in sorted((d / "steps").glob("*/crazy_wall.state.json")) if (d / "steps").exists() else []:
            st = json.loads(s.read_text(encoding="utf-8"))
            rows.append(f"- paso {s.parent.name}: {st.get('status')} modelo={st.get('model', '-')} gaps={'; '.join(st.get('gaps', []))[:200] or '-'}")
            for f in sorted((s.parent / "results").glob("*")) if (s.parent / "results").exists() else []:
                rows.append(f"  - entregable: {f.relative_to(REPO)}")
    return "\n".join(rows) or "(sin agentes)"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    files = sorted(NOTES.glob("INPUT-VERBATIM-2026-09-2*.md"))
    blocks = [f"=== ARCHIVO: Claude notas/{p.name} ===\n{director_text(p)}\n" for p in files]
    target = max(1, sum(len(b) for b in blocks) // PACKS + 1)
    packs, cur = [[] for _ in range(PACKS)], 0
    for b in blocks:
        i = min(PACKS - 1, cur // target)
        packs[i].append(b)
        cur += len(b)
    for i, pk in enumerate(packs, 1):
        (OUT / f"pack-{i}.md").write_text("\n".join(pk) or "(vacío)", encoding="utf-8")
    (OUT / "agents_state.md").write_text(agents_state()[:12000], encoding="utf-8")
    print(f"packs: {[len(''.join(p)) for p in packs]} caracteres; archivos fuente: {len(files)}")


if __name__ == "__main__":
    main()
