import os
import sys
from huggingface_hub import HfApi

NAMESPACE = "COMAND-CENTER-1"
REPO_PATH = "maxbry123-commits/router-universal-router-inteligente-"
PINNED_HUB = "huggingface_hub==2.4.0"
SLEEP_S = 900
APPLY = "--apply" in sys.argv

def require(name):
    value = (os.getenv(name) or "").strip()
    if not value:
        sys.exit(f"ABORT: la variable {name} esta vacia o no existe. No se ha escrito nada.")
    return value

GITHUB_TOKEN = require("GITHUB_TOKEN")
HF_TOKEN = require("HF_TOKEN")
ROUTER_API_KEY = require("ROUTER_API_KEY")
BRANCH = (os.getenv("GITHUB_BRANCH") or "ccr-f01c3de9-bmry0s").strip()

CLONE = f'''REPO_URL="https://${{GITHUB_TOKEN}}@github.com/{REPO_PATH}.git"
TARGET_DIR="/tmp/repo"
if [ -d "$TARGET_DIR/.git" ]; then
    cd "$TARGET_DIR" && git fetch origin "{BRANCH}" && git reset --hard "origin/{BRANCH}"
else
    git clone --depth 1 --branch "{BRANCH}" "$REPO_URL" "$TARGET_DIR"
fi
'''

ROUTER_ENTRYPOINT = "#!/usr/bin/env bash\nset -e\n: \"${GITHUB_TOKEN:?GITHUB_TOKEN vacio}\"\n" + CLONE + \
    'cd "$TARGET_DIR/ROUTER MVP v1/system_prompt_py"\n' \
    f"pip install --no-cache-dir -r requirements.txt\n" \
    "exec uvicorn openai_compatible_proxy:app --host 0.0.0.0 --port 7860\n"

MODEL_ENTRYPOINT = "#!/usr/bin/env bash\nset -e\n: \"${GITHUB_TOKEN:?GITHUB_TOKEN vacio}\"\n" + CLONE + \
    'cd "$TARGET_DIR/llm system HF"\n' \
    "pip3 install --break-system-packages -q huggingface_hub\n" \
    "python3 download_model.py || echo \"Aviso: fallo la descarga, arrancando manager.\"\n" \
    "exec python3 manager.py\n"

ROUTER_REQUIREMENTS = "fastapi==0.115.0\nuvicorn[standard]==0.32.0\nhttpx==0.27.2\npydantic==2.9.2\naiosqlite==0.20.0\nddgs==9.0.0\nbeautifulsoup4==4.12.3\n" + PINNED_HUB + "\npytest==8.2.0\n"

ROUTER_DOCKERFILE = (
    "FROM python:3.11-slim\n"
    "RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*\n"
    "RUN useradd -m -u 1000 user\n"
    "USER user\n"
    "WORKDIR /app\n"
    "COPY --chown=user:user entrypoint.sh /app/entrypoint.sh\n"
    "RUN chmod +x /app/entrypoint.sh\n"
    "EXPOSE 7860\n"
    "CMD [\"/app/entrypoint.sh\"]\n"
)

MODEL_DOCKERFILE = (
    "FROM ubuntu:24.04\n"
    "ENV DEBIAN_FRONTEND=noninteractive\n"
    "RUN apt-get update && apt-get install -y curl ca-certificates python3 python3-pip git tar gzip libgomp1 && rm -rf /var/lib/apt/lists/*\n"
    "ARG LLAMA_URL=https://github.com/ggerganov/llama.cpp/releases/download/b12000/llama-b12000-bin-ubuntu-x64.tar.gz\n"
    "RUN mkdir -p /opt/llama && curl -fsSL \"$LLAMA_URL\" -o /tmp/llama.tgz && tar -xzf /tmp/llama.tgz -C /opt/llama && rm /tmp/llama.tgz \\\n"
    "    && BIN=$(find /opt/llama -type f -name llama-server | head -1) \\\n"
    "    && test -n \"$BIN\" \\\n"
    "    && ln -sf \"$BIN\" /usr/local/bin/llama-server\n"
    "EXPOSE 7860\n"
    "CMD [\"/app/entrypoint.sh\"]\n"
)

SPACES = {
    f"{NAMESPACE}/riu-router": {
        "entrypoint.sh": ROUTER_ENTRYPOINT,
        "requirements.txt": ROUTER_REQUIREMENTS,
        "Dockerfile": ROUTER_DOCKERFILE,
        "README.md": "---\ntitle: RIU Router\nsdk: docker\napp_port: 7860\n---\n",
        "secrets": {"GITHUB_TOKEN": GITHUB_TOKEN, "GITHUB_BRANCH": BRANCH, "ROUTER_API_KEY": ROUTER_API_KEY},
    },
    f"{NAMESPACE}/swe-code-s1": {
        "entrypoint.sh": MODEL_ENTRYPOINT,
        "requirements.txt": PINNED_HUB + "\n",
        "Dockerfile": MODEL_DOCKERFILE,
        "README.md": "---\ntitle: SWE Code S1\nsdk: docker\napp_port: 7860\n---\n",
        "secrets": {"GITHUB_TOKEN": GITHUB_TOKEN, "GITHUB_BRANCH": BRANCH, "ROUTER_API_KEY": ROUTER_API_KEY},
    },
}

def plan():
    print(f"Modo: {'APLICAR' if APPLY else 'SIMULACION (no escribe nada; pasa --apply para ejecutar)'}")
    print(f"Rama de clonado: {BRANCH}")
    for space, cfg in SPACES.items():
        print(f"- {space}: archivos {sorted(k for k in cfg if k not in ('secrets',))}, secretos {sorted(cfg['secrets'])}, sleep_time={SLEEP_S}")

def apply_all():
    api = HfApi(token=HF_TOKEN)
    for space, cfg in SPACES.items():
        for key, value in cfg["secrets"].items():
            api.add_space_secret(repo_id=space, key=key, value=value)
        api.set_space_sleep_time(repo_id=space, sleep_time=SLEEP_S)
        for name in ("entrypoint.sh", "requirements.txt", "Dockerfile", "README.md"):
            api.upload_file(path_or_fileobj=cfg[name].encode(), path_in_repo=name, repo_id=space, repo_type="space")
        print(f"OK {space}: secretos, sleep_time y archivos actualizados (el build se dispara solo).")

if __name__ == "__main__":
    plan()
    if APPLY:
        apply_all()
