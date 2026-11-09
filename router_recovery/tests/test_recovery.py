"""Pruebas del router recovery. Ejecutar desde la raiz del repo: python -m pytest router_recovery/tests -q"""
from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from router_recovery.checkpoint_store import CheckpointStore
from router_recovery.pydantic_models import DagSpec
from router_recovery.runner import Runner, load_dag

ROOT = Path(__file__).resolve().parents[2]


def node(nid, deps=(), handler="dispatch_architect", files=None, loc=40, max_loc=200, acc=("ok",)):
    return {
        "node_id": nid, "name": f"n{nid}", "role": "architect", "objective": "o",
        "root_ids": ["R1"], "files": files or [], "depends_on": list(deps),
        "estimated_loc": loc, "max_loc_per_block": max_loc, "acceptance": list(acc),
        "handler": handler,
    }


def dag(nodes):
    return {"mission_id": "m", "objective": "o", "nodes": nodes}


def test_cycle_rejected():
    with pytest.raises(ValidationError, match="ciclo"):
        DagSpec.model_validate(dag([node("N1", deps=["N2"]), node("N2", deps=["N1"])]))


def test_missing_dependency_rejected():
    with pytest.raises(ValidationError, match="inexistente"):
        DagSpec.model_validate(dag([node("N1", deps=["N9"])]))


def test_duplicate_id_rejected():
    with pytest.raises(ValidationError, match="duplicados"):
        DagSpec.model_validate(dag([node("N1"), node("N1")]))


def test_block_over_200_loc_rejected():
    with pytest.raises(ValidationError):
        DagSpec.model_validate(dag([node("N1", max_loc=201)]))


def test_empty_acceptance_rejected():
    with pytest.raises(ValidationError):
        DagSpec.model_validate(dag([node("N1", acc=())]))


def test_self_dependency_rejected():
    with pytest.raises(ValidationError):
        DagSpec.model_validate(dag([node("N1", deps=["N1"])]))


def test_topo_order_is_deterministic():
    spec = DagSpec.model_validate(dag([node("N3", deps=["N1"]), node("N2"), node("N1")]))
    from router_recovery.pydantic_models import topo_order
    assert topo_order(spec.nodes) == ["N1", "N2", "N3"]


def test_run_writes_start_and_done(tmp_path):
    target = tmp_path / "a"
    spec = DagSpec.model_validate(dag([node("N1", files=[{"path": str(target) + "/", "action": "create"}])]))
    store = CheckpointStore(tmp_path / "ck")
    r = Runner(store, spec.mission_id)
    r.start(spec)
    r.run(spec)
    events = [(e.node_id, e.event) for e in store.read_ledger()]
    assert events == [("N1", "node_start"), ("N1", "node_done")]
    assert target.is_dir()


def test_state_rebuilt_from_ledger_when_corrupt(tmp_path):
    spec = DagSpec.model_validate(dag([node("N1")]))
    store = CheckpointStore(tmp_path / "ck")
    Runner(store, spec.mission_id).run(spec)
    (tmp_path / "ck" / "STATE.json").write_text("{not json", encoding="utf-8")
    assert CheckpointStore(tmp_path / "ck").load_state()["phases"] == {"N1": "completa"}


def test_partial_ledger_line_is_ignored(tmp_path):
    spec = DagSpec.model_validate(dag([node("N1")]))
    store = CheckpointStore(tmp_path / "ck")
    Runner(store, spec.mission_id).run(spec)
    with store.ledger_path.open("a", encoding="utf-8") as f:
        f.write('{"ts": "x", "node_id": "N2", "eve')  # linea cortada por kill -9
    assert [e.node_id for e in store.read_ledger()] == ["N1", "N1"]


def test_unknown_handler_fail_closed(tmp_path):
    spec = DagSpec.model_validate(dag([node("N1", handler="foo")]))
    store = CheckpointStore(tmp_path / "ck")
    with pytest.raises(ValueError, match="handler desconocido"):
        Runner(store, spec.mission_id).run(spec)
    assert store.read_ledger()[-1].event == "error"


def _write_dag(path: Path, base: Path) -> None:
    nodes = [
        node("N1", files=[{"path": str(base / "n1") + "/", "action": "create"}]),
        node("N2", deps=["N1"], handler="dispatch_sleep"),
        node("N3", deps=["N2"], files=[{"path": str(base / "n3") + "/", "action": "create"}]),
    ]
    path.write_text(yaml.safe_dump(dag(nodes)), encoding="utf-8")


def _run_cli(dag_path: Path, store: Path, env_extra: dict) -> subprocess.Popen:
    env = {**os.environ, "PYTHONPATH": str(ROOT), **env_extra}
    return subprocess.Popen(
        [sys.executable, "-m", "router_recovery.runner", "--dag", str(dag_path), "--store", str(store)],
        cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )


def test_resume_after_kill9_does_not_repeat_completed_nodes(tmp_path):
    dag_path = tmp_path / "dag.yaml"
    _write_dag(dag_path, tmp_path)
    store = tmp_path / "ck"
    ledger = store / "LEDGER.jsonl"

    proc = _run_cli(dag_path, store, {"RR_SLEEP_S": "60"})
    deadline = time.time() + 30
    while time.time() < deadline:
        if ledger.exists() and '"node_id":"N2"' in ledger.read_text(encoding="utf-8").replace('"node_id": "N2"', '"node_id":"N2"'):
            break
        time.sleep(0.1)
    else:
        proc.kill()
        pytest.fail("N2 nunca llego a node_start")
    proc.send_signal(signal.SIGKILL)
    proc.wait(timeout=10)

    resumed = _run_cli(dag_path, store, {"RR_SLEEP_S": "0"})
    out, err = resumed.communicate(timeout=60)
    assert resumed.returncode == 0, err.decode()
    assert b"COMPLETED" in out

    events = [json.loads(l) for l in ledger.read_text(encoding="utf-8").splitlines() if l.strip() and l.strip().endswith("}")]
    def count(nid, ev):
        return sum(1 for e in events if e["node_id"] == nid and e["event"] == ev)
    assert count("N1", "node_done") == 1, "N1 no debe re-ejecutarse"
    assert count("N1", "node_start") == 1, "N1 no debe re-ejecutarse"
    assert count("N2", "node_done") == 1
    assert count("N3", "node_done") == 1


def test_cli_blocks_invalid_dag_before_running(tmp_path):
    dag_path = tmp_path / "bad.yaml"
    dag_path.write_text(yaml.safe_dump(dag([node("N1", deps=["N1"])])), encoding="utf-8")
    store = tmp_path / "ck"
    res = subprocess.run([sys.executable, "-m", "router_recovery.runner", "--dag", str(dag_path),
                          "--store", str(store)], cwd=ROOT, env={**os.environ, "PYTHONPATH": str(ROOT)},
                         capture_output=True, text=True)
    assert res.returncode == 2
    assert "BLOCKER" in res.stderr
    assert not (store / "LEDGER.jsonl").exists()


def test_load_dag_from_repo_file_validates():
    spec = load_dag(ROOT / "router_recovery" / "dag_schema.yaml")
    assert [n.node_id for n in spec.nodes] == ["N1", "N2", "N3"]
