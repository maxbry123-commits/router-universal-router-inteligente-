import os
import time
import json
import subprocess
from huggingface_hub import HfApi

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

    # Jobs de HF: fuera. El cliente fijado en el Space (huggingface_hub==0.22.2)
    # no tiene ni list_jobs ni cancel_job (verificado en el wheel), y la cuenta
    # no tiene PRO ni creditos prepago -> POST /api/jobs responde 402: no se
    # puede crear ningun Job, luego no hay ninguno que cancelar.
    log("[Jobs] Sin gestion: API de Jobs no disponible en el cliente fijado y sin PRO/creditos (402).")

    try:
        for s in api.list_spaces(author=NAMESPACE):
            if DRY_RUN: log(f"[Space] Pondria sleep_time={SLEEP_S} a {s.id}")
            else: api.set_space_sleep_time(repo_id=s.id, sleep_time=SLEEP_S)
    except Exception as e:
        log(f"Error sleep: {e}")

    # Buckets: la API de buckets no existe en huggingface_hub==0.22.2 (el cliente
    # fijado en el Space) -> este bloque no puede ejecutarse. Con un cliente mas
    # nuevo vuelve a funcionar tal cual (no se toca la logica).
    if hasattr(api, "list_buckets"):
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
    else:
        log("[Buckets] Sin gestion: list_buckets no existe en el huggingface_hub fijado.")

    # Dataset de auditoria: puede no existir -> se comprueba antes de listar.
    try:
        api.repo_info(repo_id=AUDIT_DATASET, repo_type="dataset")
        files = api.list_repo_tree(repo_id=AUDIT_DATASET, repo_type="dataset", recursive=True)
        todel = [f.path for f in files if f.path not in KEEP_DATASET and not f.path.startswith(KEEP_DATASET_PREFIX)]
        if todel:
            if DRY_RUN:
                log(f"[Dataset] Borraria {len(todel)} archivos (ej: {todel[:2]})")
            else:
                api.delete_files(repo_id=AUDIT_DATASET, delete_patterns=todel, repo_type="dataset", commit_message="Mantenimiento")
                log(f"[Dataset] Borrados {len(todel)} archivos")
    except Exception as e:
        log(f"[Dataset] Sin gestion: {AUDIT_DATASET} no disponible ({type(e).__name__}).")

    log("=== MANTENIMIENTO COMPLETADO ===")

if __name__ == "__main__":
    run_maintenance()
