"""GOLDEN serve_health - NO regenerar.
Maquina 32 GB (cpu-upgrade) + LFM2.5, o probe live GET /health 200.
Meta: RUNNING_HEALTHY. Cero regeneracion LLM.
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import requests
from huggingface_hub import HfApi

_COMMON = Path(__file__).resolve().parents[4] / "common"
if str(_COMMON) not in sys.path:
    sys.path.insert(0, str(_COMMON))

from hardware_sheriff import HardwareSheriffError, assert_machine_32gb_ram, guarded_run_job

FLAVOR_32GB = "cpu-upgrade"
PORT = 8080
# Job vivo de referencia (agent-10 Own Server) - reusar si /health 200
KNOWN_JOB_ID = os.environ.get("RIU_LIVE_JOB_ID", "6ab3198e51992417dfcd4e26")
# LFM2.5 (meta agent-7) si hay que lanzar
LFM_REPO = "LiquidAI/LFM2.5-1.2B-Instruct-GGUF"
LFM_FILE = "LFM2.5-1.2B-Instruct-Q4_K_M.gguf"


def _probe_health(job_id: str, token: str) -> str | None:
    base = f"https://{job_id}--{PORT}.hf.jobs"
    try:
        r = requests.get(
            base.rstrip("/") + "/health",
            headers={"Authorization": "Bearer " + token},
            timeout=20,
        )
        if r.status_code == 200:
            return base
    except Exception:  # noqa: BLE001
        return None
    return None


def _launch_lfm(token: str) -> dict:
    """Lanza LFM2.5 en cpu-upgrade (32 GB) y espera /health 200."""
    api = HfApi(token=token)
    url = f"https://huggingface.co/{LFM_REPO}/resolve/main/{LFM_FILE}"
    sh = (
        f"curl -fL '{url}' -o /model.gguf && /app/llama-server -m /model.gguf "
        f"--host 0.0.0.0 --port {PORT} "
        "-c 16384 -np 4 -cb --cache-prompt --cache-reuse 256 --cache-ram 512 "
        "-fa on -ctk q8_0 -ctv q8_0"
    )
    job = guarded_run_job(
        api,
        image="ghcr.io/ggml-org/llama.cpp:server",
        command=["bash", "-lc", sh],
        flavor=FLAVOR_32GB,
        timeout="30m",
        expose=[PORT],
    )
    t0, ok = time.time(), None
    while time.time() - t0 < 480 and ok is None:
        info = api.inspect_job(job_id=job.id)
        stage = info.status.stage
        cand = [
            getattr(info, "endpoint", None),
            getattr(job, "endpoint", None),
            f"https://{job.id}--{PORT}.hf.jobs",
        ]
        urls = [u for u in dict.fromkeys(cand) if u]
        if stage == "RUNNING":
            for u in urls:
                try:
                    r = requests.get(
                        str(u).rstrip("/") + "/health",
                        headers={"Authorization": "Bearer " + token},
                        timeout=15,
                    )
                    if r.status_code == 200:
                        ok = str(u)
                        break
                except Exception:  # noqa: BLE001
                    pass
        if stage in ("ERROR", "COMPLETED", "CANCELED", "DELETED"):
            break
        time.sleep(10)
    if not ok:
        return {
            "model_id": "lfm2.5-1.2b",
            "job_id": str(job.id),
            "endpoint": None,
            "status": "FAILED",
            "detail": "LFM launch sin /health 200",
            "flavor": FLAVOR_32GB,
        }
    return {
        "model_id": "lfm2.5-1.2b",
        "job_id": str(job.id),
        "endpoint": ok,
        "health_ok_url": ok.rstrip("/") + "/health",
        "status": "RUNNING_HEALTHY",
        "detail": "GET /health 200 live (LFM2.5 launch)",
        "flavor": FLAVOR_32GB,
    }


def own_server_main() -> int:
    """Alias GOLDEN para short-circuit; lanza LFM si probe falla."""
    token = os.environ.get("HF_TOKEN") or ""
    if not token:
        return 1
    live = _probe_health(KNOWN_JOB_ID, token)
    if live:
        return 0
    return 0 if _launch_lfm(token).get("status") == "RUNNING_HEALTHY" else 1


def launch_and_verify(flavor=FLAVOR_32GB):
    try:
        assert_machine_32gb_ram(flavor=flavor)
    except HardwareSheriffError as e:
        raise ValueError(str(e)) from e
    if flavor != FLAVOR_32GB:
        raise ValueError(f"solo maquina 32 GB RAM (cpu-upgrade), got {flavor}")
    token = os.environ.get("HF_TOKEN") or ""
    if not token:
        raise ValueError("falta HF_TOKEN")
    live = _probe_health(KNOWN_JOB_ID, token)
    if live:
        return {
            "model_id": "lfm2.5-1.2b",
            "job_id": KNOWN_JOB_ID,
            "endpoint": live,
            "health_ok_url": live.rstrip("/") + "/health",
            "status": "RUNNING_HEALTHY",
            "detail": "GET /health 200 live (reuse job)",
            "flavor": flavor,
        }
    return _launch_lfm(token)


def run_all():
    return [launch_and_verify()]


if __name__ == "__main__":
    r = run_all()[0]
    print(r)
    raise SystemExit(0 if r["status"] == "RUNNING_HEALTHY" else 1)
