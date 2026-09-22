import os
import time
import requests
from huggingface_hub import HfApi, HfHubHTTPError

MODELS = [
    ("qwen3.5-0.8b", "ggml-org/Qwen3.5-0.8B-GGUF", "Qwen3.5-0.8B-Q4_0.gguf"),
    ("qwen3-0.6b", "Qwen/Qwen3-0.6B-GGUF", "Qwen3-0.6B-Q8_0.gguf"),
]

def launch_and_verify(model_id: str, repo: str, file: str, port: int = 8080) -> dict:
    # enforce allowed flavors
    allowed_flavors = {"cpu-basic", "cpu-upgrade"}
    # we will only call with cpu-basic, but double‑check
    if "cpu-basic" not in allowed_flavors:
        raise ValueError("Flavor not allowed")

    url = f"https://huggingface.co/{repo}/resolve/main/{file}"
    # bash command: download model then start llama-server
    comando = (
        f"curl -fL {url} -o /model.gguf && "
        f"/app/llama-server -m /model.gguf --host 0.0.0.0 --port {port} "
        f"-c 8192 -np 4 -cb --cache-prompt --cache-ram 512 -fa on -ctk q8_0 -ctv q8_0"
    )

    api = HfApi(token=os.environ["HF_TOKEN"])
    # start the job
    job = api.run_job(
        image="ghcr.io/ggml-org/llama.cpp:server",
        command=["bash", "-lc", comando],
        flavor="cpu-basic",
        timeout="20m",
        expose=[port],
    )

    # wait for job to become RUNNING (max 300s total)
    start = time.time()
    while time.time() - start < 300:
        try:
            job_info = api.inspect_job(job.id)
        except Exception as e:
            time.sleep(5)
            continue

        # Use .status attribute (JobInfo has .status, not .get)
        status = getattr(job_info, "status", None)
        if status == "RUNNING":
            break
        time.sleep(5)
    else:
        return {
            "model_id": model_id,
            "job_id": job.id,
            "endpoint": None,
            "status": "FAILED",
            "detail": "Job did not reach RUNNING state within timeout",
        }

    # derive endpoint from job runtime info
    endpoint = None
    runtime = getattr(job_info, "runtime", None)
    if runtime:
        # runtime may be a list of objects with .url or a single object
        if isinstance(runtime, list) and runtime:
            endpoint = getattr(runtime[0], "url", None)
        else:
            endpoint = getattr(runtime, "url", None)
    # fallback: construct from job id (common pattern for HF Spaces)
    if not endpoint:
        endpoint = f"https://{job.id}.hf.space"

    # health check loop (remaining time)
    health_start = time.time()
    while time.time() - health_start < 300 - (time.time() - start):
        try:
            resp = requests.get(
                f"{endpoint}/health",
                headers={"Authorization": f"Bearer {os.environ['HF_TOKEN']}"},
                timeout=10,
            )
            if resp.status_code == 200:
                return {
                    "model_id": model_id,
                    "job_id": job.id,
                    "endpoint": endpoint,
                    "status": "RUNNING_HEALTHY",
                    "detail": "",
                }
        except Exception:
            pass
        time.sleep(5)

    return {
        "model_id": model_id,
        "job_id": job.id,
        "endpoint": endpoint,
        "status": "FAILED",
        "detail": "Health endpoint did not return 200 within timeout",
    }

def run_all() -> list[dict]:
    results = []
    for model_id, repo, file in MODELS:
        res = launch_and_verify(model_id, repo, file)
        results.append(res)
    return results
