from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List

@dataclass(frozen=True)
class Evidence:
    source: str
    value: Any
    provenance: str = ""
    freshness: int = 0
    confidence: float = 1.0

@dataclass(frozen=True)
class ContextItem:
    id: str
    text: str
    priority: float = 0.5
    source: str = "repo"
    relevance: float = 0.5

@dataclass
class ContextRequest:
    request_id: str
    query: str
    items: List[ContextItem] = field(default_factory=list)
    budget_tokens: int = 2048

@dataclass
class ContextPack:
    request_id: str
    selected: List[ContextItem]
    estimated_tokens: int
    truncated: bool

@dataclass(frozen=True)
class ProposedAction:
    action: str
    capability: str
    irreversible: bool = False
    sandboxed: bool = False
    approved: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

INPUT_SHARK_RESOLUTION = {
    "fusion": False,
    "status": "external_upstream_not_implemented",
    "reason": "No authoritative inspectable Input Shark contract found; fail-closed forbids inventing one.",
    "context_composer_contract": "ContextRequest -> ContextPack",
}
