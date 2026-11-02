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
  if [ -d "$BR" ]; then
    : "${PLAYWRIGHT_BROWSERS_PATH:=/tmp/ms-playwright}"
    export PLAYWRIGHT_BROWSERS_PATH
    mkdir -p /data/state /tmp/state "$PLAYWRIGHT_BROWSERS_PATH"
    # perfiles Chromium en disco local (el bucket FUSE /data rompe launchPersistentContext);
    # restaurar desde /data/state y sincronizar de vuelta cada 5 min
    cp -a /data/state/. /tmp/state/ 2>/dev/null || true
    ( while sleep 300; do cp -a /tmp/state/. /data/state/ 2>/dev/null || true; done ) &
    # El navegador Qwen/DeepSeek es opcional; API NVIDIA/Groq/DeepSeek/MiniMax/OpenAI
    # y modelos locales NO requieren cuentas web. Ausencia no debe matar todo el Space.
    export WEB_ACCOUNTS="${WEB_ACCOUNTS:-}" WEB_PASS="${WEB_PASS:-}"
    if [ -z "$WEB_ACCOUNTS" ] || [ -z "$WEB_PASS" ]; then
      echo "WEB_CUENTAS_OPCIONALES: web sin credenciales; API y HF disponibles"
    else
      echo "WEB_ACCOUNTS_LEN=${#WEB_ACCOUNTS}"  # nunca registrar las claves
    fi
    # Primero el proceso de API; Chromium se instala en paralelo y se usa solo
    # al pedir una sesion de navegador. Evita retrasar API/HF por downloads del browser.
    (
      cd "$BR"
      npm install --omit=dev --no-audit --no-fund
      BRIDGE_PORT=7870 BRIDGE_STATE_DIR=/tmp/state exec node src/server.js
    ) 2>&1 | sed -u "s/^/[bridge] /" &
    (
      cd "$BR"
      # Version de Playwright del package.json ya instalada por npm (no npx remoto).
      for i in $(seq 1 60); do
        if [ -f node_modules/playwright/cli.js ]; then
          node node_modules/playwright/cli.js install chromium || echo "WARN: navegador no instalado (API no afectadas)"
          exit 0
        fi
        sleep 1
      done
      echo "WARN: playwright no instalado: el bridge puede seguir sirviendo APIs"
    ) 2>&1 | sed -u "s/^/[browser-setup] /" &
    echo "BRIDGE started"
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
  cd /
  exec python -m uvicorn proxy:app --host 0.0.0.0 --port 7860 --app-dir /
