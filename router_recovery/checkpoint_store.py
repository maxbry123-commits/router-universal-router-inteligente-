"""Ledger append-only con fsync + STATE.json con escritura atomica (tmp + fsync + os.replace)."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from .pydantic_models import LedgerEvent, checksum

STATE_SCHEMA = "router-state/1"


class CheckpointStore:
    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.state_path = self.root / "STATE.json"
        self.ledger_path = self.root / "LEDGER.jsonl"

    def load_state(self) -> dict[str, Any]:
        if not self.state_path.exists():
            return {"schema": STATE_SCHEMA, "phases": {}}
        try:
            state = json.loads(self.state_path.read_text(encoding="utf-8"))
            if not isinstance(state, dict) or not isinstance(state.get("phases"), dict):
                raise ValueError("STATE.json sin 'phases'")
            return state
        except (ValueError, OSError):
            return self.rebuild_state()

    def save_state(self, state: dict[str, Any]) -> None:
        tmp = self.state_path.with_name(self.state_path.name + ".tmp")
        with tmp.open("w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, self.state_path)

    def append(self, event: LedgerEvent) -> None:
        with self.ledger_path.open("a", encoding="utf-8") as f:
            f.write(event.model_dump_json() + "\n")
            f.flush()
            os.fsync(f.fileno())

    def read_ledger(self) -> list[LedgerEvent]:
        """Lee el ledger. Descarta lineas parciales (kill -9) y lineas con checksum invalido."""
        if not self.ledger_path.exists():
            return []
        events: list[LedgerEvent] = []
        for raw in self.ledger_path.read_text(encoding="utf-8").splitlines():
            raw = raw.strip()
            if not raw:
                continue
            try:
                ev = LedgerEvent.model_validate_json(raw)
            except ValueError:
                continue
            if ev.checksum != checksum(ev.model_dump(exclude={"checksum"})):
                continue
            events.append(ev)
        return events

    def rebuild_state(self) -> dict[str, Any]:
        phases: dict[str, str] = {}
        for ev in self.read_ledger():
            if ev.event == "node_start":
                phases[ev.node_id] = "en_curso"
            elif ev.event == "node_done":
                phases[ev.node_id] = "completa"
            elif ev.event == "error":
                phases[ev.node_id] = "invalido"
        return {"schema": STATE_SCHEMA, "phases": phases}
