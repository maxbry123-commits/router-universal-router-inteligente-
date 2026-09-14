import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from router import classify, select


def test_classify_contradiction():
    ids = [mid for mid, _ in classify("CI says PASS but runtime FAIL: contradiction")]
    assert "M19" in ids or "C03" in ids


def test_parallel_width():
    routes = select("need decision simulation and recovery", parallel_width=2)
    assert 1 <= len(routes) <= 2


def test_registry_tier_a():
    routes = select("source of truth authority", parallel_width=1)
    assert routes[0].method_id == "C01" and routes[0].tier == "A" and routes[0].target_records == 20
