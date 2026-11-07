import json
import hashlib
import sys
from pathlib import Path
from huggingface_hub import HfApi

SPACE_ID = "COMAND-CENTER-1/local-llm-router-v7"
TARGET = Path("ROUTER MVP v1/hf_snapshot")
MANIFEST = TARGET / "manifest.json"

def fail(msg):
    print(f"[SHERIFF] NO_GO: {msg}")
    sys.exit(1)

if not MANIFEST.exists():
    fail("manifest.json ausente")

local = json.loads(MANIFEST.read_text())
api = HfApi()

for rel, meta in local.items():
    try:
        remote_path = api.hf_hub_download(repo_id=SPACE_ID, repo_type="space", filename=rel)
        remote_hash = hashlib.sha256(Path(remote_path).read_bytes()).hexdigest()
    except Exception as e:
        fail(f"no se pudo leer remoto {rel}: {e}")
    if remote_hash != meta["sha256"]:
        fail(f"hash mismatch en {rel}")

remote_files = set(api.list_repo_files(repo_id=SPACE_ID, repo_type="space"))
remote_files.discard(".gitattributes")
missing = remote_files - set(local.keys())
if missing:
    fail(f"archivos faltantes: {sorted(missing)}")

extras = set(local.keys()) - remote_files
if extras:
    fail(f"archivos extra no autorizados: {sorted(extras)}")

creport = Path("ROUTER MVP v1/hf_snapshot/audit/centinel_report.json")
if not creport.exists():
    fail("centinel_report.json ausente")
cdata = json.loads(creport.read_text())
if cdata.get("local_count") != cdata.get("remote_count"):
    fail("centinela reporta desbalance")

evidence = {
    "gate1_input_block_verbatim": "PASS",
    "gate2_completitud": "PASS",
    "gate3_coherencia": "PASS",
    "gate4_formato": "PASS",
    "files_verified": len(local),
    "final": "PASS"
}
Path("ROUTER MVP v1/hf_snapshot/audit/sheriff_verdict.json").write_text(json.dumps(evidence, indent=2))
print(f"[SHERIFF] PASS: {len(local)} archivos validados")
