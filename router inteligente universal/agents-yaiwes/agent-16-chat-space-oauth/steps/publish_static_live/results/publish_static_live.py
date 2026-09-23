import json
import os
import requests
import time
import sys

HF_TOKEN = os.environ.get("HF_TOKEN")
if not HF_TOKEN:
    print("{\"error\": \"HF_TOKEN no encontrado\"}", file=sys.stderr)
    sys.exit(1)

headers = {"Authorization": f"Bearer {HF_TOKEN}"}

# Obtener owner
r = requests.get("https://huggingface.co/api/whoami", headers=headers)
if r.status_code != 200:
    print(f"{\"error\": \"whoami falló: {r.status_code}\"}", file=sys.stderr)
    sys.exit(1)
owner = r.json()["name"]

space_id = f"{owner}/riu-chat-yaiwes"
space_url = f"https://huggingface.co/spaces/{space_id}"

# Crear o actualizar el Space como Static Space público
create_url = f"https://huggingface.co/api/spaces"
create_data = {
    "name": "riu-chat-yaiwes",
    "type": "static",
    "private": False,
    "sdk": "static",
    "hf_oauth": True,
    "scopes": ["inference-api", "read-repos", "write-repos", "jobs"]
}
r = requests.post(create_url, headers=headers, json=create_data)
if r.status_code == 422 and "already exists" in r.text:
    # Actualizar Space existente
    update_url = f"https://huggingface.co/api/spaces/{space_id}"
    r = requests.put(update_url, headers=headers, json=create_data)
    if r.status_code not in (200, 201):
        print(f"{\"error\": \"Actualización falló: {r.status_code} - {r.text}\"}", file=sys.stderr)
        sys.exit(1)
elif r.status_code not in (200, 201):
    print(f"{\"error\": \"Creación falló: {r.status_code} - {r.text}\"}", file=sys.stderr)
    sys.exit(1)

# Subir README.md
readme_content = """---
title: RIU Chat YAIWES
emoji: 🤖
colorFrom: blue
colorTo: green
sdk: static
hf_oauth: true
scopes:
  - inference-api
  - read-repos
  - write-repos
  - jobs
---"""
upload_url = f"https://huggingface.co/api/spaces/{space_id}/files/.gitattributes"
r = requests.put(f"https://huggingface.co/api/spaces/{space_id}/files/README.md", headers=headers, data=readme_content)
if r.status_code not in (200, 201):
    print(f"{\"error\": \"Subida README falló: {r.status_code}\"}", file=sys.stderr)
    sys.exit(1)

# Subir index.html
index_html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>RIU Chat YAIWES</title>
    <script src="https://cdn.jsdelivr.net/npm/@huggingface/hub@0.4.4/dist/index.umd.js"></script>
</head>
<body>
    <h1>RIU Chat YAIWES</h1>
    <div id="auth-section">
        <button id="login-btn" style="display:none">Sign in with HF</button>
        <p id="user-info" style="display:none">Logged in as: <span id="username"></span></p>
        <button id="logout-btn" style="display:none">Logout</button>
    </div>
    <div id="chat-section" style="display:none">
        <label for="model-select">Model:</label>
        <select id="model-select">
            <option value="meta-llama/Llama-3.2-11B-Vision-Instruct">Llama 3.2 11B</option>
            <option value="Qwen/Qwen2.5-72B-Instruct">Qwen 2.5 72B</option>
            <option value="mistralai/Mixtral-8x22B-Instruct-v0.1">Mixtral 8x22B</option>
        </select>
        <div id="messages" style="border:1px solid #ccc; height:300px; overflow-y:scroll; margin:10px 0; padding:10px;"></div>
        <input type="text" id="user-input" placeholder="Type your message..." style="width:80%">
        <button id="send-btn">Send</button>
    </div>
    <script>
        (async function() {
            const { oauthLoginUrl, oauthHandleRedirectIfPresent } = window.HF?.Hub || self.HF?.Hub;
            if (!oauthLoginUrl || !oauthHandleRedirectIfPresent) {
                document.body.innerHTML += '<p>Error: HF Hub library not loaded.</p>';
                return;
            }

            const clientId = (await (await fetch('https://huggingface.co/api/spaces/' + window.location.hostname.replace('-spaces', '') + '/oauth-info', {headers: {'Referer': window.location.origin}})).json()).client_id;
            const config = { clientId, scopes: ['openid', 'profile', 'inference-api', 'read-repos', 'write-repos', 'jobs'] };

            // Handle redirect
            const result = await oauthHandleRedirectIfPresent();
            if (result) {
                localStorage.setItem('huggingface_token', result.accessToken);
                window.location.hash = '';
            }

            const accessToken = localStorage.getItem('huggingface_token');
            const loginBtn = document.getElementById('login-btn');
            const logoutBtn = document.getElementById('logout-btn');
            const userInfo = document.getElementById('user-info');
            const username = document.getElementById('username');
            const chatSection = document.getElementById('chat-section');

            if (accessToken) {
                loginBtn.style.display = 'none';
                userInfo.style.display = 'block';
                chatSection.style.display = 'block';
                const userResp = await fetch('https://huggingface.co/api/whoami', {headers: {'Authorization': 'Bearer ' + accessToken}});
                const userData = await userResp.json();
                username.textContent = userData.name;

                document.getElementById('send-btn').addEventListener('click', async () => {
                    const model = document.getElementById('model-select').value;
                    const input = document.getElementById('user-input').value;
                    const messagesDiv = document.getElementById('messages');
                    messagesDiv.innerHTML += '<div><b>You:</b> ' + input + '</div>';

                    const response = await fetch('https://router.huggingface.co/v1/chat/completions', {
                        method: 'POST',
                        headers: {
                            'Authorization': 'Bearer ' + accessToken,
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({model, messages: [{role: 'user', content: input}], max_tokens: 500})
                    });
                    const data = await response.json();
                    messagesDiv.innerHTML += '<div><b>AI:</b> ' + data.choices[0].message.content + '</div>';
                    document.getElementById('user-input').value = '';
                });
            } else {
                loginBtn.style.display = 'block';
                const url = await oauthLoginUrl(config);
                loginBtn.addEventListener('click', () => { window.location.href = url; });
            }

            logoutBtn.addEventListener('click', () => {
                localStorage.removeItem('huggingface_token');
                window.location.reload();
            });
        })();
    </script>
</body>
</html>"""

r = requests.put(f"https://huggingface.co/api/spaces/{space_id}/files/index.html", headers=headers, data=index_html)
if r.status_code not in (200, 201):
    print(f"{\"error\": \"Subida index.html falló: {r.status_code}\"}", file=sys.stderr)
    sys.exit(1)

# Verificar Space público
time.sleep(5)
for attempt in range(5):
    r = requests.get(space_url)
    if r.status_code != 404:
        break
    time.sleep(3)

http_code = r.status_code

result = {
    "owner": owner,
    "space_id": space_id,
    "space_url": space_url,
    "http_code": http_code,
    "oauth": True,
    "status": "LIVE" if http_code != 404 else "ERROR"
}

print(json.dumps(result))
