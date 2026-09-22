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

# common/ (agents-yaiwes/common) — Sheriff
_COMMON = Path(__file__).resolve().parents[4] / "common"
if str(_COMMON) not in sys.path:
    sys.path.insert(0, str(_COMMON))
from hardware_sheriff import HardwareSheriffError, assert_machine_32gb_ram, guarded_run_job

# MICRO-ORDEN: 1 modelo, máquina 32 GB RAM, timeout healthcheck mayor; PASS solo con /health
MODELS = [
    ("qwen3-0.6b", "Qwen/Qwen3-0.6B-GGUF", "Qwen3-0.6B-Q8_0.gguf")
]
JOB_TIMEOUT = "45m"
HEALTH_WAIT_S = 900  # era 300 — descarga+arranque suele superar 5 min
POLL_S = 10
PORT = 8080


def _endpoint_candidates(job, job_id: str, port: int) -> list[str]:
    cand = []
    if job is not None:
        cand.append(getattr(job, "endpoint", None))
        meta = getattr(job, "metadata", None) or {}
        if isinstance(meta, dict):
            cand.append(meta.get("endpoint"))
    if job_id:
        cand.extend(
            [
                f"https://{job_id}.jobs.huggingface.co",
                f"https://{job_id}--{port}.hf.jobs",
                f"https://{job_id}-{port}.hf.space",
            ]
        )
    out = []
    for u in cand:
        if u and str(u) not in out:
            out.append(str(u).rstrip("/"))
    return out


def launch_and_verify(model_id, repo, file, port=PORT, flavor="cpu-upgrade") -> dict:
    try:
        assert_machine_32gb_ram(flavor=flavor)
    except HardwareSheriffError as e:
        raise ValueError(str(e)) from e

    api = HfApi(token=os.environ["HF_TOKEN"])
    url = f"https://huggingface.co/{repo}/resolve/main/{file}"
    command = [
        "bash",
        "-lc",
        f"curl -fL {url} -o /model.gguf && "
        f"/app/llama-server -m /model.gguf --host 0.0.0.0 --port {port} "
        "-c 8192 -np 4 -cb --cache-prompt --cache-ram 512 -fa on -ctk q8_0 -ctv q8_0",
    ]

    try:
        job = guarded_run_job(
            api,
            image="ghcr.io/ggml-org/llama.cpp:server",
            command=command,
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
    token = os.environ["HF_TOKEN"]
    headers = {"Authorization": f"Bearer {token}"}
    start = time.time()
    health_ok = False
    endpoint = None
    detail = ""

    while time.time() - start < HEALTH_WAIT_S:
        try:
            job_info = api.inspect_job(job_id)
            stage = getattr(getattr(job_info, "status", None), "stage", None) or getattr(
                job_info, "stage", None
            )
            cand = _endpoint_candidates(job, str(job_id) if job_id else "", port)
            ep_info = getattr(job_info, "endpoint", None)
            if ep_info:
                cand.insert(0, str(ep_info).rstrip("/"))
            if stage in ("ERROR", "COMPLETED", "CANCELED", "DELETED"):
                detail = f"Job ended early (stage={stage})"
                break
            if stage != "RUNNING":
                detail = f"Job not RUNNING (stage={stage})"
                time.sleep(POLL_S)
                continue
            for u in cand:
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
    results = []
    for model_id, repo, file in MODELS:
        results.append(launch_and_verify(model_id, repo, file))
    return results
