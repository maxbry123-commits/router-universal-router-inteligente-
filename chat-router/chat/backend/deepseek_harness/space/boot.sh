#!/usr/bin/env bash
set -euo pipefail
rm -rf /tmp/repo
: "${GITHUB_TOKEN:?GITHUB_TOKEN ausente}"
# Token solo via header efimero (-c): no queda en la URL, .git/config ni logs.
git -c http.https://github.com/.extraheader="Authorization: Basic $(printf 'x-access-token:%s' "$GITHUB_TOKEN" | base64 -w0)" \
  clone --depth 1 -b main https://github.com/maxbry123-commits/router-universal-router-inteligente-.git /tmp/repo
echo "HEAD=$(git -C /tmp/repo rev-parse HEAD)"
cd /tmp/repo
# Agentes reales: ya instalados en el build (RIU_AGENTES_RUNTIME, ver Dockerfile); esto instala solo lo que falte (idempotente) y NO retrasa el puerto 7860:
# hasta que termine, el selector muestra NO INSTALADO lo que aun no esta. Un fallo no impide arrancar (log en /tmp/instalar-agentes.log, sin claves).
export RIU_AGENTES_RUNTIME="${RIU_AGENTES_RUNTIME:-/opt/riu-agentes}"
( RIU_INSTALAR_TOLERANTE=1 bash /tmp/repo/chat-router/agentes/runtime/instalar-agentes.sh > /tmp/instalar-agentes.log 2>&1 \
  && bash /tmp/repo/chat-router/agentes/runtime/verificar-agentes.sh >> /tmp/instalar-agentes.log 2>&1 ) &
export PYTHONPATH=/tmp/repo/chat-router:/tmp/repo/router-mvp:/tmp/repo  # server.py importa plugins.router_api_cliente y agentes.adaptadores (ambos bajo chat-router)
exec python -m uvicorn plugins.deepseek_harness.server:app --host 0.0.0.0 --port 7860
