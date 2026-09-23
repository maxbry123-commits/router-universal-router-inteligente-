```python
import json
import os
from typing import Dict, Any

def _load_state(agent_dir: str) -> Dict[str, Any]:
    state_path = os.path.join(agent_dir, "crazy_wall.state.json")
    if not os.path.isfile(state_path):
        raise FileNotFoundError(f"State file not found: {state_path}")
    with open(state_path, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in {state_path}: {e}")
    if not isinstance(data, dict):
        raise ValueError(f"State file does not contain a JSON object: {state_path}")
    return data

def _results_output_exists(agent_dir: str) -> bool:
    out_path = os.path.join(agent_dir, "results", "output.txt")
    return os.path.isfile(out_path)

def check() -> Dict[str, str]:
    # Locate repository root from __file__
    current_file = os.path.abspath(__file__)
    # __file__ is .../agent-18-chat-final-auditor/steps/wait_live/gate_live.py
    repo_root = os.path.abspath(
        os.path.join(
            os.path.dirname(current_file),  # wait_live
            "..",  # steps
            "..",  # agent-18-chat-final-auditor
            "..",  # agents-yaiwes
            ".."   # router inteligente universal (repo root)
        )
    )

    agent16_dir = os.path.join(repo_root, "agents-yaiwes", "agent-16-chat-space-oauth")
    agent17_dir = os.path.join(repo_root, "agents-yaiwes", "agent-17-chat-backend-32gb")

    # Load state files
    state16 = _load_state(agent16_dir)
    state17 = _load_state(agent17_dir)

    status16 = state16.get("status")
    status17 = state17.get("status")

    # Verify both are CLOSED and results/output.txt exist
    if status16 == "CLOSED" and status17 == "CLOSED" \
       and _results_output_exists(agent16_dir) and _results_output_exists(agent17_dir):
        return {"status": "READY"}

    # Otherwise raise with observed statuses
    raise RuntimeError(
        f"Chat agents not ready: agent-16 status={status16!r}, agent-17 status={status17!r}"
    )

if __name__ == "__main__":
    # Simple manual test
    try:
        print(check())
    except Exception as e:
        print(f"ERROR: {e}")
