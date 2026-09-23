# chat_backend_32gb.py
import os
import sys
import time
import json
from huggingface_hub import HfApi
import requests

def assert_machine_32gb_ram(flavor: str):
    """Valida que el flavor sea exactamente cpu-upgrade (32GB RAM)"""
    if flavor != "cpu-upgrade":
        raise ValueError(f"Flavor {flavor} no es la máquina de 32GB RAM requerida (cpu-upgrade)")

def guarded_run_job(api: HfApi, repo_id: str, flavor: str, *args, **kwargs):
    """Wrapper que verifica flavor antes de lanzar job"""
    assert_machine_32gb_ram(flavor)
    return api.run_job(repo_id=repo_id, flavor=flavor, *args, **kwargs)

def main():
    # Obtener token HF
    hf_token = os.environ.get("HF_TOKEN")
    if not hf_token:
        raise ValueError("HF_TOKEN no está configurado")

    # Verificar job existente sano
    api = HfApi(token=hf_token)
    existing_jobs = api.list_jobs(status="RUNNING")
    
    # Buscar job compatible existente
    target_endpoint = None
    for job in existing_jobs:
        if job.get("flavor") == "cpu-upgrade" and "chat-backend" in job.get("name", ""):
            job_id = job["id"]
            try:
                resp = requests.get(
                    f"https://{job_id}--8080.hf.jobs/chat/providers",
                    headers={"Authorization": f"Bearer {hf_token}"},
                    timeout=10
                )
                if resp.status_code == 200:
                    target_endpoint = f"https://{job_id}--8080.hf.jobs"
                    break
            except:
                continue

    if not target_endpoint:
        # Lanzar nuevo job con imagen Python, clonando repo público
        # Usar guarded_run_job para validar 32GB
        job_response = guarded_run_job(
            api,
            repo_id=".",  # repo actual clonado
            flavor="cpu-upgrade",
            name="chat-backend-32gb",
            sleep_until_status="RUNNING",
            max_duration_seconds=3600,  # 60 minutos
            expose=[8080],
            image="python:3.10-slim",
            command="""
            pip install huggingface_hub requests uvicorn fastapi
            python -c "
import os, subprocess
# Clonar repo actual (público)
subprocess.run(['git', 'clone', 'https://huggingface.co/spaces/COMAND-CENTER-1/router-inteligente-universal', '.'], check=True)
# Instalar dependencias del chat_mvp
subprocess.run(['pip', 'install', '-r', 'integration/chat_mvp/requirements.txt'], check=True)
# Ejecutar uvicorn
os.environ['RIU_DATA_DIR'] = '/data'
os.chdir('router-inteligente-universal')
subprocess.run(['uvicorn', 'integration.chat_mvp.app:app', '--host', '0.0.0.0', '--port', '8080'], check=True)
"
            """,
            volume={
                "type": "bucket",
                "source": "COMAND-CENTER-1/yaiwes-v54",
                "mount_path": "/data"
            },
            env={
                "RIU_DATA_DIR": "/data",
                "HF_TOKEN": hf_token
            }
        )
        job_id = job_response["id"]
        target_endpoint = f"https://{job_id}--8080.hf.jobs"

    # Hacer smoke test hasta HTTP 200
    max_attempts = 20
    for attempt in range(max_attempts):
        try:
            resp = requests.get(
                f"{target_endpoint}/chat/providers",
                headers={"Authorization": f"Bearer {hf_token}"},
                timeout=10
            )
            if resp.status_code == 200:
                providers_data = resp.json()
                # Devolver resultado exitoso
                result = {
                    "job_id": job_id if not target_endpoint.startswith("https://") else target_endpoint.split("--")[0].split("//")[1],
                    "endpoint": f"{target_endpoint}",
                    "flavor": "cpu-upgrade",
                    "providers_http": providers_data,
                    "status": "RUNNING_HEALTHY"
                }
                print(json.dumps(result))
                sys.exit(0)
        except:
            pass
        time.sleep(15)  # Esperar 15s entre intentos

    # Si llegamos aquí, smoke test falló
    raise RuntimeError("Smoke test de /chat/providers no devolvió HTTP 200 después de 20 intentos (~5 min)")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"FALLO CRÍTICO: {e}", file=sys.stderr)
        sys.exit(1)
