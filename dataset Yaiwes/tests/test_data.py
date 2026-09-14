import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = {"id","method_id","method","tier","category","source","commit","added_at","trigger","problem","correct_method","verification","tags"}
FILES = [ROOT/"data/mythos.jsonl", ROOT/"data/yaiwes.jsonl", ROOT/"data/meta_runtime.jsonl", ROOT/"data/cognitive_control.jsonl"]


def load_records():
    out=[]
    for path in FILES:
        assert path.exists(), f"missing {path}"
        for n,line in enumerate(path.read_text(encoding="utf-8").splitlines(),1):
            if not line.strip():
                continue
            row=json.loads(line)
            missing=REQUIRED-set(row)
            assert not missing, f"{path}:{n} missing {sorted(missing)}"
            out.append(row)
    return out


def test_registry_contract():
    reg=json.loads((ROOT/"registry.json").read_text(encoding="utf-8"))
    assert reg["logical_methods"] == 107
    assert reg["target_records"] == 1139
    assert len(reg["tier_A"]) == 12
    assert len(reg["tier_C"]) == 17


def test_records_have_unique_ids_and_provenance():
    rows=load_records()
    ids=[r["id"] for r in rows]
    assert len(ids) == len(set(ids))
    assert all(r["source"] and r["commit"] and r["added_at"] for r in rows)


def test_final_target_count():
    # Deliberately fails until dataset population/compaction is complete.
    reg=json.loads((ROOT/"registry.json").read_text(encoding="utf-8"))
    rows=load_records()
    assert len(rows) == reg["target_records"], f"population incomplete: {len(rows)}/{reg['target_records']}"
