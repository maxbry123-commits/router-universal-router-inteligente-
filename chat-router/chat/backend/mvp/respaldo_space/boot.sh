#!/usr/bin/env bash
set -euo pipefail

# Verificar los secretos necesarios.
: "${GITHUB_TOKEN:?Falta GITHUB_TOKEN}"
: "${RIU_API_KEY:?Falta RIU_API_KEY}"

# Autenticacion Git desde secreto de entorno.
# Nunca incluir el token en la URL del repositorio.
export GIT_TERMINAL_PROMPT=0
export GIT_CONFIG_COUNT=1
export GIT_CONFIG_KEY_0=credential.helper
export GIT_CONFIG_VALUE_0='!f() { printf "username=x-access-token\npassword=%s\n" "$GITHUB_TOKEN"; }; f'

# GitHub es la unica fuente del codigo.
REPO="/tmp/repo"

rm -rf "$REPO"

git clone \
  --depth 1 \
  --single-branch \
  --branch main \
  https://github.com/maxbry123-commits/router-universal-router-inteligente-.git \
  "$REPO"

cd "$REPO"

# Verificar rama y commit.
echo "MVP_BRANCH=$(git branch --show-current)"
echo "MVP_COMMIT=$(git rev-parse HEAD)"

# Las dos raices del repo son router-mvp/ y chat-router/; NO existe mvp/ en la raiz.
export PYTHONPATH="$REPO/router-mvp:$REPO/chat-router${PYTHONPATH:+:$PYTHONPATH}"
test -f router-mvp/mvp/run.py
test -f router-mvp/mvp/app.py
test -f router-mvp/mvp/requirements.txt
test -f "chat-router/SWE CODE/web-bridge/src/server.js"

# Bridge existente dentro del MISMO contenedor: dependencias npm, sin otro despliegue.
npm install --omit=dev --no-audit --no-fund --prefix "chat-router/SWE CODE/web-bridge"

# El Runner MVP inicia/vigila el bridge Node y expone /web/* desde FastAPI.
exec python -m mvp.run
