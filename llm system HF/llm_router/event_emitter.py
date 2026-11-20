import json
import time
import os
import threading
from forensic_dlq import sanitize_secrets

class EventEmitter:
    def __init__(self, filepath: str = "events.jsonl"):
        self.filepath = filepath
        self.lock = threading.Lock()

    def emit(self, event_type: str, data: dict):
        with self.lock:
            event = {
                "timestamp": time.time(),
                "event_type": event_type,
                "data": self._sanitize_dict(data)
            }
            with open(self.filepath, "a", encoding="utf-8") as f:
                f.write(json.dumps(event, ensure_ascii=False) + "\n")

    def _sanitize_dict(self, data: dict) -> dict:
        if not isinstance(data, dict):
            return data
        sanitized = {}
        for key, value in data.items():
            if isinstance(value, str):
                sanitized[key] = sanitize_secrets(value)
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_dict(value)
            else:
                sanitized[key] = value
        return sanitized

EMITTER = EventEmitter()
