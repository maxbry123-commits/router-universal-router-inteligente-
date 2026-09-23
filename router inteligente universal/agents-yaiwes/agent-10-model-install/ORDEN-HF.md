# ORDEN HF — agent-10 install_launch_test (verbatim, sin fences)

Copia verbatim el archivo en steps/install_launch_test/results/install_launch_test.py
o el TEMPLATE tras BEGIN_TEMPLATE.
PROHIBIDO regenerar. Poll con api.inspect_job (nunca .refresh en el objeto job).
Método = own_server_launch.py (Qwen3.5-0.8B, /app/llama-server, --8080.hf.jobs).
Solo máquina 32 GB RAM. NUNCA .gguf al repo.

BEGIN_TEMPLATE
"""install_launch_test — RÉPLICA verbatim del método own_server_launch que YA tiene /health OK.
PROHIBIDO regenerar. Poll solo con api.inspect_job. Solo máquina 32 GB RAM.
Modelo vivo confirmado: Qwen3.5-0.8B → https://<job_id>--8080.hf.jobs/health
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import requests
from huggingface_hub import HfApi

try:
    from huggingface_hub.errors import HfHubHTTPError
except Exception:  # pragma: no cover
    from huggingface_hub.utils import HfHubHTTPError  # type: ignore

_COMMON = Path(__file__).resolve().parents[4] / "common"
if str(_COMMON) not in sys.path:
    sys.path.insert(0, str(_COMMON))
from hardware_sheriff import HardwareSheriffError, assert_machine_32gb_ram, guarded_run_job

# RÉPLICA del método vivo (own_server_launch.py) — 1 modelo esta ronda
MODELS = [
    ("qwen3.5-0.8b", "ggml-org/Qwen3.5-0.8B-GGUF", "Qwen3.5-0.8B-Q4_0.gguf"),
]
JOB_TIMEOUT = "45m"
HEALTH_WAIT_S = 900
POLL_S = 10
PORT = 8080
FLAVOR_32GB = "cpu-upgrade"
IMAGE = "ghcr.io/ggml-org/llama.cpp:server"


def launch_and_verify(model_id, repo, file, port=PORT, flavor=FLAVOR_32GB) -> dict:
    try:
        assert_machine_32gb_ram(flavor=flavor)
    except HardwareSheriffError as e:
        raise ValueError(str(e)) from e

    token = os.environ["HF_TOKEN"]
    api = HfApi(token=token)
    url = f"https://huggingface.co/{repo}/resolve/main/{file}"
    sh = (
        f"curl -fL '{url}' -o /model.gguf && /app/llama-server -m /model.gguf "
        f"--host 0.0.0.0 --port {port} "
        "-c 8192 -np 4 -cb --cache-prompt --cache-reuse 256 --cache-ram 512 "
        "-fa on -ctk q8_0 -ctv q8_0"
    )
    try:
        job = guarded_run_job(
            api,
            image=IMAGE,
            command=["bash", "-lc", sh],
            flavor=flavor,
            timeout=JOB_TIMEOUT,
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
    except Exception as e:
        return {
            "model_id": model_id,
            "job_id": None,
            "endpoint": None,
            "status": "FAILED",
            "detail": f"sheriff/run_job: {type(e).__name__}: {e}",
            "flavor": flavor,
        }

    job_id = getattr(job, "id", None)
    headers = {"Authorization": f"Bearer {token}"}
    start = time.time()
    health_ok = False
    endpoint = None
    detail = ""

    while time.time() - start < HEALTH_WAIT_S:
        try:
            info = api.inspect_job(job_id=job_id)
            stage = getattr(getattr(info, "status", None), "stage", None) or getattr(info, "stage", None)
            cand = [
                getattr(info, "endpoint", None),
                getattr(job, "endpoint", None),
                f"https://{job_id}--{port}.hf.jobs",
                f"https://{job_id}.jobs.huggingface.co",
            ]
            urls = [str(u).rstrip("/") for u in dict.fromkeys(cand) if u]
            if stage in ("ERROR", "COMPLETED", "CANCELED", "DELETED"):
                detail = f"Job ended early (stage={stage})"
                break
            if stage != "RUNNING":
                detail = f"Job not RUNNING (stage={stage})"
                time.sleep(POLL_S)
                continue
            for u in urls:
                try:
                    resp = requests.get(f"{u}/health", headers=headers, timeout=15)
                    if resp.status_code == 200:
                        health_ok = True
                        endpoint = u
                        break
                    detail = f"Health {resp.status_code} at {u}"
                except Exception as e:  # pragma: no cover
                    detail = f"health err {type(e).__name__} at {u}"
            if health_ok:
                break
        except Exception as e:  # pragma: no cover
            detail = f"Error during polling: {e}"
        time.sleep(POLL_S)

    status = "RUNNING_HEALTHY" if health_ok else "FAILED"
    if not health_ok and not detail:
        detail = f"Timeout waiting for /health ({HEALTH_WAIT_S}s)"

    return {
        "model_id": model_id,
        "job_id": job_id,
        "endpoint": endpoint,
        "status": status,
        "detail": detail,
        "flavor": flavor,
    }


def run_all() -> list[dict]:
    return [launch_and_verify(mid, repo, file) for mid, repo, file in MODELS]


if __name__ == "__main__":
    for res in run_all():
        print(res)

END_TEMPLATE
