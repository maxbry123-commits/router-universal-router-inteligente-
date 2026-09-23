"""publish_live option 3: Static Space + OAuth + Inference Providers. No Job."""
from __future__ import annotations

import json
import os
import tempfile
import time
from pathlib import Path

import requests
from huggingface_hub import HfApi, whoami

SPACE_NAME = "riu-chat-yaiwes"
AGENT_DIR = Path(__file__).resolve().parents[3]
CRAZY = AGENT_DIR / "crazy_wall.state.json"
OUT = Path(__file__).resolve().parent / "output.txt"


def _token() -> str:
    tok = os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN") or ""
    if not tok:
        raise RuntimeError("HF_TOKEN missing")
    return tok


def _readme() -> str:
    return (
        "---\n"
        "title: Chat YAIWES\n"
        "emoji: 💬\n"
        "colorFrom: blue\n"
        "colorTo: indigo\n"
        "sdk: static\n"
        "pinned: false\n"
        "hf_oauth: true\n"
        "hf_oauth_scopes:\n"
        "  - inference-api\n"
        "---\n\n"
        "RIU Static Chat — OAuth + Inference Providers. Sin Job permanente.\n"
    )


def _index_html() -> str:
    return """<!doctype html>
<html lang="es">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>Chat YAIWES</title>
  <style>
    body{font-family:system-ui,sans-serif;max-width:720px;margin:2rem auto;padding:0 1rem}
    textarea,select,button{width:100%;margin:.4rem 0;padding:.5rem}
    #log{white-space:pre-wrap;border:1px solid #ddd;padding:.75rem;min-height:8rem}
  </style>
</head>
<body>
  <h1>Chat YAIWES</h1>
  <p id="auth">Comprobando OAuth…</p>
  <select id="model">
    <option value="deepseek-ai/DeepSeek-V3">DeepSeek V3</option>
    <option value="MiniMaxAI/MiniMax-M2">MiniMax M2</option>
    <option value="moonshotai/Kimi-K2-Instruct">Kimi K2</option>
    <option value="nvidia/Llama-3.1-Nemotron-70B-Instruct-HF">NVIDIA Nemotron</option>
  </select>
  <textarea id="msg" rows="4" placeholder="Escribe un mensaje"></textarea>
  <button id="send">Enviar</button>
  <div id="log"></div>
  <script>
  const logEl = document.getElementById('log');
  function log(t, err){ const p=document.createElement('p'); p.textContent=t; if(err)p.style.color='crimson'; logEl.appendChild(p); }
  async function tokenFromOAuth(){
    if (window.huggingface && window.huggingface.oauth && window.huggingface.oauth.token) {
      const tok = window.huggingface.oauth.token;
      return tok.accessToken || tok.access_token || null;
    }
    try {
      const r = await fetch('/auth/oauth-info', {credentials:'include'});
      if (r.ok) {
        const j = await r.json();
        if (j && j.accessToken) return j.accessToken;
      }
    } catch (e) {}
    return null;
  }
  async function refreshAuth(){
    const t = await tokenFromOAuth();
    const el = document.getElementById('auth');
    if (t) { el.textContent = 'OAuth OK'; return t; }
    el.innerHTML = 'Necesitas <a href="/oauth/authorize?scope=inference-api">iniciar sesión HF</a>';
    return null;
  }
  document.getElementById('send').onclick = async () => {
    const tok = await refreshAuth();
    if (!tok) { log('Sin OAuth', true); return; }
    const model = document.getElementById('model').value;
    const message = document.getElementById('msg').value.trim();
    if (!message) { log('Mensaje vacío', true); return; }
    log('→ ' + message);
    try {
      const r = await fetch('https://router.huggingface.co/v1/chat/completions', {
        method:'POST',
        headers:{
          'Authorization':'Bearer '+tok,
          'Content-Type':'application/json'
        },
        body: JSON.stringify({
          model: model,
          messages:[{role:'user', content: message}],
          max_tokens: 512
        })
      });
      const txt = await r.text();
      if (!r.ok) { log('Error '+r.status+': '+txt.slice(0,500), true); return; }
      let data={}; try{data=JSON.parse(txt);}catch(e){}
      const reply = (data.choices && data.choices[0] && data.choices[0].message && data.choices[0].message.content) || txt;
      log('← ' + reply);
    } catch(e) { log('Red: '+e.message, true); }
  };
  refreshAuth();
  </script>
</body>
</html>
"""


def publish() -> dict:
    token = _token()
    info = whoami(token=token)
    name = info.get("name") or ""
    if not name:
        raise RuntimeError("whoami without name")
    api = HfApi(token=token)
    space_id = name + "/" + SPACE_NAME
    space_url = "https://huggingface.co/spaces/" + space_id

    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        (tdp / "README.md").write_text(_readme(), encoding="utf-8")
        (tdp / "index.html").write_text(_index_html(), encoding="utf-8")
        api.create_repo(
            repo_id=space_id,
            repo_type="space",
            space_sdk="static",
            exist_ok=True,
        )
        api.upload_folder(
            folder_path=str(tdp),
            repo_id=space_id,
            repo_type="space",
        )

    live_ok = False
    http_code = 0
    headers = {"Authorization": "Bearer " + token}
    # allow build propagation
    for _ in range(12):
        try:
            r = requests.get(space_url, headers=headers, timeout=30, allow_redirects=True)
            http_code = r.status_code
            if r.status_code != 404 and r.status_code < 500:
                live_ok = True
                break
        except Exception:
            pass
        time.sleep(5)

    if not live_ok:
        raise RuntimeError(
            "Space not live (HTTP %s). Refusing paper CLOSED. space_url=%s"
            % (http_code, space_url)
        )

    OUT.write_text(
        "space_url: " + space_url + "\n"
        "provider_endpoint: https://router.huggingface.co/v1/chat/completions\n"
        "http_code: " + str(http_code) + "\n",
        encoding="utf-8",
    )

    result = {
        "space_url": space_url,
        "space_id": space_id,
        "http_code": http_code,
        "deploy_mode": "option3_static_oauth_inference",
        "job_deferred": True,
        "status": "PENDING_VERIFY",
    }

    if CRAZY.exists():
        try:
            data = json.loads(CRAZY.read_text(encoding="utf-8"))
        except Exception:
            data = {}
        # Never CLOSED here — orch verifies GET live first
        data["status"] = "PENDING_VERIFY"
        data["space_url"] = space_url
        data["deploy_mode"] = "INPUT-l option 3 Static+OAuth+InferenceProviders"
        data["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        data["blockers"] = []
        data["failed"] = []
        data["completed"] = ["space_readme", "space_index", "deploy_script", "publish_live"]
        data["hardware_requirement"] = "No HF Job this round; option 2 Job-32GB deferred"
        CRAZY.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    return result


if __name__ == "__main__":
    print(json.dumps(publish(), indent=2))
