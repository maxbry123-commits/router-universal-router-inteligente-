import os
import json
import subprocess
import time
from huggingface_hub import HfApi, cancel_job

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
    if not api.token:
        log("No HF_TOKEN found. Skipping maintenance.")
        return

    try:
        jobs = list(api.list_jobs(namespace=NAMESPACE))
        for j in jobs:
            st = getattr(getattr(j, "status", None), "stage", None)
            if st in {"RUNNING", "PENDING", "STARTING", "QUEUED", "STOPPING"}:
                cancel_job(job_id=j.id, namespace=NAMESPACE)
                log(f"Job {j.id} cancelado.")
    except Exception as e:
        log(f"Error cancelando jobs: {e}")

    try:
        for s in api.list_spaces(author=NAMESPACE):
            api.set_space_sleep_time(repo_id=s.id, sleep_time=SLEEP_S)
            log(f"sleep_time=900 aplicado a {s.id}")
    except Exception as e:
        log(f"Error en sleep_time: {e}")

    try:
        for b in api.list_buckets(namespace=NAMESPACE):
            files = list(api.list_bucket_tree(bucket_id=b.id))
            old = [f.path for f in files if getattr(f, "mtime", None) and (time.time() - f.mtime.timestamp()) > CUTOFF_S and not f.path.startswith(PROTECTED_BUCKET_PREFIX)]
            if old:
                for i in range(0, len(old), 2000):
                    api.batch_bucket_files(bucket_id=b.id, delete=old[i:i+2000])
                log(f"Borrados {len(old)} archivos de {b.id}")
    except Exception as e:
        log(f"Error limpiando buckets: {e}")

    try:
        files = api.list_repo_tree(repo_id=AUDIT_DATASET, repo_type="dataset", recursive=True)
        todel = [f.path for f in files if f.path not in KEEP_DATASET and not f.path.startswith(KEEP_DATASET_PREFIX)]
        if todel:
            api.delete_files(repo_id=AUDIT_DATASET, delete_patterns=todel, repo_type="dataset", commit_message="Mantenimiento 24h automatico")
            log(f"Borrados {len(todel)} archivos del dataset.")
    except Exception as e:
        log(f"Error limpiando dataset: {e}")

    log("=== MANTENIMIENTO 24H COMPLETADO ===")

if __name__ == "__main__":
    run_maintenance()
