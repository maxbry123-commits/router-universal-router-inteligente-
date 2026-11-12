import os
import time
import json
import subprocess
from huggingface_hub import HfApi, cancel_job

DRY_RUN = True
NAMESPACE = "COMAND-CENTER-1"
CUTOFF_S = 24 * 3600
SLEEP_S = 900
AUDIT_DATASET = "COMAND-CENTER-1/router-universal-router-inteligente-auditoria"
KEEP_DATASET = {"INDEX.md", ".gitattributes"}
KEEP_DATASET_PREFIX = ("20261107-cierre/",)

PROTECTED_BUCKET_PREFIX = (
    "router-inteligente-universal/", "router-respaldo/", "riu-chat/",
    "riu_chat.sqlite3", "backups/", "state/", "perfiles/", "checkpoints/",
    "evolucion/", "handoff/", "swen_mcp/", "audit-memoria/", "apk/",
    "temp/", "agentes/", "banco-swe.bin", "riu_vault.db", "swen-gaps.json",
    "openclaw/", "router_updater/", "ms-playwright/",
)

def log(msg):
    print(msg, flush=True)

def run_maintenance():
    api = HfApi(token=os.getenv("HF_TOKEN"))
    log(f"=== MANTENIMIENTO (DRY_RUN={DRY_RUN}) ===")

    try:
        jobs = list(api.list_jobs(namespace=NAMESPACE))
        for j in jobs:
            st = getattr(getattr(j, "status", None), "stage", None)
            if st in {"RUNNING", "PENDING", "STARTING", "QUEUED"}:
                if DRY_RUN: log(f"[Job] Cancelaria {j.id} ({st})")
                else: cancel_job(job_id=j.id, namespace=NAMESPACE)
    except Exception as e:
        log(f"Error jobs: {e}")

    try:
        for s in api.list_spaces(author=NAMESPACE):
            if DRY_RUN: log(f"[Space] Pondria sleep_time={SLEEP_S} a {s.id}")
            else: api.set_space_sleep_time(repo_id=s.id, sleep_time=SLEEP_S)
    except Exception as e:
        log(f"Error sleep: {e}")

    try:
        for b in api.list_buckets(namespace=NAMESPACE):
            files = list(api.list_bucket_tree(bucket_id=b.id))
            old = [f.path for f in files if getattr(f, "mtime", None) and (time.time() - f.mtime.timestamp()) > CUTOFF_S and not f.path.startswith(PROTECTED_BUCKET_PREFIX)]
            if old:
                if DRY_RUN:
                    log(f"[Bucket {b.id}] Borraria {len(old)} archivos (ej: {old[:2]})")
                else:
                    for i in range(0, len(old), 2000):
                        api.batch_bucket_files(bucket_id=b.id, delete=old[i:i+2000])
                    log(f"[Bucket {b.id}] Borrados {len(old)} archivos")
    except Exception as e:
        log(f"Error buckets: {e}")

    try:
        files = api.list_repo_tree(repo_id=AUDIT_DATASET, repo_type="dataset", recursive=True)
        todel = [f.path for f in files if f.path not in KEEP_DATASET and not f.path.startswith(KEEP_DATASET_PREFIX)]
        if todel:
            if DRY_RUN:
                log(f"[Dataset] Borraria {len(todel)} archivos (ej: {todel[:2]})")
            else:
                api.delete_files(repo_id=AUDIT_DATASET, delete_patterns=todel, repo_type="dataset", commit_message="Mantenimiento")
                log(f"[Dataset] Borrados {len(todel)} archivos")
    except Exception as e:
        log(f"Error dataset: {e}")

    log("=== MANTENIMIENTO COMPLETADO ===")

if __name__ == "__main__":
    run_maintenance()
