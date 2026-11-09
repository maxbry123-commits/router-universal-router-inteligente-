#!/usr/bin/env bash
set -euo pipefail

# Verificar los secretos necesarios.
: "${GITHUB_TOKEN:?Falta GITHUB_TOKEN}"
: "${RIU_API_KEY:?Falta RIU_API_KEY}"

# Rama de arranque: variable GITHUB_BRANCH, default la rama de trabajo de Router 1.
# (antes estaba fija a main; ver Claude notas.md, flag de boot.sh)
GITHUB_BRANCH="${GITHUB_BRANCH:-ccr-f01c3de9-bmry0s}"

# Autenticacion Git desde secreto de entorno.
# Nunca incluir el token en la URL del repositorio.
export GIT_TERMINAL_PROMPT=0
export GIT_CONFIG_COUNT=1
export GIT_CONFIG_KEY_0=credential.helper
export GIT_CONFIG_VALUE_0='!f() { printf "username=x-access-token\npassword=%s\n" "$GITHUB_TOKEN"; }; f'

# GitHub es la unica fuente del codigo.
REPO="/tmp/repo"

rm -rf "$REPO"

# El repo GitHub pesa >8 GB (agentes vendorizados); clon parcial + sparse
# excluyendo carpetas pesadas que el router no usa (antes: clone colgado >30 min).
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

# Verificar rama y commit.
echo "MVP_BRANCH=$(git branch --show-current)"
echo "MVP_COMMIT=$(git rev-parse HEAD)"

  # La estructura nueva trae 2 raices: router-mvp/ y chat-router/.
  if [ -d router-mvp ]; then
    cd router-mvp
    export PYTHONPATH="$PWD:$PWD/../chat-router${PYTHONPATH:+:$PYTHONPATH}"
  fi

  # Verificar archivos requeridos (funciona con la estructura vieja y la nueva).
  test -f mvp/run.py
  test -f mvp/app.py
  test -f mvp/requirements.txt

  # --- web-bridge en background :7870 ---
  BR="$REPO/chat-router/SWE CODE/web-bridge"; [ -d "$BR" ] || BR="$REPO/router-mvp/SWE CODE/web-bridge"
  echo "BOOT step: bridge"
  if [ -d "$BR" ] && [ -n "${WEB_ACCOUNTS:-}" ] && [ -n "${WEB_PASS:-}" ]; then
    timeout 20 mkdir -p /data/state /tmp/state "$PLAYWRIGHT_BROWSERS_PATH"
    # perfiles Chromium en disco local (el bucket FUSE /data rompe launchPersistentContext);
    # restaurar desde /data/state y sincronizar de vuelta cada 5 min
    : "${WEB_ACCOUNTS:?Falta WEB_ACCOUNTS}"
    : "${WEB_PASS:?Falta WEB_PASS}"
    export WEB_ACCOUNTS WEB_PASS
    echo "WEB_ACCOUNTS_LEN=${#WEB_ACCOUNTS}"   # solo longitud, nunca el valor
    # State FUSE restore NO debe bloquear npm/node del bridge (antes: cp hasta 600s
    # antes de npm -> :7870 muerto -> /web 500 y chat vacio).
    ( echo "STATE restore start"; timeout 600 cp -a /data/state/. /tmp/state/ 2>/dev/null; echo "STATE restore done"
      while sleep 300; do timeout 280 cp -a /tmp/state/. /data/state/ 2>/dev/null || true; done ) 2>&1 | sed -u "s/^/[state] /" &
    ( cd "$BR" && echo "BRIDGE npm start" && npm install --omit=dev --no-audit --no-fund \
        && echo "BRIDGE playwright install" && npx playwright install chromium \
        && echo "BRIDGE node start" \
        && BRIDGE_PORT=7870 BRIDGE_STATE_DIR=/tmp/state exec node src/server.js ) 2>&1 | sed -u "s/^/[bridge] /" &
    echo "BRIDGE started"
  elif [ -d "$BR" ]; then
    echo "WARN: web-bridge omitido: faltan WEB_ACCOUNTS/WEB_PASS (D-86 recuperacion)"
  else
    echo "WARN: web-bridge dir no encontrado"
  fi

  # --- puente-movil :7862 (APK WSS /agente + MCP /mcp) ---
  PM="$REPO/chat-router/SWE CODE free/puente-movil"; [ -d "$PM" ] || PM="$REPO/router-mvp/SWE CODE free/puente-movil"
  if [ -d "$PM" ] && [ -z "${PUENTE_TOKEN:-}" ]; then
    echo "WARN: PUENTE_TOKEN no definido, puente omitido"
  elif [ -d "$PM" ]; then
    ( cd "$PM" && npm install --omit=dev --no-audit --no-fund \
        && PUENTE_PORT=7862 PUENTE_TOKEN="$PUENTE_TOKEN" exec node server.js ) 2>&1 | sed -u "s/^/[puente] /" &
    echo "PUENTE started :7862"
  else
    echo "WARN: puente-movil dir no encontrado"
  fi

  # --- OpenClaw Gateway en background 127.0.0.1:18789 (opcional: OPENCLAW_ENABLE=1) ---
  if [ "${OPENCLAW_ENABLE:-0}" = "1" ]; then
    /openclaw.sh 2>&1 | sed -u "s/^/[openclaw] /" &
    echo "OPENCLAW started"
  fi

  # --- router MVP en :7861 (proxy ocupa 7860) ---
  echo "RUNPY_PORT_LINES:"; grep -nE "PORT|port" mvp/run.py || true
  if grep -qE "environ.*PORT|getenv\(.?.?PORT" mvp/run.py; then
    PORT=7861 RIU_PORT=7861 python -m mvp.run &
  else
    echo "run.py sin PORT env -> uvicorn mvp.app:app :7861"
    python -m uvicorn mvp.app:app --host 127.0.0.1 --port 7861 &
  fi
  ROUTER_PID=$!

  # --- proxy :7860 ---
  echo "BOOT step: proxy :7860"
  cd /
  exec python -m uvicorn proxy:app --host 0.0.0.0 --port 7860 --app-dir /
