from __future__ import annotations
import json
from pathlib import Path
from ..contracts import Status
from ._common import index_evidence, iter_files, result

LAYER = "L02_XRAY_DOCUMENTS"


def run(node, ctx):
    root = Path(ctx.get("repo_root") or "")
    if not ctx.get("repo_root") or not root.is_dir():
        return result(node, Status.INCONCLUSIVE, gaps=["L02_INPUT_GAP:repo_root"])
    files = list(iter_files(root, (".md", ".json", ".yaml", ".yml")))
    gaps = []
    for f in files:
        if f.suffix == ".json":
            try:
                json.loads(f.read_text(encoding="utf-8"))
            except Exception:
                gaps.append(f"JSON_INVALID:{f.relative_to(root).as_posix()}")
    by_ext: dict[str, int] = {}
    for f in files:
        by_ext[f.suffix] = by_ext.get(f.suffix, 0) + 1
    status = Status.PASS if files and not gaps else Status.INCONCLUSIVE
    if not files:
        gaps.append("NO_DOCUMENTS_FOUND")
    return result(node, status, output={"documents": len(files), "by_ext": by_ext},
                  evidence=[index_evidence("docs_index", root, files)] if files else [], gaps=gaps[:50])
