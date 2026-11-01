FROM node:22-slim AS nodo
FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir fastapi "uvicorn[standard]"
# Node 22 (codex, opencode, claude y openclaw son paquetes npm): copiado de la imagen oficial, sin apt
COPY --from=nodo /usr/local/bin/node /usr/local/bin/node
COPY --from=nodo /usr/local/lib/node_modules /usr/local/lib/node_modules
RUN ln -s ../lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm && ln -s ../lib/node_modules/npm/bin/npx-cli.js /usr/local/bin/npx
# Agentes REALES (chat-router/agentes/runtime/instalar-agentes.sh): se instalan en el BUILD en /opt/riu-agentes (los adaptadores lo encuentran por RIU_AGENTES_RUNTIME).
# Necesita el secreto de build GITHUB_TOKEN (el repo es privado); sin el, el paso se salta y boot.sh instala lo que falte al arrancar. Idempotente.
ENV RIU_AGENTES_RUNTIME=/opt/riu-agentes
RUN --mount=type=secret,id=GITHUB_TOKEN \
    if [ -s /run/secrets/GITHUB_TOKEN ]; then \
      rm -rf /tmp/repo-build \
      && git -c http.https://github.com/.extraheader="Authorization: Basic $(printf 'x-access-token:%s' "$(cat /run/secrets/GITHUB_TOKEN)" | base64 -w0)" \
         clone --depth 1 -b main https://github.com/maxbry123-commits/router-universal-router-inteligente-.git /tmp/repo-build \
      && (RIU_INSTALAR_TOLERANTE=1 bash /tmp/repo-build/chat-router/agentes/runtime/instalar-agentes.sh || echo "instalar-agentes.sh fallo en el build; boot.sh reintenta"); \
      rm -rf /tmp/repo-build; \
    else echo "sin secreto de build GITHUB_TOKEN: los agentes se instalan al arrancar (boot.sh)"; fi
WORKDIR /app
COPY boot.sh /boot.sh
RUN chmod +x /boot.sh
EXPOSE 7860
CMD ["/boot.sh"]
