import os
import time
import requests
from huggingface_hub import HfApi
try:
    from huggingface_hub.errors import HfHubHTTPError
except ImportError:
    from huggingface_hub.utils import HfHubHTTPError  # noqa: F401

MODELS = [
    ("qwen3-0.6b", "Qwen/Qwen3-0.6B-GGUF", "Qwen3-0.6B-Q8_0.gguf"),
]

ALLOWED_FLAVOR = "cpu-upgrade"  # 8 vCPU / 32 GB — único permitido


def launch_and_verify(model_id: str, repo: str, file: str, port: int = 8080, flavor: str = "cpu-upgrade") -> dict:
    if flavor != ALLOWED_FLAVOR:
        raise ValueError("HARDWARE: solo cpu-upgrade 32GB permitido")

    url = f"https://huggingface.co/{repo}/resolve/main/{file}"
    comando = (
        f"curl -fL {url} -o /model.gguf && "
        f"/app/llama-server -m /model.gguf --host 0.0.0.0 --port {port} "
        f"-c 8192 -np 4 -cb --cache-prompt --cache-ram 512 -fa on -ctk q8_0 -ctv q8_0"
    )

    api = HfApi(token=os.environ["HF_TOKEN"])
    job = api.run_job(
        image="ghcr.io/ggml-org/llama.cpp:server",
        command=["bash", "-lc", comando],
        flavor=ALLOWED_FLAVOR,
        timeout="20m",
        expose=[port],
    )

    start = time.time()
    job_info = None
    while time.time() - start < 300:
        try:
            job_info = api.inspect_job(job.id)
        except Exception:
            time.sleep(5)
            continue
        status = getattr(job_info, "status", None)
        stage = status
        if hasattr(status, "stage"):
            stage = status.stage
        if str(stage).upper() in ("RUNNING", "JobStatus.RUNNING") or stage == "RUNNING":
            break
        time.sleep(5)
    else:
        return {
            "model_id": model_id,
            "job_id": getattr(job, "id", None),
            "endpoint": None,
            "status": "FAILED",
            "detail": "Job did not reach RUNNING within timeout",
            "flavor": ALLOWED_FLAVOR,
        }

    endpoint = None
    runtime = getattr(job_info, "runtime", None)
    if runtime:
        if isinstance(runtime, list) and runtime:
            endpoint = getattr(runtime[0], "url", None)
        else:
            endpoint = getattr(runtime, "url", None)
    if not endpoint:
        jid = getattr(job, "id", "unknown")
        endpoint = f"https://{jid}--{port}.jobs.huggingface.co"

    while time.time() - start < 300:
        try:
            resp = requests.get(
                f"{endpoint}/health",
                headers={"Authorization": f"Bearer {os.environ['HF_TOKEN']}"},
                timeout=10,
            )
            if resp.status_code == 200:
                return {
                    "model_id": model_id,
                    "job_id": getattr(job, "id", None),
                    "endpoint": endpoint,
                    "status": "RUNNING_HEALTHY",
                    "detail": "",
                    "flavor": ALLOWED_FLAVOR,
                }
        except Exception:
            pass
        time.sleep(5)

    return {
        "model_id": model_id,
        "job_id": getattr(job, "id", None),
        "endpoint": endpoint,
        "status": "FAILED",
        "detail": "Health endpoint did not return 200 within timeout",
        "flavor": ALLOWED_FLAVOR,
    }


def run_all() -> list:
    results = []
    for model_id, repo, file in MODELS:
        results.append(launch_and_verify(model_id, repo, file))
    return results
