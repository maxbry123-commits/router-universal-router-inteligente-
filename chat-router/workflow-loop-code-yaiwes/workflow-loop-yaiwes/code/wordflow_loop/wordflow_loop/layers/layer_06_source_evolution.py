from __future__ import annotations
import json
from pathlib import Path
from ..contracts import Status
from ._common import file_evidence, missing_inputs, result

LAYER = "L06_SOURCE_EVOLUTION"


def run(node, ctx):
    miss = missing_inputs(ctx, ["manifest_before", "manifest_after"])
    if miss:
        return result(node, Status.INCONCLUSIVE, gaps=[f"L06_INPUT_GAP:{k}" for k in miss])
    pb, pa = Path(ctx["manifest_before"]), Path(ctx["manifest_after"])
    if not (pb.is_file() and pa.is_file()):
        return result(node, Status.INCONCLUSIVE, gaps=["MANIFEST_MISSING"])
    before, after = json.loads(pb.read_text(encoding="utf-8")), json.loads(pa.read_text(encoding="utf-8"))
    added = sorted(set(after) - set(before))
    removed = sorted(set(before) - set(after))
    changed = sorted(k for k in set(before) & set(after) if before[k] != after[k])
    return result(node, Status.PASS, output={"added": len(added), "removed": len(removed), "changed": len(changed),
                  "sample": (added + removed + changed)[:20]},
                  evidence=[file_evidence(pb, "manifest_before"), file_evidence(pa, "manifest_after")])
