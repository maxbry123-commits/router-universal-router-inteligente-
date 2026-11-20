"""crazy_wall.py — Bitacora JSONL + taint tracking (NCT/APEX)"""
import json, os, time, logging
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)
LOG_DIR = Path(os.getenv("NCT_LOG_DIR", "./state"))
WALL_PATH = LOG_DIR / "crazy_wall.jsonl"
TAINT_FLAGS = {"hallucination", "contradiction", "missing_source", "escalation"}

class CrazyWall:
    def __init__(self, path: Path = WALL_PATH):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def log(self, event: str, payload: Dict[str, Any],
            taint: Optional[List[str]] = None) -> Dict[str, Any]:
        raw = taint or []
        valid = [t for t in raw if t in TAINT_FLAGS]
        invalid = [t for t in raw if t not in TAINT_FLAGS]
        if invalid:
            logger.warning("taint flags descartadas: %s", invalid)
        entry = {"ts": time.time(),
                 "iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                 "event": event, "payload": payload, "taint": valid}
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        if valid:
            logger.warning("Taint en crazy_wall: %s", valid)
        return entry

    def tail(self, n: int = 20) -> List[Dict[str, Any]]:
        if not self.path.exists():
            return []
        out = []
        with open(self.path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        for ln in lines[-n:]:
            try:
                out.append(json.loads(ln))
            except json.JSONDecodeError:
                continue
        return out

    def tainted_entries(self, limit: int = 100) -> List[Dict[str, Any]]:
        if not self.path.exists():
            return []
        tainted: List[Dict[str, Any]] = []
        with open(self.path, "r", encoding="utf-8") as f:
            for ln in f:
                try:
                    e = json.loads(ln)
                    if e.get("taint"):
                        tainted.append(e)
                        if len(tainted) >= limit:
                            break
                except json.JSONDecodeError:
                    continue
        return tainted

    def size(self) -> Dict[str, Any]:
        if not self.path.exists():
            return {"exists": False, "lines": 0, "bytes": 0}
        lines = 0
        with open(self.path, "r", encoding="utf-8") as f:
            for _ in f:
                lines += 1
        return {"exists": True, "lines": lines, "bytes": self.path.stat().st_size}

WALL = CrazyWall()
