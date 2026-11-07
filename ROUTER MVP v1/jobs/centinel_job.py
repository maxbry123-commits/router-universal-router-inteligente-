import json
import time
import sys
from pathlib import Path
from huggingface_hub import HfApi

SPACE_ID = "COMAND-CENTER-1/local-llm-router-v7"
TARGET = Path("ROUTER MVP v1/hf_snapshot")
MANIFEST = TARGET / "manifest.json"

for _ in range(60):
    if MANIFEST.exists():
        break
    time.sleep(2)
else:
    sys.exit(1)

api = HfApi()
remote = sorted(api.list_repo_files(repo_id=SPACE_ID, repo_type="space"))
remote = [f for f in remote if f != ".gitattributes"]
local = json.loads(MANIFEST.read_text())

report = {
    "space": SPACE_ID,
    "local_count": len(local),
    "remote_count": len(remote),
    "missing_local": sorted(set(remote) - set(local)),
    "extra_local": sorted(set(local) - set(remote)),
    "files": [{"path": k, "bytes": v["bytes"]} for k, v in local.items()]
}

Path("ROUTER MVP v1/hf_snapshot/audit/centinel_report.json").write_text(json.dumps(report, indent=2))
print(f"[CENTINELA] local={report['local_count']} remoto={report['remote_count']}")
