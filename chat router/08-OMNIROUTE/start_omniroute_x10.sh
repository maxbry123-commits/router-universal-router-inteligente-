#!/usr/bin/env bash
# OmniRoute x10 dentro de la máquina HF 16 GB del Router (orden del Director 2026-09-28).
# Construye UNA vez (misma receta estable de T03: v3.8.50, Node 24, better-sqlite3 nativo) y arranca N instancias:
#   instancia i → PORT = 20128 + 10*i (API_PORT = PORT+1), DATA_DIR propio, memoria máx 1 GB, bucle de reinicio con espera.
# El Router reparte entre las que respondan (omniroute_proxy.py, OMNIROUTE_PORTS). Log: /tmp/omniroute.log y /tmp/omniroute-<i>.log
set -uo pipefail
N="${OMNIROUTE_INSTANCIAS:-10}"
LOG=/tmp/omniroute.log
APP_DIR="${OMNIROUTE_APP_DIR:-/tmp/omniroute-app}"
TAG="v3.8.50"; NODE_MAJOR=24
log(){ echo "[$(date -u +%FT%TZ)] $*" | tee -a "$LOG"; }
die(){ log "FATAL: $*"; exit 1; }

[ -n "${STORAGE_ENCRYPTION_KEY:-}" ] || die "STORAGE_ENCRYPTION_KEY no definida"

if ! node -v 2>/dev/null | grep -q "^v${NODE_MAJOR}\."; then
  log "Instalando Node ${NODE_MAJOR}.x…"
  curl -fsSL "https://deb.nodesource.com/setup_${NODE_MAJOR}.x" | bash - >>"$LOG" 2>&1 && apt-get install -y nodejs >>"$LOG" 2>&1 || die "Node ${NODE_MAJOR} no instalado"
fi
log "node $(node -v)"
[ -d "$APP_DIR/.git" ] || git clone -q --depth 1 --branch "$TAG" https://github.com/diegosouzapw/OmniRoute.git "$APP_DIR" >>"$LOG" 2>&1 || die "clone $TAG"
cd "$APP_DIR"
log "npm ci…"; npm ci >>"$LOG" 2>&1 || die "npm ci"
npm rebuild better-sqlite3 >>"$LOG" 2>&1 || true
node -e "require('better-sqlite3')" >>"$LOG" 2>&1 || die "better-sqlite3 nativo no carga"
log "build…"; NODE_OPTIONS=--max-old-space-size=4096 npm run build >>"$LOG" 2>&1 || die "build"
log "build OK → arrancando $N instancias"

arrancar() {  # $1 = índice
  local i="$1" port=$((20128 + 10 * $1)) data="/tmp/omniroute-data-$1" espera=5
  mkdir -p "$data"
  while true; do
    ( cd "$APP_DIR" && DATA_DIR="$data" PORT="$port" API_PORT=$((port + 1)) APP_BIND_HOST=127.0.0.1 REQUIRE_API_KEY=false \
      NODE_OPTIONS=--max-old-space-size=1024 npm run start >>"/tmp/omniroute-$i.log" 2>&1 )
    echo "[$(date -u +%FT%TZ)] instancia $i (puerto $port) cayó; reinicio en ${espera}s" >>"$LOG"
    for _ in $(seq 1 30); do (echo > /dev/tcp/127.0.0.1/$port) 2>/dev/null || break; sleep 1; done  # esperar puerto libre
    sleep "$espera"; espera=$(( espera < 120 ? espera * 3 : 120 ))
  done
}
for i in $(seq 0 $((N - 1))); do
  arrancar "$i" &
  log "instancia $i lanzada en puerto $((20128 + 10 * i))"
  sleep 15   # arranque escalonado para no saturar CPU/RAM
done
wait
