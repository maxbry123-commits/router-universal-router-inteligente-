from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable, List
from contracts import Evidence
from source_of_truth import authority_of

@dataclass(frozen=True)
class ConsistencyResult:
    state: str
    action: str
    conflicts: List[str]


def check(evidence: Iterable[Evidence]) -> ConsistencyResult:
    items = list(evidence)
    if not items:
        return ConsistencyResult("UNKNOWN", "RECONCILE", ["NO_EVIDENCE"])
    values = {}
    for e in items:
        values.setdefault(str(e.value), []).append(e)
    if len(values) == 1:
        return ConsistencyResult("VALID", "CONTINUE", [])
    # Any disagreement involving authoritative observations is a deterministic conflict.
    ordered = sorted(items, key=lambda e: authority_of(e.source), reverse=True)
    conflict = [f"{e.source}={e.value}" for e in ordered]
    return ConsistencyResult("CONFLICTED", "RECONCILE", conflict)
