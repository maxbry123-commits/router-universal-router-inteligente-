import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHARDS = ROOT / "data" / "shards"
REQUIRED = {"id","method_id","method","tier","category","source","commit","added_at","trigger","problem","correct_method","verification","tags"}
EXPECTED = {
    "A": Counter({"debugging":10,"causal":5,"error":3,"counterexample":2}),
    "B": Counter({"debugging":5,"causal":3,"error":1,"counterexample":1}),
    "C": Counter({"debugging":3,"causal":2,"error":1,"counterexample":1}),
}


def records():
    for path in sorted(SHARDS.glob("*.jsonl")):
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            yield path, lineno, json.loads(line)


def test_each_shard_record_matches_contract():
    seen = set()
    for path, lineno, row in records():
        missing = REQUIRED - set(row)
        assert not missing, f"{path}:{lineno} missing {sorted(missing)}"
        assert row["id"] not in seen, f"duplicate id {row['id']}"
        seen.add(row["id"])
        assert row["tier"] in EXPECTED
        assert row["category"] in EXPECTED[row["tier"]]
        assert isinstance(row["correct_method"], list) and row["correct_method"]
        assert isinstance(row["tags"], list) and row["tags"]
        assert row["source"] and row["commit"] and row["added_at"]


def test_completed_methods_have_exact_tier_distribution():
    by_method = defaultdict(list)
    for path, lineno, row in records():
        by_method[row["method_id"]].append((path, lineno, row))
    for method_id, items in by_method.items():
        tiers = {x[2]["tier"] for x in items}
        assert len(tiers) == 1, f"{method_id} mixed tiers {tiers}"
        tier = next(iter(tiers))
        counts = Counter(x[2]["category"] for x in items)
        total_expected = sum(EXPECTED[tier].values())
        if len(items) == total_expected:
            assert counts == EXPECTED[tier], f"{method_id}: {counts} != {EXPECTED[tier]}"
        else:
            # Partial shards are allowed while a node is IN_PROGRESS, but cannot exceed tier quota.
            for category, count in counts.items():
                assert count <= EXPECTED[tier][category], f"{method_id} exceeds {category} quota"
            assert len(items) < total_expected, f"{method_id} invalid total {len(items)}"
