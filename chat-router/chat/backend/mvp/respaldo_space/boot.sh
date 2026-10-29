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

# Verificar archivos requeridos.
test -f mvp/run.py
test -f mvp/app.py
test -f mvp/requirements.txt

# Ejecutar exclusivamente el MVP.
exec python -m mvp.run
