"""Guardia de recepción: verifica el plan y conserva el avance entre sesiones."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STATE_DIR = ROOT / "chat router/03-ESTADO"
PLAN_PATH = ROOT / "chat router/01-PLAN/PLAN.json"
CHECKPOINT_PATH = STATE_DIR / "CHECKPOINT.json"
sys.path.insert(0, str(ROOT / "router inteligente universal"))
from integration.chat_mvp import ui_bridge


def now() -> datetime:
    return datetime.now(timezone.utc)


def iso(value: datetime) -> str:
    return value.isoformat(timespec="seconds").replace("+00:00", "Z")


def write_text(path: Path, text: str) -> None:
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as f:
        tmp = Path(f.name)
        f.write(text)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def write_json(path: Path, value: dict) -> None:
    write_text(path, json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def load_plan() -> tuple[dict, list[str]]:
    plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
    steps = plan.get("steps", [])
    if plan.get("status") != "VALIDATED" or len(steps) != 100:
        raise ValueError("PLAN_NOT_VALIDATED_100_STEPS")
    ids = [step["id"] for step in steps]
    if len(set(ids)) != len(ids) or not all(isinstance(key, str) and key for key in ids):
        raise ValueError("PLAN_STEP_IDS_INVALID")
    source = plan.get("source_path")
    if not isinstance(source, str):
        raise TypeError("PLAN_SOURCE_MISSING")
    source_path = (ROOT / source).resolve()
    if not source_path.is_relative_to(ROOT) or not source_path.is_file():
        raise ValueError("PLAN_SOURCE_MISSING")
    if hashlib.sha256(source_path.read_bytes()).hexdigest() != plan.get("source_sha256"):
        raise ValueError("PLAN_SOURCE_CHANGED")
    return plan, ids


def project_checkpoint(checkpoint: dict) -> None:
    current = STATE_DIR / "BITACORA.jsonl"
    events = ui_bridge._state_events(current.read_text(encoding="utf-8"))
    phase = {
        "RECEPTION": "AWAITING_PLAN",
        "RUNNING": "PLAN_100_RUNNING",
        "STOPPED": "STOP_CLEAN",
    }[checkpoint["status"]]
    if checkpoint["status"] == "RECEPTION":
        summary = checkpoint.get(
            "reception_summary",
            "Modo recepcion: plan de 100 pasos sin subir; T-06 pausada; sin PASS visual. Reloj sin iniciar.",
        )
    elif checkpoint["status"] == "RUNNING":
        summary = "Plan original de 100 pasos validado; reloj iniciado. CHECKPOINT.json registra el avance."
    else:
        summary = (
            "Guardia detenida: " + checkpoint["stop_reason"]
            + "; completados " + str(len(checkpoint["completed_steps"]))
            + "/" + str(checkpoint["total_steps"])
            + "; proximo: " + str(checkpoint["next_exact_action"])
        )
    event = ui_bridge._state_event(
        {
            "type": "CHECKPOINT_RECORDED",
            "project": "chat-yaiwes",
            "task": "PLAN-RECEPCION",
            "actor": "devin",
            "phase": phase,
            "status": "BLOCKED" if checkpoint["status"] != "RUNNING" else "RUNNING",
            "next": "Recibir plan original" if checkpoint["status"] == "RECEPTION" else "Ver CHECKPOINT.json",
            "summary": summary,
        },
        events[-1]["seq"] + 1,
    )
    text = current.read_text(encoding="utf-8").rstrip() + "\n"
    updated_log = text + json.dumps(event, ensure_ascii=False, separators=(",", ":")) + "\n"
    write_text(current, updated_log)
    events.append(event)
    state, wall = ui_bridge._state_projection(events)
    write_json(STATE_DIR / "STATE.json", state)
    write_json(STATE_DIR / "CRAZY_WALL.json", wall)
    handoff = STATE_DIR / "HANDOFF.md"
    updated_handoff = ui_bridge._render_handoff(handoff.read_text(encoding="utf-8"), state, wall, events)
    write_text(handoff, updated_handoff)
    if (
        current.read_text(encoding="utf-8") != updated_log
        or json.loads((STATE_DIR / "STATE.json").read_text(encoding="utf-8")) != state
        or json.loads((STATE_DIR / "CRAZY_WALL.json").read_text(encoding="utf-8")) != wall
        or handoff.read_text(encoding="utf-8") != updated_handoff
    ):
        raise OSError("CHECKPOINT_READBACK_FAILED")


def update(command: str, completed: str | None) -> dict:
    plan, ids = load_plan()
    checkpoint = json.loads(CHECKPOINT_PATH.read_text(encoding="utf-8"))
    instant = now()
    if command == "start":
        if checkpoint["status"] != "RECEPTION":
            raise ValueError("PLAN_ALREADY_STARTED")
        checkpoint.update(
            status="RUNNING",
            source_path=plan["source_path"],
            source_sha256=plan["source_sha256"],
            started_at=iso(instant),
            total_steps=len(ids),
            completed_steps=[],
            pending_steps=ids,
            next_exact_action=ids[0],
        )
    elif checkpoint["status"] != "RUNNING":
        raise ValueError("PLAN_NOT_RUNNING")
    elapsed = int((instant - datetime.fromisoformat(checkpoint["started_at"].replace("Z", "+00:00"))).total_seconds())
    checkpoint["elapsed_seconds"] = max(0, elapsed)
    if command == "tick" and completed:
        if completed not in ids:
            raise ValueError("UNKNOWN_STEP")
        if elapsed < checkpoint["stop_at_elapsed_seconds"] and completed not in checkpoint["completed_steps"]:
            checkpoint["completed_steps"].append(completed)
    checkpoint["pending_steps"] = [step for step in ids if step not in checkpoint["completed_steps"]]
    checkpoint["next_exact_action"] = checkpoint["pending_steps"][0] if checkpoint["pending_steps"] else "Plan terminado"
    checkpoint["updated_at"] = iso(instant)
    fraction = len(checkpoint["completed_steps"]) / len(ids)
    if elapsed >= checkpoint["stop_at_elapsed_seconds"] or fraction >= checkpoint["stop_at_completed_fraction"]:
        checkpoint["status"] = "STOPPED"
        checkpoint["stop_reason"] = "TIME_3H45" if elapsed >= checkpoint["stop_at_elapsed_seconds"] else "PLAN_95_PERCENT"
        write_json(CHECKPOINT_PATH, checkpoint)
        project_checkpoint(checkpoint)
    else:
        write_json(CHECKPOINT_PATH, checkpoint)
        if command == "start":
            project_checkpoint(checkpoint)
    return checkpoint


def heartbeat() -> dict:
    checkpoint = json.loads(CHECKPOINT_PATH.read_text(encoding="utf-8"))
    if checkpoint["status"] == "RECEPTION":
        checkpoint["updated_at"] = iso(now())
        write_json(CHECKPOINT_PATH, checkpoint)
        project_checkpoint(checkpoint)
    elif checkpoint["status"] == "RUNNING":
        checkpoint = update("heartbeat", None)
        if checkpoint["status"] == "RUNNING":
            project_checkpoint(checkpoint)
    else:
        raise ValueError("PLAN_STOPPED")
    checkpoint["bitacora_revision"] = json.loads(
        (STATE_DIR / "STATE.json").read_text(encoding="utf-8")
    )["revision"]
    write_json(CHECKPOINT_PATH, checkpoint)
    if json.loads(CHECKPOINT_PATH.read_text(encoding="utf-8")) != checkpoint:
        raise OSError("CHECKPOINT_READBACK_FAILED")
    return checkpoint


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("start", "tick", "status", "heartbeat"))
    parser.add_argument("--completed", help="ID de un paso completado, solo con tick")
    args = parser.parse_args()
    if args.completed and args.command != "tick":
        parser.error("--completed solo admite tick")
    try:
        if args.command == "status":
            checkpoint = json.loads(CHECKPOINT_PATH.read_text(encoding="utf-8"))
            if checkpoint["status"] == "RUNNING":
                checkpoint = update("tick", None)
        elif args.command == "heartbeat":
            checkpoint = heartbeat()
        else:
            checkpoint = update(args.command, args.completed)
    except (ValueError, TypeError, KeyError, OSError, json.JSONDecodeError) as exc:
        print(f"CHECKPOINT_ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({
        "status": checkpoint["status"],
        "elapsed_seconds": checkpoint["elapsed_seconds"],
        "remaining_seconds": max(0, checkpoint["stop_at_elapsed_seconds"] - checkpoint["elapsed_seconds"]),
        "completed": len(checkpoint["completed_steps"]),
        "total": checkpoint.get("total_steps", 100),
        "next": checkpoint["next_exact_action"],
    }, ensure_ascii=False))
    return 75 if checkpoint["status"] == "STOPPED" else 0


if __name__ == "__main__":
    raise SystemExit(main())
