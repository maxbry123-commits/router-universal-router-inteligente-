import os
from huggingface_hub import HfApi

api = HfApi(token=os.getenv("HF_TOKEN"))

SCALER = """import os
import time
import threading
import urllib.request

THRESHOLD = float(os.environ.get("RAM_SCALE_THRESHOLD", "85"))
INTERVAL = float(os.environ.get("SCALE_INTERVAL_S", "10"))
STREAK = int(os.environ.get("SCALE_STREAK", "2"))
NEXT = (os.environ.get("NEXT_SPACE_URL") or "").rstrip("/")
COOLDOWN = float(os.environ.get("SCALE_COOLDOWN_S", "60"))

def ram_pct():
    try:
        with open("/sys/fs/cgroup/memory.current") as f: current = int(f.read())
        with open("/sys/fs/cgroup/memory.max") as f: limit = f.read().strip()
        if limit == "max": return 0.0
        return (current / int(limit)) * 100.0
    except: return 0.0

def wake_next():
    if not NEXT: return False
    try:
        req = urllib.request.Request(NEXT + "/health", headers={"User-Agent": "scaler"})
        urllib.request.urlopen(req, timeout=10)
        return True
    except: return False

def loop():
    streak = 0
    last_wake = 0
    while True:
        time.sleep(INTERVAL)
        pct = ram_pct()
        if pct >= THRESHOLD:
            streak += 1
            if streak >= STREAK and (time.time() - last_wake) > COOLDOWN:
                wake_next()
                last_wake = time.time()
                streak = 0
        else:
            streak = 0

if __name__ == "__main__":
    threading.Thread(target=loop, daemon=True).start()
"""

import os
import sys

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

try:
    from external.core.space_inventory import all_spaces
    SPACES = list(all_spaces())
except ImportError:  # pragma: no cover
    SPACES = [
        "space-grupo-1-router-mvp-1", "space-grupo-1-router-mvp-1-v2", "space-grupo-1-router-mvp-1-v7",
        "space-grupo-2-router-llm-hf-1", "space-grupo-2-router-llm-hf-2", "space-grupo-2-router-llm-hf-3",
    ]

for sp in SPACES:
    try:
        api.upload_file(
            path_or_fileobj=SCALER.encode(),
            path_in_repo="scaler_ram.py",
            repo_id=f"COMAND-CENTER-1/{sp}",
            repo_type="space"
        )
        print(f"INJECT_OK: {sp}")
    except Exception as e:
        print(f"INJECT_FAIL: {sp} - {e}")
