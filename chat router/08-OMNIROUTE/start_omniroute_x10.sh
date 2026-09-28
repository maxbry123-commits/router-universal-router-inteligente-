#!/usr/bin/env bash
# OmniRoute dentro de la máquina HF 16 GB del Router.
# Recuperación OOM 2026-09-28:
# - construir UNA vez con la receta upstream de bajo riesgo;
# - no ejecutar postinstall generales;
# - Webpack en lugar de Turbopack para host limitado;
# - 2 workers de build (CIRCLE_NODE_TOTAL=3);
# - 1 instancia por defecto hasta pasar health/models/chat real.
set -uo pipefail

N="${OMNIROUTE_INSTANCIAS:-1}"
LOG=/tmp/omniroute.log
APP_DIR="${OMNIROUTE_APP_DIR:-/tmp/omniroute-app}"
TAG="v3.8.50"
NODE_MAJOR=24

log(){ echo "[$(date -u +%FT%TZ)] $*" | tee -a "$LOG"; }
die(){ log "FATAL: $*"; exit 1; }
mem(){ if [ -r /sys/fs/cgroup/memory.current ]; then log "RAM cgroup=$(cat /sys/fs/cgroup/memory.current)/$(cat /sys/fs/cgroup/memory.max 2>/dev/null || echo '?')"; fi; }

[ -n "${STORAGE_ENCRYPTION_KEY:-}" ] || die "STORAGE_ENCRYPTION_KEY no definida"

# Build tools requeridos por better-sqlite3.
if ! command -v make >/dev/null 2>&1 || ! command -v g++ >/dev/null 2>&1 || ! command -v python3 >/dev/null 2>&1; then
  log "Instalando build tools…"
  apt-get update -qq >>"$LOG" 2>&1 || true
  DEBIAN_FRONTEND=noninteractive apt-get install -y -qq python3 make g++ ca-certificates curl git >>"$LOG" 2>&1 || die "build tools"
fi

if ! node -v 2>/dev/null | grep -q "^v${NODE_MAJOR}\."; then
  log "Instalando Node ${NODE_MAJOR}.x…"
  curl -fsSL "https://deb.nodesource.com/setup_${NODE_MAJOR}.x" | bash - >>"$LOG" 2>&1 \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y -qq nodejs >>"$LOG" 2>&1 \
    || die "Node ${NODE_MAJOR} no instalado"
fi
log "node $(node -v) · npm $(npm -v)"
mem

if [ ! -d "$APP_DIR/.git" ]; then
  git clone -q --depth 1 --branch "$TAG" https://github.com/diegosouzapw/OmniRoute.git "$APP_DIR" >>"$LOG" 2>&1 || die "clone $TAG"
fi
cd "$APP_DIR"

# Fail-closed: el checkout debe ser exactamente el tag esperado.
git describe --tags --exact-match 2>/dev/null | grep -qx "$TAG" || die "checkout no está en $TAG"

# Receta equivalente a la usada por el Dockerfile upstream:
# instala dependencias de forma reproducible, pero bloquea postinstall generales
# (Playwright/Chromium, ONNX Runtime, etc.) que disparaban el pico de RAM.
export NPM_CONFIG_LEGACY_PEER_DEPS=true
export PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1
export PUPPETEER_SKIP_DOWNLOAD=true
export npm_config_audit=false
export npm_config_fund=false
export npm_config_foreground_scripts=false

log "reparando lockfile incompleto del tag sin instalar paquetes…"
npm install --package-lock-only --ignore-scripts --legacy-peer-deps --no-audit --no-fund >>"$LOG" 2>&1 \
  || die "package-lock repair"
log "npm ci upstream-safe (--ignore-scripts)…"
npm ci --include=optional --no-audit --no-fund --legacy-peer-deps --ignore-scripts >>"$LOG" 2>&1 \
  || die "npm ci upstream-safe"
mem

# better-sqlite3 es el binding nativo obligatorio. No aceptar sql.js como fallback.
log "reconstruyendo better-sqlite3 nativo…"
if [ -x node_modules/.bin/node-gyp ]; then
  ( cd node_modules/better-sqlite3 && ../.bin/node-gyp rebuild ) >>"$LOG" 2>&1 \
    || die "node-gyp better-sqlite3"
else
  npm rebuild better-sqlite3 --foreground-scripts >>"$LOG" 2>&1 \
    || die "npm rebuild better-sqlite3"
fi
node -e "const DB=require('better-sqlite3'); const db=new DB(':memory:'); db.close(); console.log('BETTER_SQLITE3=PASS')" >>"$LOG" 2>&1 \
  || die "better-sqlite3 nativo no carga"

# tls-client-node: mismo tratamiento selectivo que upstream. Si el paquete no lo
# necesita/trae, no bloquear; si existe y su script falla, registrar y continuar
# porque la prueba objetivo usa proveedores no-auth que no requieren impersonación.
if [ -f node_modules/tls-client-node/scripts/postinstall.js ]; then
  log "preparando tls-client-node…"
  node node_modules/tls-client-node/scripts/postinstall.js >>"$LOG" 2>&1 \
    || log "WARN tls-client-node postinstall falló; proveedores web/TLS pueden quedar no disponibles"
fi

# Liberar cache npm antes del build. La RAM del cgroup es el recurso crítico.
npm cache clean --force >>"$LOG" 2>&1 || true
rm -rf /root/.npm/_cacache 2>/dev/null || true
mem

# Upstream documenta que Turbopack usa memoria nativa fuera del heap V8.
# En 16 GB usamos Webpack + 2 workers y heap de build 6 GB.
export NEXT_TELEMETRY_DISABLED=1
export OMNIROUTE_USE_TURBOPACK=0
export CIRCLE_NODE_TOTAL=3
export NODE_OPTIONS=--max-old-space-size=6144

log "build Webpack limitado…"
npm run build >>"$LOG" 2>&1 || die "build Webpack"
log "build OK"
mem

# Runtime: volver al techo pequeño. Una instancia por defecto; escalar solo tras PASS.
unset OMNIROUTE_USE_TURBOPACK CIRCLE_NODE_TOTAL
export NODE_OPTIONS=--max-old-space-size=1024
log "arrancando $N instancia(s)"

arrancar() {
  local i="$1" port=$((20128 + 10 * $1)) data="/tmp/omniroute-data-$1" espera=5
  mkdir -p "$data"
  while true; do
    (
      cd "$APP_DIR"
      DATA_DIR="$data" \
      PORT="$port" \
      API_PORT=$((port + 1)) \
      APP_BIND_HOST=127.0.0.1 \
      REQUIRE_API_KEY=false \
      NODE_OPTIONS=--max-old-space-size=1024 \
      npm run start >>"/tmp/omniroute-$i.log" 2>&1
    )
    rc=$?
    echo "[$(date -u +%FT%TZ)] instancia $i (puerto $port) cayó rc=$rc; reinicio en ${espera}s: $(tail -c 500 /tmp/omniroute-$i.log | tr '\n' ' ')" >>"$LOG"
    for _ in $(seq 1 30); do
      (echo > /dev/tcp/127.0.0.1/$port) 2>/dev/null || break
      sleep 1
    done
    sleep "$espera"
    espera=$(( espera < 120 ? espera * 3 : 120 ))
  done
}

for i in $(seq 0 $((N - 1))); do
  arrancar "$i" &
  log "instancia $i lanzada en puerto $((20128 + 10 * i))"
  sleep 15
done

wait