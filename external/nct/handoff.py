"""handoff.py — Stated JSON Handoff (NCT/APEX). Dual-output: stdout + state/handoff.json"""
import json, os, time, logging
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)
STATE_DIR = Path(os.getenv("NCT_STATE_DIR", "./state"))
HANDOFF_PATH = STATE_DIR / "handoff.json"

class Handoff:
    def __init__(self, state_path: Path = HANDOFF_PATH):
        self.state_path = Path(state_path)
        self.state_path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> Dict[str, Any]:
        if not self.state_path.exists():
            return {"version": "1.0.0", "created_at": time.time(), "entries": []}
        try:
            with open(self.state_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error("No se pudo cargar handoff: %s", e)
            return {"version": "1.0.0", "entries": [], "error": str(e)}

    def save(self, data: Dict[str, Any]) -> None:
        data["updated_at"] = time.time()
        tmp = self.state_path.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, self.state_path)

    def append(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        data = self.load()
        entry.setdefault("timestamp", time.time())
        entry.setdefault("id", f"e-{len(data['entries'])+1:05d}")
        data["entries"].append(entry)
        if len(data["entries"]) > 1000:
            data["entries"] = data["entries"][-1000:]
        self.save(data)
        print(json.dumps(entry, ensure_ascii=False, indent=2))
        return entry

    def snapshot(self, last_n: int = 10) -> Dict[str, Any]:
        data = self.load()
        return {"version": data.get("version"),
                "total_entries": len(data.get("entries", [])),
                "last_n": data.get("entries", [])[-last_n:]}

HANDOFF = Handoff()
