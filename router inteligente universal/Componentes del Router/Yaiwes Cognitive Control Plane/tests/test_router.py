import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from router import classify, select, retrieve, route_and_retrieve


def test_classify_contradiction():
    ids = [mid for mid, _ in classify("CI says PASS but runtime FAIL: contradiction")]
    assert "M19" in ids or "C03" in ids


def test_parallel_width():
    routes = select("need decision simulation and recovery", parallel_width=2)
    assert 1 <= len(routes) <= 2


def test_registry_tier_a():
    routes = select("source of truth authority", parallel_width=1)
    assert routes[0].method_id == "C01" and routes[0].tier == "A" and routes[0].target_records == 20


def test_retrieve_reads_exact_method_range():
    rows = retrieve("Y26")
    assert len(rows) == 20
    assert {r["method_id"] for r in rows} == {"Y26"}
    assert {r["category"] for r in rows} == {"debugging","causal","error","counterexample"}


def test_retrieve_category_limits():
    rows = retrieve("M23", category_limits={"debugging":2,"causal":1,"error":1,"counterexample":1})
    assert len(rows) == 5
    assert sum(r["category"] == "debugging" for r in rows) == 2
    assert sum(r["category"] == "causal" for r in rows) == 1


def test_route_and_retrieve_small_context_pack_source():
    result = route_and_retrieve("need recovery and evidence gate", parallel_width=2,
                                category_limits={"debugging":2,"causal":1,"error":1,"counterexample":1})
    assert 1 <= len(result) <= 2
    assert all(1 <= len(rows) <= 5 for rows in result.values())
