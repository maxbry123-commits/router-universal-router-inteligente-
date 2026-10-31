# swe-code-web: puente web -> OpenAI-compatible (scale-to-zero Space)
# CONTEXTO DE BUILD = RAIZ DEL REPO (el bridge lee archivos de chat-router/SWE CODE free y chat-router/chat/backend/mvp):
#   docker build -f "chat-router/SWE CODE/web-bridge/Dockerfile" -t swe-code-web .
# La imagen conserva la misma disposicion de carpetas que el repo (/repo/chat-router/...), asi las rutas por defecto del codigo funcionan sin variables.
# Nota: el Space REAL no usa esta imagen tal cual; arranca clonando el repo (autopull) y ejecuta src/server.js desde el clon.
FROM node:20-slim

# python3 + cryptography (banco cifrado, claves_banco.py) y las dependencias de mvp.memoria (memoria_hf.py); Chromium headless + deps OSS (se auto-descarga al build)
RUN apt-get update && apt-get install -y --no-install-recommends python3 python3-pip python3-cryptography git ca-certificates \
 && pip3 install --no-cache-dir --break-system-packages fastapi httpx huggingface_hub \
 && rm -rf /var/lib/apt/lists/*
RUN npx -y playwright@1.47 install --with-deps chromium

WORKDIR /repo/chat-router/SWE CODE/web-bridge
COPY ["chat-router/SWE CODE/web-bridge/package.json", "./"]
RUN npm install --omit=dev
COPY ["chat-router/SWE CODE/web-bridge/src", "./src"]
COPY ["chat-router/SWE CODE/web-bridge/claves_banco.py", "chat-router/SWE CODE/web-bridge/memoria_hf.py", "./"]
# gramatica "SWEN CODE free" (activar.js + documentos.js) y la config de OpenClaw (provider-openclaw.json, swen.json)
COPY ["chat-router/SWE CODE free/activar.js", "chat-router/SWE CODE free/documentos.js", "chat-router/SWE CODE free/provider-openclaw.json", "chat-router/SWE CODE free/swen.json", "/repo/chat-router/SWE CODE free/"]
# banco cifrado y memoria compartida (mvp.bank, mvp.memoria, mvp.hf_store) y el formato de salida del chat
COPY ["chat-router/chat/backend/mvp/bank.py", "chat-router/chat/backend/mvp/memoria.py", "chat-router/chat/backend/mvp/hf_store.py", "/repo/chat-router/chat/backend/mvp/"]
COPY ["chat-router/chat/backend/mvp/prompts/FORMATO_SALIDA.md", "/repo/chat-router/chat/backend/mvp/prompts/"]

ENV BRIDGE_PORT=7870 \
    BRIDGE_STATE_DIR=/data/state \
    RIU_REPO_ROOT=/repo
# secrets del Space: WEB_ACCOUNTS (correos), WEB_PASS (clave), BRIDGE_TOKEN y/o RIU_API_KEY (acceso), BRIDGE_PROXY (opcional)
EXPOSE 7870
CMD ["node", "src/server.js"]
