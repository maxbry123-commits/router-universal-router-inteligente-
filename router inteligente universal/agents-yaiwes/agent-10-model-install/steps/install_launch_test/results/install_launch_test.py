import os
import time
from huggingface_hub import HfApi
import requests

def launch_and_verify(model_id: str, repo: str, file: str, port: int = 8080) -> dict:
    # Validate flavor restriction
    allowed_flavors = {"cpu-basic", "cpu-upgrade"}
    flavor = "cpu-basic"  # as required by the task
    if flavor not in allowed_flavors:
        raise ValueError(f"Flavor '{flavor}' is not allowed. Use one of {allowed_flavors}")

    # Build public URL and bash command
    url = f"https://huggingface.co/{repo}/resolve/main/{file}"
    comando = (
        f"curl -fL {url} -o /model.gguf && "
        f"/app/llama-server -m /model.gguf --host 0.0.0.0 --port {port} "
        "-c 8192 -np 4 -cb --cache-prompt --cache-ram 512 "
        "-fa on -ctk q8_0 -ctv q8_0"
    )

    # Launch job on Hugging Face
    api = HfApi(token=os.environ["HF_TOKEN"])
    job = api.run_job(
        image="ghcr.io/ggml-org/llama.cpp:server",
        command=["bash", "-lc", comando],
        flavor=flavor,
        timeout="20m",
        expose=[port],
    )
    job_id = job.id  # correct attribute for JobInfo

    # Wait for job to become RUNNING and health endpoint to respond 200
    endpoint = None
    start = time.time()
    while time.time() - start < 300:  # 5 minutes max wait
        info = api.inspect_job(job_id)
        if getattr(info, "stage", None) == "RUNNING":
            endpoint = getattr(info, "endpoint", None)
            if endpoint:
                health_url = f"{endpoint}/health"
                try:
                    resp = requests.get(
                        health_url,
                        headers={"Authorization": f"Bearer {os.environ['HF_TOKEN']}"},
                        timeout=5,
                    )
                    if resp.status_code == 200:
                        return {
                            "model_id": model_id,
                            "job_id": job_id,
                            "endpoint": endpoint,
                            "status": "RUNNING_HEALTHY",
                            "detail": "",
                        }
                except Exception as e:
                    # health check failed, continue waiting
                    pass
        time.sleep(5)

    # If we exit the loop, something went wrong
    return {
        "model_id": model_id,
        "job_id": job_id,
        "endpoint": endpoint or "",
        "status": "FAILED",
        "detail": "Job did not become healthy within timeout",
    }


MODELS = [
    ("qwen3.5-0.8b", "ggml-org/Qwen3.5-0.8B-GGUF", "Qwen3.5-0.8B-Q4_0.gguf"),
    ("qwen3-0.6b", "Qwen/Qwen3-0.6B-GGUF", "Qwen3-0.6B-Q8_0.gguf"),
]


def run_all() -> list[dict]:
    results = []
    for model_id, repo, file in MODELS:
        result = launch_and_verify(model_id, repo, file)
        results.append(result)
    return results
