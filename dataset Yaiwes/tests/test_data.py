import json
from collections import Counter
from itertools import islice
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = {"id","method_id","method","tier","category","source","commit","added_at","trigger","problem","correct_method","verification","tags"}
EXPECTED = {
    "A": Counter({"debugging":10,"causal":5,"error":3,"counterexample":2}),
    "B": Counter({"debugging":5,"causal":3,"error":1,"counterexample":1}),
    "C": Counter({"debugging":3,"causal":2,"error":1,"counterexample":1}),
}


def load_contracts():
    reg=json.loads((ROOT/"registry.json").read_text(encoding="utf-8"))
    idx=json.loads((ROOT/"indexes/shard_index.json").read_text(encoding="utf-8"))
    return reg, idx


def tier_of(reg, method_id):
    if method_id in reg["tier_A"]: return "A"
    if method_id in reg["tier_C"]: return "C"
    return reg["default_tier"]


def method_rows(loc):
    path=ROOT/loc["path"]
    assert path.exists(), f"missing shard {path}"
    start=int(loc["start_line"]); count=int(loc["count"])
    with path.open("r", encoding="utf-8") as fh:
        rows=[json.loads(line) for line in islice(fh,start-1,start-1+count)]
    assert len(rows)==count, f"short range {path}:{start} {len(rows)}/{count}"
    return rows


def test_registry_and_index_contract():
    reg,idx=load_contracts()
    assert reg["logical_methods"]==107
    assert reg["target_records"]==1139
    assert idx["records"]==1139
    assert len(idx["methods"])==107
    registered={mid for group in reg["groups"].values() for mid,_ in group}
    assert registered==set(idx["methods"])


def test_all_1139_records_match_exact_tier_quotas_and_provenance():
    reg,idx=load_contracts()
    seen=set(); total=0
    for method_id,loc in idx["methods"].items():
        rows=method_rows(loc)
        tier=tier_of(reg,method_id)
        assert len(rows)==reg["tier_rules"][tier]["records"]
        counts=Counter()
        for row in rows:
            missing=REQUIRED-set(row)
            assert not missing, f"{row.get('id')} missing {sorted(missing)}"
            assert row["method_id"]==method_id
            assert row["tier"]==tier
            assert row["id"] not in seen, f"duplicate id {row['id']}"
            seen.add(row["id"])
            counts[row["category"]]+=1
            assert row["source"] and row["commit"] and row["added_at"]
            assert isinstance(row["correct_method"],list) and row["correct_method"]
            assert isinstance(row["tags"],list) and row["tags"]
        assert counts==EXPECTED[tier], f"{method_id}: {counts} != {EXPECTED[tier]}"
        total += len(rows)
    assert total==1139
    assert len(seen)==1139


def test_legacy_seed_files_are_not_canonical():
    manifest=(ROOT/"manifest.yaml").read_text(encoding="utf-8")
    assert "segmented_jsonl" in manifest
    assert "SUPERSEDED_NOT_ROUTED" in manifest
    assert "indexes/shard_index.json" in manifest
