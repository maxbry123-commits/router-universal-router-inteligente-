import hashlib
import importlib.util
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

GUARD_PATH = Path(__file__).resolve().parents[2] / "chat router/03-ESTADO/checkpoint_guard.py"
spec = importlib.util.spec_from_file_location("checkpoint_guard", GUARD_PATH)
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


def test_guard_requires_original_validated_plan(tmp_path, monkeypatch):
    plan_path = tmp_path / "PLAN.json"
    checkpoint_path = tmp_path / "CHECKPOINT.json"
    plan_path.write_text(json.dumps({"status": "AWAITING_UPLOAD", "steps": []}), encoding="utf-8")
    checkpoint_path.write_text(json.dumps({"status": "RECEPTION"}), encoding="utf-8")
    monkeypatch.setattr(guard, "ROOT", tmp_path)
    monkeypatch.setattr(guard, "PLAN_PATH", plan_path)
    monkeypatch.setattr(guard, "CHECKPOINT_PATH", checkpoint_path)
    with pytest.raises(ValueError, match="PLAN_NOT_VALIDATED"):
        guard.update("start", None)
    assert json.loads(checkpoint_path.read_text(encoding="utf-8"))["status"] == "RECEPTION"


def test_guard_stops_at_95_percent_and_preserves_source(tmp_path, monkeypatch):
    plan_path = tmp_path / "PLAN.json"
    checkpoint_path = tmp_path / "CHECKPOINT.json"
    source = tmp_path / "original.md"
    source.write_text("100 pasos del Director", encoding="utf-8")
    plan = {
        "status": "VALIDATED",
        "source_path": "original.md",
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "steps": [{"id": f"STEP-{index:03d}"} for index in range(1, 101)],
    }
    plan_path.write_text(json.dumps(plan), encoding="utf-8")
    checkpoint_path.write_text(json.dumps({
        "status": "RECEPTION", "stop_at_elapsed_seconds": 13500,
        "stop_at_completed_fraction": 0.95, "completed_steps": [],
    }), encoding="utf-8")
    monkeypatch.setattr(guard, "ROOT", tmp_path)
    monkeypatch.setattr(guard, "PLAN_PATH", plan_path)
    monkeypatch.setattr(guard, "CHECKPOINT_PATH", checkpoint_path)
    monkeypatch.setattr(guard, "now", lambda: datetime(2026, 10, 1, tzinfo=timezone.utc))
    emitted = []
    monkeypatch.setattr(guard, "project_checkpoint", lambda data: emitted.append(data["status"]))
    assert guard.update("start", None)["status"] == "RUNNING"
    for index in range(1, 95):
        assert guard.update("tick", f"STEP-{index:03d}")["status"] == "RUNNING"
    stopped = guard.update("tick", "STEP-095")
    assert stopped["status"] == "STOPPED"
    assert stopped["stop_reason"] == "PLAN_95_PERCENT"
    assert stopped["next_exact_action"] == "STEP-096"
    assert emitted == ["RUNNING", "STOPPED"]
    assert json.loads(plan_path.read_text(encoding="utf-8")) == plan
    assert source.read_text(encoding="utf-8") == "100 pasos del Director"


def test_guard_stops_at_three_hours_forty_five(tmp_path, monkeypatch):
    source = tmp_path / "original.md"
    source.write_text("plan", encoding="utf-8")
    plan_path = tmp_path / "PLAN.json"
    plan_path.write_text(json.dumps({
        "status": "VALIDATED", "source_path": "original.md",
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "steps": [{"id": f"STEP-{i:03d}"} for i in range(1, 101)],
    }), encoding="utf-8")
    checkpoint_path = tmp_path / "CHECKPOINT.json"
    checkpoint_path.write_text(json.dumps({
        "status": "RECEPTION", "stop_at_elapsed_seconds": 13500,
        "stop_at_completed_fraction": 0.95, "completed_steps": [],
    }), encoding="utf-8")
    monkeypatch.setattr(guard, "ROOT", tmp_path)
    monkeypatch.setattr(guard, "PLAN_PATH", plan_path)
    monkeypatch.setattr(guard, "CHECKPOINT_PATH", checkpoint_path)
    start = datetime(2026, 10, 1, tzinfo=timezone.utc)
    monkeypatch.setattr(guard, "now", lambda: start)
    monkeypatch.setattr(guard, "project_checkpoint", lambda _data: None)
    guard.update("start", None)
    monkeypatch.setattr(guard, "now", lambda: start + timedelta(hours=3, minutes=45))
    stopped = guard.update("tick", "STEP-001")
    assert stopped["status"] == "STOPPED"
    assert stopped["stop_reason"] == "TIME_3H45"
    assert stopped["completed_steps"] == []


def test_stop_projects_append_only_event_and_recovery_files(tmp_path, monkeypatch):
    monkeypatch.setattr(guard, "STATE_DIR", tmp_path)
    original = guard.ui_bridge._state_event({
        "type": "TASK_CLAIMED", "project": "chat-yaiwes", "task": "UI-T-06",
        "actor": "devin",
    }, 1)
    (tmp_path / "BITACORA.jsonl").write_text(json.dumps(original) + "\n", encoding="utf-8")
    (tmp_path / "HANDOFF.md").write_text("# Handoff\n", encoding="utf-8")
    guard.project_checkpoint({
        "status": "STOPPED", "stop_reason": "TIME_3H45",
        "completed_steps": ["STEP-001"], "total_steps": 100,
        "next_exact_action": "STEP-002",
    })
    events = [json.loads(line) for line in (tmp_path / "BITACORA.jsonl").read_text(encoding="utf-8").splitlines()]
    assert events[0] == original
    assert events[1]["type"] == "CHECKPOINT_RECORDED"
    assert events[1]["seq"] == 2
    assert json.loads((tmp_path / "STATE.json").read_text(encoding="utf-8"))["revision"] == 2
    node = json.loads((tmp_path / "CRAZY_WALL.json").read_text(encoding="utf-8"))["nodes"]["PLAN-RECEPCION"]
    assert node["phase"] == "STOP_CLEAN"
    assert node["status"] == "BLOCKED"
    assert "STEP-002" in (tmp_path / "HANDOFF.md").read_text(encoding="utf-8")
