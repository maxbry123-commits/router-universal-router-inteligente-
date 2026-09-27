#!/usr/bin/env bash
# Arranca OmniRoute oficial (v3.8.51) DENTRO de la máquina HF 16 GB del Router, en segundo plano.
# El Router lo alcanza en http://127.0.0.1:20128 (ruta /omniroute/* del Router). Sin UI para nosotros.
# Datos en /tmp/omniroute-data (se reconfigura al relanzar; las claves de proveedores van como secretos).
set -u
LOG=/tmp/omniroute.log
{
  echo "[omniroute] instalando Node 20..."
  if ! command -v node >/dev/null || ! node -v | grep -qE '^v(2[0-9])'; then
    apt-get update -qq >/dev/null 2>&1
    apt-get install -y -qq curl ca-certificates >/dev/null 2>&1
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - >/dev/null 2>&1
    apt-get install -y -qq nodejs >/dev/null 2>&1
  fi
  echo "[omniroute] node $(node -v)"
  rm -rf /tmp/omniroute && git clone -q --depth 1 --branch release/v3.8.51 https://github.com/diegosouzapw/OmniRoute.git /tmp/omniroute
  cd /tmp/omniroute
  export DATA_DIR=/tmp/omniroute-data PORT=20128 APP_BIND_HOST=127.0.0.1 REQUIRE_API_KEY=true OMNIROUTE_MEMORY_MB=4096 NODE_OPTIONS=--max-old-space-size=4096
  export INITIAL_PASSWORD="${RIU_ROUTER_API_KEY:-${GITHUB_TOKEN:0:24}}"
  mkdir -p "$DATA_DIR"
  echo "[omniroute] npm ci + build (tarda varios minutos)..."
  npm ci --no-audit --no-fund >/dev/null 2>&1 && npm run build >/dev/null 2>&1 || { echo "[omniroute] BUILD_FALLO"; exit 1; }
  echo "[omniroute] arrancando en 127.0.0.1:20128"
  exec npm run start
} >>"$LOG" 2>&1
