import os
import sys
import time
from pathlib import Path

import requests
from huggingface_hub import HfApi

try:
    from huggingface_hub.errors import HfHubHTTPError
except Exception:  # pragma: no cover
    from huggingface_hub.utils import HfHubHTTPError  # fallback

# common/ (agents-yaiwes/common) — Sheriff en main SHA e966263+
_COMMON = Path(__file__).resolve().parents[4] / "common"
if str(_COMMON) not in sys.path:
    sys.path.insert(0, str(_COMMON))
from hardware_sheriff import assert_machine_32gb_ram, guarded_run_job

MODELS = [
    ("qwen3-0.6b", "Qwen/Qwen3-0.6B-GGUF", "Qwen3-0.6B-Q8_0.gguf")
]


def launch_and_verify(model_id, repo, file, port=8080, flavor="cpu-upgrade") -> dict:
    # ANTES de run_job: FAIL si ≠ máquina 32 GB RAM
    assert_machine_32gb_ram(flavor=flavor)

    api = HfApi(token=os.environ["HF_TOKEN"])
    url = f"https://huggingface.co/{repo}/resolve/main/{file}"
    command = [
        "bash",
        "-lc",
        f"curl -fL {url} -o /model.gguf && "
        f"/app/llama-server -m /model.gguf --host 0.0.0.0 --port {port} "
        "-c 8192 -np 4 -cb --cache-prompt --cache-ram 512 -fa on -ctk q8_0 -ctv q8_0"
    ]

    try:
        job = guarded_run_job(
            api,
            image="ghcr.io/ggml-org/llama.cpp:server",
            command=command,
            flavor=flavor,
            timeout="20m",
            expose=[port],
        )
    except HfHubHTTPError as e:  # pragma: no cover
        return {
            "model_id": model_id,
            "job_id": None,
            "endpoint": None,
            "status": "FAILED",
            "detail": f"run_job failed: {e}",
            "flavor": flavor,
        }
    except Exception as e:  # HardwareSheriffError u otros
        return {
            "model_id": model_id,
            "job_id": None,
            "endpoint": None,
            "status": "FAILED",
            "detail": f"sheriff/run_job: {type(e).__name__}: {e}",
            "flavor": flavor,
        }

    job_id = getattr(job, "id", None)
    endpoint = None
    if job and hasattr(job, "metadata"):
        endpoint = job.metadata.get("endpoint")
    if not endpoint and job_id:
        endpoint = f"https://{job_id}.jobs.huggingface.co"

    start = time.time()
    health_ok = False
    detail = ""
    while time.time() - start < 300:
        try:
            job_info = api.inspect_job(job_id)
            stage = getattr(getattr(job_info, "status", None), "stage", None) or getattr(job_info, "stage", None)
            if stage != "RUNNING":
                detail = f"Job not RUNNING (stage={stage})"
                time.sleep(2)
                continue
            health_url = f"{str(endpoint).rstrip('/')}/health"
            headers = {"Authorization": f"Bearer {os.environ['HF_TOKEN']}"}
            resp = requests.get(health_url, headers=headers, timeout=5)
            if resp.status_code == 200:
                health_ok = True
                break
            else:
                detail = f"Health check returned {resp.status_code}"
        except Exception as e:  # pragma: no cover
            detail = f"Error during polling: {e}"
        time.sleep(2)

    status = "RUNNING_HEALTHY" if health_ok else "FAILED"
    if not health_ok and not detail:
        detail = "Timeout waiting for job to become healthy"

    return {
        "model_id": model_id,
        "job_id": job_id,
        "endpoint": endpoint,
        "status": status,
        "detail": detail,
        "flavor": flavor,
    }


def run_all() -> list[dict]:
    results = []
    for model_id, repo, file in MODELS:
        results.append(launch_and_verify(model_id, repo, file))
    return results
