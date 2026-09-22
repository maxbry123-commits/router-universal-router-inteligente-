"""Launches a REAL local model server on the Director's OWN Hugging Face account (his compute, his Job, cpu-basic, free) — NOT a third-party
paid API, and the weights are fetched straight from the public Hub URL inside the Job itself (no separate download step anywhere else).
FIX (2026-09-22): the `volumes=["hf://…"]` shortcut raised an internal error in this huggingface_hub version ('str' object has no attribute
'to_dict'); replaced with a plain curl of the model's public resolve URL inside the container's own command — same result, no download
outside the Job, still on the Director's own account, still cpu-basic, still no paid API."""
from __future__ import annotations

import os
import time

import requests
from huggingface_hub import HfApi

MODEL_REPO = "ggml-org/Qwen3.5-0.8B-GGUF"
MODEL_FILE = "Qwen3.5-0.8B-Q4_0.gguf"
PORT = 8080


def note(title: str, msg: str, level: str = "notice") -> None:
    print(f"::{title.upper()} {level}:: {msg}".replace("\n", " ")[:900], flush=True)
    print(f"::{level} title=RIU_OWNSERVER_{title}::{msg}".replace("\n", " ")[:900], flush=True)


def main() -> int:
    token = os.environ["HF_TOKEN"]
    api = HfApi(token=token)
    url = f"https://huggingface.co/{MODEL_REPO}/resolve/main/{MODEL_FILE}"
    sh = (f"curl -fL '{url}' -o /model.gguf && /app/llama-server -m /model.gguf --host 0.0.0.0 --port {PORT} "
          "-c 8192 -np 4 -cb --cache-prompt --cache-reuse 256 --cache-ram 512 -fa on -ctk q8_0 -ctv q8_0")
    try:
        job = api.run_job(image="ghcr.io/ggml-org/llama.cpp:server", command=["bash", "-lc", sh], flavor="cpu-basic",
                          timeout="30m", expose=[PORT])
    except Exception as exc:  # noqa: BLE001
        note("LAUNCH_ERROR", f"{type(exc).__name__}: {str(exc)[:400]}", "warning")
        return 1
    note("JOB_ID", str(job.id))
    t0, ok, urls, stage, info = time.time(), None, [], None, None
    while time.time() - t0 < 480 and ok is None:
        info = api.inspect_job(job_id=job.id)
        stage = info.status.stage
        cand = [getattr(info, "endpoint", None), getattr(job, "endpoint", None), f"https://{job.id}--{PORT}.hf.jobs"]
        urls = [u for u in dict.fromkeys(cand) if u]
        if stage == "RUNNING":
            for u in urls:
                try:
                    r = requests.get(str(u).rstrip("/") + "/health", headers={"Authorization": "Bearer " + token}, timeout=15)
                    if r.status_code == 200:
                        ok = u
                        break
                except Exception:  # noqa: BLE001
                    pass
        if stage in ("ERROR", "COMPLETED", "CANCELED", "DELETED"):
            break
        time.sleep(10)
    logs = []
    try:
        for line in api.fetch_job_logs(job_id=job.id):
            logs.append(str(line))
    except Exception as exc:  # noqa: BLE001
        logs.append(f"logs: {type(exc).__name__}")
    note("STATE", f"stage={stage} health_ok_url={ok} urls_probadas={urls} logs_final={' | '.join(logs[-8:])[:600]}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
