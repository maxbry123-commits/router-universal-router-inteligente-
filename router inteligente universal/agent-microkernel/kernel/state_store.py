"""Crazy Wall state (yaiwes.crazy-wall/v1): one file per agent + an aggregate. Atomic writes, thread-safe."""
from __future__ import annotations

import json
import os
import threading
import time
from pathlib import Path
from typing import Any

STATES = ("PENDING", "RUNNING", "VALIDATING", "GAP", "STABLE", "BLOCKED", "CLOSED")


class StateStore:
    def __init__(self, root: str | Path, run_id: str) -> None:
        self.root, self.run_id = Path(root), run_id
        (self.root / "crazy_wall").mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._agents: dict[str, dict[str, Any]] = {}

    def _write(self, path: Path, data: dict[str, Any]) -> None:
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
        os.replace(tmp, path)

    def update(self, agent: str, status: str, **fields: Any) -> None:
        assert status in STATES, status
        with self._lock:
            cur = self._agents.setdefault(agent, {"schema": "yaiwes.crazy-wall/v1", "run_id": self.run_id, "agent": agent, "completed": [],
                                                  "failed": [], "gaps": [], "evidence": [], "current_nodes": [], "next_nodes": []})
            cur.update(status=status, updated_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), **fields)
            self._write(self.root / "crazy_wall" / f"{agent}.state.json", cur)
            self._write(self.root / "crazy_wall.state.json", self.aggregate())

    def aggregate(self) -> dict[str, Any]:
        statuses = [a["status"] for a in self._agents.values()]
        overall = "CLOSED" if statuses and all(s == "CLOSED" for s in statuses) else ("BLOCKED" if "BLOCKED" in statuses else "RUNNING")
        return {"schema": "yaiwes.crazy-wall/v1", "run_id": self.run_id, "status": overall,
                "completed": sorted(n for n, a in self._agents.items() if a["status"] == "CLOSED"),
                "failed": sorted(n for n, a in self._agents.items() if a["status"] == "BLOCKED"),
                "gaps": [g for a in self._agents.values() for g in a.get("gaps", [])],
                "evidence": [e for a in self._agents.values() for e in a.get("evidence", [])],
                "agents": self._agents}
