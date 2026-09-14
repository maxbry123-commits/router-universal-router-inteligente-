from __future__ import annotations
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

REGISTRY_PATH = Path(__file__).resolve().parent.parent / "dataset Yaiwes" / "registry.json"

KEYWORDS = {
    "M07": ["goal", "objective", "objetivo", "decompose"],
    "M14": ["dependency", "dependencia", "dag", "block"],
    "M19": ["contradiction", "contradic", "conflict"],
    "M23": ["simulation", "simulacion", "scenario"],
    "M30": ["replan", "replanificar", "changed plan"],
    "M32": ["decision", "decidir", "choose", "elegir"],
    "Y26": ["recover", "recovery", "recuper", "resume"],
    "Y27": ["sheriff", "acceptance", "gate", "evidence"],
    "C01": ["source of truth", "authority", "fuente", "autoridad"],
    "C03": ["consistency", "consistencia", "ci=pass", "runtime=fail"],
    "C04": ["route", "router", "agent", "modelo"],
    "C05": ["policy", "permission", "permiso", "approve", "sandbox"],
}

@dataclass(frozen=True)
class Route:
    method_id: str
    score: float
    tier: str
    target_records: int


def load_registry(path: Path = REGISTRY_PATH) -> Dict:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _tier(registry: Dict, method_id: str) -> str:
    if method_id in registry["tier_A"]:
        return "A"
    if method_id in registry["tier_C"]:
        return "C"
    return registry.get("default_tier", "B")


def _records_for(registry: Dict, tier: str) -> int:
    return int(registry["tier_rules"][tier]["records"])


def classify(text: str) -> List[Tuple[str, float]]:
    q = text.lower()
    scores: Dict[str, float] = {}
    for method_id, words in KEYWORDS.items():
        hits = sum(1 for word in words if word in q)
        if hits:
            scores[method_id] = min(1.0, 0.35 + 0.18 * hits)
    if not scores:
        scores["M03"] = 0.40  # problem framing fallback, not arbitrary execution
    return sorted(scores.items(), key=lambda x: (-x[1], x[0]))


def select(text: str, parallel_width: int = 3, registry_path: Path = REGISTRY_PATH) -> List[Route]:
    if parallel_width < 1:
        raise ValueError("parallel_width must be >= 1")
    registry = load_registry(registry_path)
    out: List[Route] = []
    for method_id, score in classify(text)[:parallel_width]:
        tier = _tier(registry, method_id)
        out.append(Route(method_id, score, tier, _records_for(registry, tier)))
    return out
