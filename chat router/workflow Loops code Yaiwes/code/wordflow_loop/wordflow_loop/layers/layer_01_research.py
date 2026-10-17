from __future__ import annotations
from pathlib import Path
from ..contracts import Evidence, Status
from ._common import file_evidence, index_evidence, iter_files, result

LAYER = "L01_RESEARCH"


def run(node, ctx):
    sources = ctx.get("research_sources") or []
    if not sources:
        return result(node, Status.INCONCLUSIVE, gaps=["L01_INPUT_GAP:research_sources"])
    ev, gaps = [], []
    for s in sources:
        p = Path(s)
        if p.is_file():
            ev.append(file_evidence(p, "source_file"))
        elif p.is_dir():
            ev.append(index_evidence("source_dir", p, list(iter_files(p, (".md", ".json", ".yaml", ".yml", ".py", ".txt")))))
        else:
            gaps.append(f"SOURCE_MISSING:{s}")
    status = Status.PASS if ev and not gaps else Status.INCONCLUSIVE
    return result(node, status, output={"found": len(ev), "missing": len(gaps)}, evidence=ev, gaps=gaps)
