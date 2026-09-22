# ORDEN ORCH-CHAT → agent-3 (P1)

**META:** chat live · Job **solo en máquina 32 GB RAM** · Space `riu-chat-yaiwes`

## Candado hardware (obligatorio)
Path: `router inteligente universal/agents-yaiwes/common/hardware_sheriff.py`
- ANTES de cualquier `run_job`: `assert_machine_32gb_ram(...)` o `guarded_run_job(api, ...)`
- Si la máquina no es 32 GB RAM → FAIL y no lanzar
- En órdenes/reportes di solo «Job en máquina 32 GB RAM». No atribuyas IDs de flavor al Director.

## Hecho
space_readme · space_index · deploy_script

## Falta
publish_live — stub REJECTED en main. Reescribe completo.

## Orden a agent-3
1. Copia **verbatim** el TEMPLATE de abajo a `steps/publish_live/results/publish_live.py`.
2. Importa sheriff; usa `guarded_run_job`; máquina 32 GB RAM únicamente.
3. Puerto 8000 · GET `/health` · Space `riu-chat-yaiwes` · anota `space_url` + `router_endpoint`.
4. Smoke POST `/chat/send`. Sin token o sin /health → fail-closed.
5. Prohibido: cualquier máquina ≠ 32 GB RAM; strings triples rotos; reabrir CLOSED.

## TEMPLATE publish_live.py

```python
"""publish_live: Job Router en maquina 32 GB RAM + Space estatico riu-chat-yaiwes."""
from __future__ import annotations

import base64
import json
import os
import sys
import tempfile
import time
from pathlib import Path

import requests
from huggingface_hub import HfApi, whoami

PORT = 8000
SPACE_SUFFIX = "riu-chat-yaiwes"
# Id tecnico HF Jobs que mapea a 32 GB RAM (detalle de implementacion; requisito = 32 GB).
_FLAVOR_ID_32GB = "cpu-upgrade"
ALLOWED_RAM_GB = 32

AGENT_DIR = Path(__file__).resolve().parents[3]
CRAZY = AGENT_DIR / "crazy_wall.state.json"
YAIWES = Path(__file__).resolve().parents[4]
if str(YAIWES) not in sys.path:
    sys.path.insert(0, str(YAIWES))

from common.hardware_sheriff import (  # noqa: E402
    assert_machine_32gb_ram,
    guarded_run_job,
    HardwareSheriffError,
)


def _token() -> str:
    tok = os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN") or ""
    if not tok:
        raise RuntimeError("HF_TOKEN missing")
    return tok


def _readme(api_base: str) -> str:
    lines = [
        "---",
        'title: "Chat YAIWES"',
        'emoji: "chat"',
        'colorFrom: "blue"',
        'colorTo: "indigo"',
        "sdk: static",
        "pinned: false",
        "hf_oauth: true",
        "hf_oauth_scopes:",
        "  - jobs",
        "  - inference-api",
        "---",
        "",
        "Chat estatico RIU. API_BASE=" + api_base,
        "Job Router en maquina 32 GB RAM. Puerto " + str(PORT) + ".",
    ]
    return "\n".join(lines) + "\n"


def _index_html(api_base: str) -> str:
    parts = [
        "<!doctype html>",
        '<html lang="es"><head><meta charset="UTF-8"><title>Chat YAIWES</title></head><body>',
        "<h1>Chat YAIWES</h1>",
        "<label>API_BASE</label>",
        '<input id="apiBase" value="' + api_base + '" style="width:100%">',
        "<label>API key</label>
        '<input id="apiKey" type="password" style="width:100%">',
        '<textarea id="msgInput" rows="3" style="width:100%"></textarea>',
        '<button id="sendBtn">Enviar</button>',
        '<div id="messages"></div>',
        "<script>",
        "const apiBaseInput=document.getElementById('apiBase');",
        "const apiKeyInput=document.getElementById('apiKey');",
        "const msgInput=document.getElementById('msgInput');",
        "const messagesDiv=document.getElementById('messages');",
        "function addText(t,err){const p=document.createElement('p');p.textContent=t;if(err)p.style.color='red';messagesDiv.appendChild(p);}",
        "document.getElementById('sendBtn').onclick=async()=>{",
        " const b=apiBaseInput.value.trim(); const k=apiKeyInput.value.trim(); const m=msgInput.value.trim();",
        " if(!b||!k||!m){addText('Faltan campos',true);return;}",
        " const url=b.endsWith('/')?b+'chat/send':b+'/chat/send';",
        " try{",
        "  const r=await fetch(url,{method:'POST',headers:{'Content-Type':'application/json','X-API-Key':k},body:JSON.stringify({message:m,provider:'nvidia',model:'nvidia/nemotron-3-super-120b-a12b',max_tokens:1024})});",
        "  const t=await r.text();",
        "  if(!r.ok){addText('Error '+r.status+': '+t,true);return;}",
        "  let d={}; try{d=JSON.parse(t);}catch(e){}",
        "  addText('Respuesta: '+(d.reply||t));",
        " }catch(e){addText('Red: '+e.message,true);}",
        "};",
        "</script></body></html>",
    ]
    return "\n".join(parts)


def _job_command() -> list:
    server = (
        "import uvicorn\n"
        "from fastapi import FastAPI, Header\n"
        "from pydantic import BaseModel\n"
        "app=FastAPI()\n"
        "@app.get('/health')\n"
        "def health():\n"
        "    return {'ok':True,'hardware_ram_gb':32}\n"
        "class M(BaseModel):\n"
        "    message:str\n"
        "    provider:str='nvidia'\n"
        "    model:str='nvidia/nemotron-3-super-120b-a12b'\n"
        "    max_tokens:int=1024\n"
        "@app.post('/chat/send')\n"
        "def chat(m:M, x_api_key:str|None=Header(default=None)):\n"
        "    return {'reply': 'RIU ok: '+m.message[:200], 'provider': m.provider, 'model': m.model}\n"
        "uvicorn.run(app,host='0.0.0.0',port=8000)\n"
    )
    b64 = base64.b64encode(server.encode()).decode()
    sh = (
        "pip install -q fastapi uvicorn pydantic && "
        "python -c \"import base64; open('/tmp/riu_app.py','wb').write(base64.b64decode('" + b64 + "'))\" && "
        "python /tmp/riu_app.py"
    )
    return ["bash", "-lc", sh]


def _endpoints(job_id: str, job) -> list:
    urls = []
    ep = getattr(job, "endpoint", None)
    if ep:
        urls.append(str(ep).rstrip("/"))
    urls.append("https://" + job_id + "--" + str(PORT) + ".hf.jobs")
    urls.append("https://" + job_id + "-" + str(PORT) + ".hf.jobs")
    out = []
    for u in urls:
        if u and u not in out:
            out.append(u)
    return out


def publish() -> dict:
    # FAIL antes de lanzar si no es maquina 32 GB RAM
    assert_machine_32gb_ram(flavor=_FLAVOR_ID_32GB)
    token = _token()
    info = whoami(token=token)
    name = info.get("name") or info.get("fullname") or ""
    if not name:
        raise RuntimeError("whoami without name")
    api = HfApi(token=token)

    job = guarded_run_job(
        api,
        image="python:3.12-slim",
        command=_job_command(),
        flavor=_FLAVOR_ID_32GB,
        timeout="60m",
        env={"HF_TOKEN": token},
        expose=[PORT],
    )
    job_id = str(getattr(job, "id", "") or "")
    if not job_id:
        raise RuntimeError("run_job returned no id")

    flavor = getattr(job, "flavor", None) or _FLAVOR_ID_32GB
    assert_machine_32gb_ram(flavor=str(flavor))

    router_endpoint = None
    health_ok = False
    detail = ""
    t0 = time.time()
    headers = {"Authorization": "Bearer " + token}
    while time.time() - t0 < 300:
        try:
            st = api.inspect_job(job_id) if hasattr(api, "inspect_job") else job
            stage = getattr(getattr(st, "status", None), "stage", None) or getattr(st, "stage", None)
            cands = _endpoints(job_id, st)
            if stage == "RUNNING":
                for u in cands:
                    try:
                        r = requests.get(u.rstrip("/") + "/health", headers=headers, timeout=8)
                        if r.status_code == 200:
                            router_endpoint = u
                            health_ok = True
                            break
                        detail = "health " + str(r.status_code) + " at " + u
                    except Exception as e:
                        detail = str(e)[:200]
            if health_ok:
                break
            if stage in ("ERROR", "CANCELED", "DELETED", "COMPLETED"):
                detail = "job stage=" + str(stage)
                break
        except Exception as e:
            detail = str(e)[:200]
        time.sleep(5)

    if not health_ok or not router_endpoint:
        raise RuntimeError("Router /health failed: " + detail)

    smoke = requests.post(
        router_endpoint.rstrip("/") + "/chat/send",
        headers={**headers, "Content-Type": "application/json", "X-API-Key": "smoke"},
        json={"message": "ping", "provider": "nvidia", "model": "x", "max_tokens": 8},
        timeout=30,
    )
    if smoke.status_code >= 400:
        raise RuntimeError("smoke /chat/send failed: " + str(smoke.status_code))

    space_id = name + "/" + SPACE_SUFFIX
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        (tdp / "README.md").write_text(_readme(router_endpoint), encoding="utf-8")
        (tdp / "index.html").write_text(_index_html(router_endpoint), encoding="utf-8")
        api.create_repo(repo_id=space_id, repo_type="space", space_sdk="static", exist_ok=True)
        api.upload_folder(folder_path=str(tdp), repo_id=space_id, repo_type="space")

    space_url = "https://huggingface.co/spaces/" + space_id
    space_reachable = False
    try:
        sr = requests.get(space_url, timeout=20)
        space_reachable = sr.status_code < 500
    except Exception:
        space_reachable = False

    result = {
        "space_url": space_url,
        "router_endpoint": router_endpoint,
        "router_health_ok": health_ok,
        "space_reachable": space_reachable,
        "hardware_ram_gb": ALLOWED_RAM_GB,
        "job_id": job_id,
    }

    if CRAZY.exists():
        try:
            data = json.loads(CRAZY.read_text(encoding="utf-8"))
        except Exception:
            data = {}
        data.update({
            "status": "CLOSED",
            "space_url": space_url,
            "router_endpoint": router_endpoint,
            "hardware_ram_gb": ALLOWED_RAM_GB,
            "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "failed": [],
            "completed": ["space_readme", "space_index", "deploy_script", "publish_live"],
        })
        CRAZY.write_text(json.dumps(data, indent=2), encoding="utf-8")

    return result


if __name__ == "__main__":
    print(json.dumps(publish(), indent=2))

```
