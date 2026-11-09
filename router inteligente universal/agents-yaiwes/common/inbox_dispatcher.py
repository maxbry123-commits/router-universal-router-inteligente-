"""YAIWES immutable JSON inbox dispatcher.

A task is created as agents-yaiwes/inbox/<task>.json.
A task is considered processed when agents-yaiwes/receipts/<task>.json exists.
The instruction file itself is never mutated, so workflow result commits do not
re-trigger the push path for the original instruction.

Orchestrators 14/15 may request child tasks with:
<YAIWES_DELEGATIONS_JSON>
{"delegations":[{"target_agent":"agent-16-chat-space-oauth","instruction":"..."}]}
</YAIWES_DELEGATIONS_JSON>

Child targets are fail-closed against the Director-approved pool and recursion
is capped by MAX_DELEGATION_DEPTH.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import subprocess
import sys

AGENTS = Path(__file__).resolve().parents[1]
REPO = AGENTS.parents[1]
INBOX = AGENTS / "inbox"
RECEIPTS = AGENTS / "receipts"
MAX_TASKS = int(os.environ.get("RIU_INBOX_MAX_TASKS", "4"))
MAX_DELEGATION_DEPTH = int(os.environ.get("RIU_MAX_DELEGATION_DEPTH", "3"))
TASK_TIMEOUT = int(os.environ.get("RIU_INBOX_TASK_TIMEOUT", "5400"))

DELEGATION_POOL = {
    "agent-14-orchestrator-msaf": {
        "agent-4-router-smol",
        "agent-8-router-local",
        "agent-11-download-extraction",
        "agent-12-yaiwes-router",
        "agent-16-chat-space-oauth",
        "agent-17-chat-backend-32gb",
        "agent-18-chat-final-auditor",
        "agent-19-chat-components-motors",
    },
    "agent-15-orchestrator-grok": {
        "agent-4-router-smol",
        "agent-8-router-local",
        "agent-11-download-extraction",
        "agent-12-yaiwes-router",
        "agent-16-chat-space-oauth",
        "agent-17-chat-backend-32gb",
        "agent-18-chat-final-auditor",
        "agent-19-chat-components-motors",
    },
}

DELEGATIONS_RE = re.compile(
    r"<YAIWES_DELEGATIONS_JSON>\s*(\{.*?\})\s*</YAIWES_DELEGATIONS_JSON>",
    re.DOTALL,
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def safe_id(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in value)[:96]


def repo_rel(path: Path) -> str:
    return str(path.resolve().relative_to(REPO.resolve()))


def receipt_path(task_file: Path) -> Path:
    return RECEIPTS / task_file.name


def write_receipt(task_file: Path, payload: dict, status: str, rc: int, output: Path | None, state: Path | None, note: str = "") -> None:
    RECEIPTS.mkdir(parents=True, exist_ok=True)
    data = {
        "schema": "yaiwes.receipt/v1",
        "task_id": payload.get("task_id"),
        "target_agent": payload.get("target_agent"),
        "status": status,
        "runner_rc": rc,
        "processed_at_utc": utc_now(),
        "instruction_file": repo_rel(task_file),
        "output_file": repo_rel(output) if output and output.exists() else None,
        "state_file": repo_rel(state) if state and state.exists() else None,
        "note": note,
    }
    receipt_path(task_file).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def validate_task(task_file: Path, payload: dict) -> tuple[str, Path, str, int]:
    if payload.get("schema") != "yaiwes.instruction/v1":
        raise ValueError("INVALID_SCHEMA")
    task_id = str(payload.get("task_id") or "").strip()
    target = str(payload.get("target_agent") or "").strip()
    instruction = str(payload.get("instruction") or "").strip()
    depth = int(payload.get("depth", 0))
    if not task_id or safe_id(task_id) != task_file.stem:
        raise ValueError("TASK_ID_FILENAME_MISMATCH")
    if not re.fullmatch(r"agent-[A-Za-z0-9_-]+", target):
        raise ValueError("INVALID_TARGET")
    agent_dir = (AGENTS / target).resolve()
    if AGENTS.resolve() not in agent_dir.parents or not (agent_dir / "chain.yaml").is_file():
        raise ValueError("TARGET_AGENT_NOT_FOUND")
    if not instruction:
        raise ValueError("EMPTY_INSTRUCTION")
    if depth < 0 or depth > MAX_DELEGATION_DEPTH:
        raise ValueError("INVALID_DEPTH")
    return target, agent_dir, instruction, depth


def spawn_delegations(parent_payload: dict, output: Path) -> list[str]:
    parent = str(parent_payload.get("target_agent") or "")
    allowed = DELEGATION_POOL.get(parent)
    if not allowed or not output.exists():
        return []
    depth = int(parent_payload.get("depth", 0))
    if depth >= MAX_DELEGATION_DEPTH:
        return []

    text = output.read_text(encoding="utf-8", errors="ignore")
    match = DELEGATIONS_RE.search(text)
    if not match:
        return []

    parsed = json.loads(match.group(1))
    items = parsed.get("delegations") or []
    if not isinstance(items, list):
        raise ValueError("DELEGATIONS_NOT_LIST")

    created: list[str] = []
    INBOX.mkdir(parents=True, exist_ok=True)
    for idx, item in enumerate(items[:8], start=1):
        if not isinstance(item, dict):
            continue
        target = str(item.get("target_agent") or "").strip()
        instruction = str(item.get("instruction") or "").strip()
        if target not in allowed or not instruction:
            continue
        child_id = safe_id(f"{parent_payload['task_id']}--{target}--{idx}")
        child_path = INBOX / f"{child_id}.json"
        if child_path.exists() or (RECEIPTS / child_path.name).exists():
            continue
        child = {
            "schema": "yaiwes.instruction/v1",
            "task_id": child_id,
            "target_agent": target,
            "parent_task_id": parent_payload["task_id"],
            "depth": depth + 1,
            "allow_delegation": False,
            "instruction": instruction,
            "context_files": item.get("context_files") or [],
            "created_by": parent,
        }
        child_path.write_text(json.dumps(child, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        created.append(repo_rel(child_path))
    return created


def run_task(task_file: Path) -> None:
    try:
        payload = json.loads(task_file.read_text(encoding="utf-8"))
        target, agent_dir, _instruction, _depth = validate_task(task_file, payload)
    except Exception as exc:
        payload = locals().get("payload", {"task_id": task_file.stem, "target_agent": None})
        write_receipt(task_file, payload, "BLOCKED", 2, None, None, f"VALIDATION:{type(exc).__name__}:{exc}")
        return

    step_id = f"inbox_{safe_id(payload['task_id'])}"
    output = agent_dir / "steps" / step_id / "results" / "output.txt"
    state = agent_dir / "crazy_wall.state.json"

    env = os.environ.copy()
    env["RIU_INSTRUCTION_FILE"] = repo_rel(task_file)
    env.pop("RIU_ONLY_STEP", None)

    print(f"INBOX_RUN task={payload['task_id']} target={target}")
    try:
        proc = subprocess.run(
            [sys.executable, str(AGENTS / "chain.py"), str(agent_dir)],
            cwd=str(REPO),
            env=env,
            timeout=TASK_TIMEOUT,
            check=False,
        )
        rc = int(proc.returncode)
    except subprocess.TimeoutExpired:
        rc = 98

    status = "CLOSED" if rc == 0 and output.exists() else "BLOCKED"
    note = ""
    if status == "CLOSED":
        try:
            children = spawn_delegations(payload, output)
            if children:
                note = "DELEGATIONS_CREATED=" + ",".join(children)
        except Exception as exc:
            status = "BLOCKED"
            note = f"DELEGATION_PARSE:{type(exc).__name__}:{exc}"

    write_receipt(task_file, payload, status, rc, output, state, note)


def main() -> int:
    INBOX.mkdir(parents=True, exist_ok=True)
    RECEIPTS.mkdir(parents=True, exist_ok=True)
    pending = [p for p in sorted(INBOX.glob("*.json")) if not receipt_path(p).exists()]
    print(f"INBOX_PENDING={len(pending)}")
    for task_file in pending[:MAX_TASKS]:
        run_task(task_file)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
