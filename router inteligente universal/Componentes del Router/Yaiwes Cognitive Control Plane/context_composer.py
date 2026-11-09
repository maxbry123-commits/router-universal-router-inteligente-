from __future__ import annotations
from typing import List
from contracts import ContextItem, ContextPack, ContextRequest
from source_of_truth import authority_of


def estimate_tokens(text: str) -> int:
    return max(1, (len(text) + 3) // 4)


def _score(item: ContextItem) -> float:
    authority = authority_of(item.source) / 500.0
    return (0.45 * item.relevance) + (0.35 * item.priority) + (0.20 * authority)


def compose(req: ContextRequest) -> ContextPack:
    if req.budget_tokens <= 0:
        raise ValueError("budget_tokens must be positive")
    # Deduplicate semantically-identical payloads by normalized text.
    seen = set()
    candidates: List[ContextItem] = []
    for item in sorted(req.items, key=_score, reverse=True):
        key = " ".join(item.text.lower().split())
        if key in seen:
            continue
        seen.add(key)
        candidates.append(item)
    selected: List[ContextItem] = []
    used = 0
    truncated = False
    for item in candidates:
        cost = estimate_tokens(item.text)
        if used + cost > req.budget_tokens:
            truncated = True
            continue
        selected.append(item)
        used += cost
    return ContextPack(req.request_id, selected, used, truncated)
