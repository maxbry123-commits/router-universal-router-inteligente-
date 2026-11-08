import os
import time
from huggingface_hub import HfApi, cancel_job

DRY_RUN = True
NAMESPACE = "COMAND-CENTER-1"
CUTOFF_S = 24 * 3600

api = HfApi(token=os.getenv("HF_TOKEN"))

def run_maintenance():
    print(f"=== INICIANDO MANTENIMIENTO (DRY_RUN={DRY_RUN}) ===")
    try:
        jobs = list(api.list_jobs(namespace=NAMESPACE))
        for j in jobs:
            st = getattr(getattr(j, "status", None), "stage", None)
            if st in {"RUNNING", "PENDING", "STARTING", "QUEUED"}:
                if not DRY_RUN:
                    cancel_job(job_id=j.id, namespace=NAMESPACE)
                print(f"[Job] Cancelaria {j.id} ({st})")
    except Exception as e:
        print(f"Error jobs: {e}")

    try:
        for s in api.list_spaces(author=NAMESPACE):
            print(f"[Space] Poniendo sleep_time=900 a {s.id}")
            if not DRY_RUN:
                api.set_space_sleep_time(repo_id=s.id, sleep_time=900)
    except Exception as e:
        print(f"Error sleep: {e}")

    print("=== MANTENIMIENTO COMPLETADO ===")

if __name__ == "__main__":
    run_maintenance()
