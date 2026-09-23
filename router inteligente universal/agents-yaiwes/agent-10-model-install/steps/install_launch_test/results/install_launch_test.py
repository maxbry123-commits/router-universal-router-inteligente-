We are to copy the TEMPLATE from ORDEN-HF.md verbatim. The TEMPLATE is between BEGIN_TEMPLATE and END_TEMPLATE.
 We are not to regenerate, so we must output exactly the template as given.

 However, note that the user's previous attempt failed because of an unterminated string literal.
 We must ensure that the output is exactly the template without any changes.

 Let's extract the template from the ORDEN-HF.md file provided in the context.

 The template is:

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
                     if resp.status_code == 2
