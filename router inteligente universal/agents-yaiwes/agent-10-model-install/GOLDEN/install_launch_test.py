"""GOLDEN wrapper — NO regenerar. Ejecuta common/own_server_launch.py (método vivo Director).
Solo máquina 32 GB RAM. Meta: RUNNING_HEALTHY vía /health en --8080.hf.jobs.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

_COMMON = Path(__file__).resolve().parents[4] / "common"
if str(_COMMON) not in sys.path:
    sys.path.insert(0, str(_COMMON))

from hardware_sheriff import HardwareSheriffError, assert_machine_32gb_ram
from own_server_launch import main as own_server_main

FLAVOR_32GB = "cpu-upgrade"


def launch_and_verify(model_id="qwen3.5-0.8b", repo="ggml-org/Qwen3.5-0.8B-GGUF", file="Qwen3.5-0.8B-Q4_0.gguf", port=8080, flavor=FLAVOR_32GB):
    try:
        assert_machine_32gb_ram(flavor=flavor)
    except HardwareSheriffError as e:
        raise ValueError(str(e)) from e
    if flavor != FLAVOR_32GB:
        raise ValueError(f"solo máquina 32 GB RAM, got {flavor}")
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
