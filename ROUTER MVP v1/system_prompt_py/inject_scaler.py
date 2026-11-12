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

SPACES = ["swe-code-s1", "swe-code-s2", "swe-code-s3", "riu-router", "claude-github-mcp-backup", "swe-code-web"]

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
