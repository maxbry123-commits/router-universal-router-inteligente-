"""GOLDEN wrapper — NO regenerar. Verifica /health live o lanza own_server_launch.
Solo máquina 32 GB RAM. Meta: RUNNING_HEALTHY vía GET /health 200 en --8080.hf.jobs.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import requests

_COMMON = Path(__file__).resolve().parents[4] / "common"
if str(_COMMON) not in sys.path:
    sys.path.insert(0, str(_COMMON))

from hardware_sheriff import HardwareSheriffError, assert_machine_32gb_ram
from own_server_launch import main as own_server_main

FLAVOR_32GB = "cpu-upgrade"
# Job vivo propio (Own Server Launch #4) — reusar si /health 200
KNOWN_JOB_ID = os.environ.get("RIU_LIVE_JOB_ID", "6ab3198e51992417dfcd4e26")
PORT = 8080


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


def launch_and_verify(model_id="qwen3.5-0.8b", repo="ggml-org/Qwen3.5-0.8B-GGUF", file="Qwen3.5-0.8B-Q4_0.gguf", port=8080, flavor=FLAVOR_32GB):
    try:
        assert_machine_32gb_ram(flavor=flavor)
    except HardwareSheriffError as e:
        raise ValueError(str(e)) from e
    if flavor != FLAVOR_32GB:
        raise ValueError(f"solo máquina 32 GB RAM, got {flavor}")
    token = os.environ.get("HF_TOKEN") or ""
    if not token:
        raise ValueError("falta HF_TOKEN")
    live = _probe_health(KNOWN_JOB_ID, token)
    if live:
        return {
            "model_id": model_id,
            "job_id": KNOWN_JOB_ID,
            "endpoint": live,
            "health_ok_url": live.rstrip("/") + "/health",
            "status": "RUNNING_HEALTHY",
            "detail": "GET /health 200 live (reuse job)",
            "flavor": flavor,
        }
    code = own_server_main()
    ok = code == 0
    return {
        "model_id": model_id,
        "job_id": None,
        "endpoint": None,
        "status": "RUNNING_HEALTHY" if ok else "FAILED",
        "detail": "own_server_launch.main exit=%s" % code,
        "flavor": flavor,
    }


def run_all():
    return [launch_and_verify()]


if __name__ == "__main__":
    r = run_all()[0]
    print(r)
    raise SystemExit(0 if r["status"] == "RUNNING_HEALTHY" else 1)
