#!/usr/bin/env bash
set -euo pipefail

# Verificar los secretos necesarios.
: "${GITHUB_TOKEN:?Falta GITHUB_TOKEN}"
: "${RIU_API_KEY:?Falta RIU_API_KEY}"

# Rama de arranque: variable GITHUB_BRANCH, default la rama de trabajo de Router 1.
GITHUB_BRANCH="${GITHUB_BRANCH:-ccr-f01c3de9-bmry0s}"

export GIT_TERMINAL_PROMPT=0
export GIT_CONFIG_COUNT=1
export GIT_CONFIG_KEY_0=credential.helper
export GIT_CONFIG_VALUE_0='!f() { printf "username=x-access-token\npassword=%s\n" "$GITHUB_TOKEN"; }; f'

REPO="/tmp/repo"
rm -rf "$REPO"

git clone \
  --depth 1 \
  --filter=blob:none \
  --no-checkout \
  --single-branch \
  --branch "$GITHUB_BRANCH" \
  https://github.com/maxbry123-commits/router-universal-router-inteligente-.git \
  "$REPO"

cd "$REPO"
git sparse-checkout set --no-cone '/*' \
  '!/chat-router/agentes/agentes-listos/' '!/chat-router/agentes/frameworks/' \
  '!/chat-router/agentes/investigacion/' '!/chat-router/chatbot/' \
  '!/chat-router/memoria/' '!/chat-router/otros/' \
  '!/chat-router/workflow-loop-code-yaiwes/'
git checkout -q "$GITHUB_BRANCH"

echo "MVP_BRANCH=$(git branch --show-current)"
echo "MVP_COMMIT=$(git rev-parse HEAD)"
# Resto del arranque (web-bridge, puente-movil, openclaw, router :7861, proxy :7860):
# ver el historial de este archivo en el Space riu-router. Codigo no invocado por el Dockerfile.
