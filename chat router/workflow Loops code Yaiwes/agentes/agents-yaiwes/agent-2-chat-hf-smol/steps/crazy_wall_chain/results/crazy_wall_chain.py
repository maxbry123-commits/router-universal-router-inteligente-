import hashlib
import json
from copy import deepcopy


def _compute_hash(prev: str, event: dict) -> str:
    return hashlib.sha256(
        (prev + json.dumps(event, sort_keys=True, ensure_ascii=False)).encode("utf-8")
    ).hexdigest()


def append_event(state: dict, event: dict) -> dict:
    """
    Return a NEW state (does not mutate the received one) whose "events" list
    (empty if absent) has one more element: {"seq": n, "event": event,
    "prev": hash of previous event or "GENESIS", "hash": sha256 hex of
    (prev + json.dumps(event, sort_keys=True, ensure_ascii=False))}.
    """
    new_state = deepcopy(state)
    events = new_state.get("events", [])
    prev_hash = "GENESIS"
    if events:
        prev_hash = events[-1]["hash"]
    seq = len(events) + 1
    h = _compute_hash(prev_hash, event)
    entry = {
        "seq": seq,
        "event": event,
        "prev": prev_hash,
        "hash": h,
    }
    events.append(entry)
    new_state["events"] = events
    return new_state


def verify(state: dict) -> bool:
    """
    True if the whole chain is consistent:
    - seq are consecutive starting from 1,
    - prev matches the previous event's hash (or "GENESIS" for the first),
    - recalculated hash matches the stored hash.
    """
    events = state.get("events", [])
    for i, entry in enumerate(events):
        expected_seq = i + 1
        if entry.get("seq") != expected_seq:
            return False
        expected_prev = "GENESIS" if i == 0 else events[i - 1]["hash"]
        if entry.get("prev") != expected_prev:
            return False
        computed = _compute_hash(expected_prev, entry["event"])
        if computed != entry.get("hash"):
            return False
    return True


def render_handoff(state: dict) -> str:
    """
    Markdown that starts with "# HANDOFF",
    has the line "## Eventos" and then one line per event with its seq
    and the value of event.get("texto", "").
    """
    lines = ["# HANDOFF", "## Eventos"]
    for entry in state.get("events", []):
        seq = entry.get("seq", "")
        texto = entry.get("event", {}).get("texto", "")
        lines.append(f"- {seq}: {texto}")
    return "\n".join(lines)
