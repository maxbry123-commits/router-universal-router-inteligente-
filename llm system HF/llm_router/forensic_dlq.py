import json
import time
import re
import os
import threading

SECRET_PATTERNS = [
    (re.compile(r'(sk-[a-zA-Z0-9]{20,})'), '[REDACTED_OPENAI]'),
    (re.compile(r'(gsk_[a-zA-Z0-9]{20,})'), '[REDACTED_GROQ]'),
    (re.compile(r'(nvapi-[a-zA-Z0-9_-]{20,})'), '[REDACTED_NVIDIA]'),
]

def sanitize_secrets(text: str) -> str:
    if not isinstance(text, str):
        return text
    for pattern, replacement in SECRET_PATTERNS:
        text = pattern.sub(replacement, text)
    return text

class ForensicDLQ:
    def __init__(self, filepath: str = "forensic_dlq.jsonl"):
        self.filepath = filepath
        self.lock = threading.Lock()

    def log_failure(self, provider: str, error: str, prompt: str, history: list = None, metadata: dict = None):
        with self.lock:
            entry = {
                "timestamp": time.time(),
                "provider": provider,
                "error": sanitize_secrets(str(error)),
                "prompt": sanitize_secrets(prompt),
                "history": [
                    {"role": m.get("role"), "content": sanitize_secrets(m.get("content", ""))}
                    for m in (history or [])
                ],
                "metadata": metadata or {}
            }
            with open(self.filepath, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def replay_failures(self) -> list:
        if not os.path.exists(self.filepath):
            return []
        failures = []
        with open(self.filepath, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    failures.append(json.loads(line))
        return failures
