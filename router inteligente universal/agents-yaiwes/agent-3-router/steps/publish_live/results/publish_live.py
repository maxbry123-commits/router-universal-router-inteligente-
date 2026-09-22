```python
import os
import time
import tempfile
import requests
from huggingface_hub import HfApi

def publish() -> dict:
    token = os.environ["HF_TOKEN"]
    api = HfApi(token=token)

    # 1) Get account name
    whoami = api.whoami()
    account = whoami.get("name")
    if not account:
        raise RuntimeError("Unable to retrieve HF account name")

    # 2) Launch Router Job
    repo = "https://github.com/maxbry123-commits/router-universal-router-inteligente-"
    clone_cmd = (
        f"git clone --depth 1 --filter=blob:none --sparse {repo} r && "
        f"cd r && "
        f"git sparse-checkout set --no-cone \"router inteligente universal\" \"Chat Mvp/secret_bank\" && "
        f"pip install fastapi uvicorn[standard] pydantic huggingface_hub cryptography pyyaml && "
        f"python \"router inteligente universal/agents-yaiwes/common/router_job_start.py\""
    )
    job = api.run_job(
        command=clone_cmd,
        image="python:3.12",
        flavor="cpu-basic",
        expose=[8000],
    )
    job_id = job.id
    router_endpoint = f"https://{job_id}--8000.hf.jobs"

    # 3) Wait for job to be RUNNING and health endpoint to respond 200
    start = time.time()
    timeout = 300
    router_health_ok = False
    while time.time() - start < timeout:
        try:
            job_status = api.job_status(job_id)
            if getattr(job_status, "stage", None) == "RUNNING":
                health_url = f"{router_endpoint}/health"
                headers = {"Authorization": f"Bearer {token}"}
                resp = requests.get(health_url, headers=headers, timeout=10)
                if resp.status_code == 200:
                    router_health_ok = True
                    break
        except Exception:
            pass
        time.sleep(5)
    if not router_health_ok:
        raise RuntimeError("Router job did not become healthy within timeout")

    # 4) Prepare static files in a temporary folder
    with tempfile.TemporaryDirectory() as tmpdir:
        readme_path = os.path.join(tmpdir, "README.md")
        index_path = os.path.join(tmpdir, "index.html")

        readme_content = '''---
title: "Chat YAIWES"
emoji: "💬"
colorFrom: "blue"
colorTo: "indigo"
sdk: static
pinned: false
hf_oauth: true
hf_oauth_scopes:
  - jobs
  - inference-api
---
Este Space estático proporciona una interfaz de chat basada en HTML y JavaScript que se ejecuta totalmente en el navegador del usuario. No almacena ni expone claves privadas; toda la información sensible permanece en el servidor del Router, que se ejecuta como un Job de Hugging Face con los recursos especificados (8 vCPU / 32 GB). La interfaz se comunica mediante peticiones HTTP al endpoint expuesto por el Job (https://<job_id>--8000.hf.jobs), enviando el cuerpo JSON requerido por la API del Router y recibiendo la respuesta con el mensaje, el identificador de conversación y otros campos. Para autenticar sin necesidad de un token maestro, el Space utiliza HF OAuth, solicitando únicamente los scopes `jobs` e `inference-api`, lo que permite al frontend iniciar y consultar el Job y, si es necesario, acceder a proveedores de inferencia de forma segura. Todo el código del Space es público y revisable, garantizando transparencia, ausencia de credenciales sensibles y una experiencia de chat que depende exclusivamente del Router ejecutado en un Job de HF.
'''

        index_content = '''<!doctype html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>Chat YAIWES</title>
<style>
  body {font-family: Arial, sans-serif; margin: 20px; background:#f9f9f9;}
  .container {max-width: 600px; margin:auto; background:#fff; padding:20px; border-radius:8px; box-shadow:0
