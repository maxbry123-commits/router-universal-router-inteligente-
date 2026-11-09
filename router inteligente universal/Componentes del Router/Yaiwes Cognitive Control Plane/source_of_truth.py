from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable, Optional
from contracts import Evidence

AUTHORITY = {
    "runtime": 500,
    "test": 400,
    "repo": 300,
    "agent_inference": 200,
    "llm_text": 100,
}

@dataclass(frozen=True)
class Resolution:
    selected: Optional[Evidence]
    authority: int
    conflicted: bool
    reason: str


def authority_of(source: str) -> int:
    return AUTHORITY.get(source, 0)


def resolve(evidence: Iterable[Evidence]) -> Resolution:
    items = list(evidence)
    if not items:
        return Resolution(None, 0, False, "NO_EVIDENCE")
    ranked = sorted(items, key=lambda e: (authority_of(e.source), e.freshness, e.confidence), reverse=True)
    top = ranked[0]
    top_level = authority_of(top.source)
    peers = [e for e in ranked if authority_of(e.source) == top_level]
    conflicted = any(e.value != top.value for e in peers[1:])
    return Resolution(top, top_level, conflicted, "TOP_AUTHORITY_CONFLICT" if conflicted else "RESOLVED")
