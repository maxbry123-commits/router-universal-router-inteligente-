import os
import sys
import time
from pathlib import Path
import requests

# Add common/ to sys.path (parents[4]/common)
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "common"))

from huggingface_hub import HfApi
try:
    from huggingface_hub.errors import HfHubHTTPError
except ImportError:  # fallback
    from huggingface_hub.utils import HfHubHTTPError  # type: ignore

from hardware_sheriff import assert_machine_32gb_ram, guarded_run_job, HardwareSheriffError

# Constants
MODELS = [("qwen3-0.6b", "Qwen/Qwen3-0.6B-GGUF", "Qwen3-0.6B-Q8_0.gguf")]
JOB_TIMEOUT = "45m"
HEALTH_WAIT_S = 900
POLL_S = 10


def launch_and_verify(model_id: str, repo: str, file: str, port: int = 8080, flavor: str = "cpu-upgrade") -> dict:
    # Verify machine RAM before launching
    try:
        assert_machine_32gb_ram(flavor=flavor)
    except HardwareSheriffError as e:
        raise ValueError(str(e))

    api = HfApi()
    image = "ghcr.io/ggml-org/llama.cpp:server"
    # Command: fetch model via curl, then launch llama-server
    cmd = (
        f"curl -L -o model.gguf https://huggingface.co/{repo}/resolve/main/{file} && "
        f"./llama-server -m model.gguf -c 2048 --port {port} --host 0.0.0.0"
    )

    job = guarded_run_job(
        api,
        image=image,
        command=["sh", "-c", cmd],
        flavor=flavor,
        timeout=JOB_TIMEOUT,
        expose=[port],
    )

    job_id = job.id
    endpoint = job.endpoint
    start = time.time()
    status = None
    detail = ""

    while time.time() - start < HEALTH_WAIT_S:
        job.refresh()
        if job.status != "RUNNING":
            status = job.status
            detail = f"Job not RUNNING, status={status}"
            break

        # Try several possible health-check URLs
        health_urls = [
            f"{endpoint}/health",
            f"{endpoint}--{port}.hf.co/health",
            f"{endpoint}.jobs.huggingface.co/health",
        ]
        healthy = False
        for url in health_urls:
            try:
                resp = requests.get(
                    url,
                    headers={"Authorization": f"Bearer {os.getenv('HF_TOKEN')}"},
                    timeout=5,
                )
                if resp.status_code == 200:
                    healthy = True
                    break
            except Exception:
                continue

        if healthy:
            status = "RUNNING_HEALTHY"
            detail = "Health check passed"
            break

        time.sleep(POLL_S)
    else:
        status = "FAILED"
        detail = f"Health check not passed within {HEALTH_WAIT_S}s"

    return {
        "model_id": model_id,
        "job_id": job_id,
        "endpoint": endpoint,
        "status": status,
        "detail": detail,
        "flavor": flavor,
    }


def run_all():
    results = []
    for model_id, repo, file in MODELS:
        results.append(launch_and_verify(model_id, repo, file))
    return results


if __name__ == "__main__":
    for res in run_all():
        print(res)
