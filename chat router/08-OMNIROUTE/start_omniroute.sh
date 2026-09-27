#!/usr/bin/env bash
# T03 — Arranque estable de OmniRoute v3.8.50 dentro del Job HF 16 GB del Router.
# Opus copia este script al Router tras revisarlo. Log: /tmp/omniroute.log
set -euo pipefail

LOG=/tmp/omniroute.log
APP_DIR="${OMNIROUTE_APP_DIR:-/tmp/omniroute-app}"
DATA_DIR="${DATA_DIR:-/tmp/omniroute-data}"
TAG="v3.8.50"
NODE_MAJOR=24

log(){ echo "[$(date -u +%FT%TZ)] $*" | tee -a "$LOG"; }
die(){ log "FATAL: $*"; exit 1; }

# --- 0. Clave de cifrado fija (nunca regenerar en cada arranque) ---
if [ -z "${STORAGE_ENCRYPTION_KEY:-}" ]; then
  die "STORAGE_ENCRYPTION_KEY no definida. Exporta una clave fija (p.ej. openssl rand -hex 32) en el entorno del Job."
fi

# --- 1. Node 24 LTS ---
need_node=1
if command -v node >/dev/null 2>&1; then
  v="$(node -v | sed 's/^v//;s/\..*//')"
  [ "$v" = "$NODE_MAJOR" ] && need_node=0
fi
if [ "$need_node" = 1 ]; then
  log "Instalando Node ${NODE_MAJOR}.x LTS…"
  if command -v apt-get >/dev/null 2>&1; then
    curl -fsSL "https://deb.nodesource.com/setup_${NODE_MAJOR}.x" | bash - >>"$LOG" 2>&1 \
      && apt-get install -y nodejs >>"$LOG" 2>&1 \
      || die "No se pudo instalar Node ${NODE_MAJOR} vía nodesource"
  else
    die "No hay apt-get; instala Node ${NODE_MAJOR}.x manualmente"
  fi
fi
node -v | tee -a "$LOG"
node -v | grep -q "^v${NODE_MAJOR}\." || die "Node fuera de rango: $(node -v) (se requiere v${NODE_MAJOR}.x)"

# --- 2. Código v3.8.50 (estable; 3.8.51 es preview) ---
if [ ! -d "$APP_DIR/.git" ]; then
  log "Clonando OmniRoute $TAG en $APP_DIR…"
  git clone --depth 1 --branch "$TAG" \
    https://github.com/diegosouzapw/OmniRoute.git "$APP_DIR" >>"$LOG" 2>&1 \
    || die "git clone $TAG falló"
else
  log "Repo ya presente en $APP_DIR (no se re-clona)"
fi
cd "$APP_DIR"

# --- 3. Dependencias + better-sqlite3 nativo (obligatorio) ---
log "npm ci…"
npm ci >>"$LOG" 2>&1 || die "npm ci falló"
log "npm rebuild better-sqlite3…"
npm rebuild better-sqlite3 >>"$LOG" 2>&1 || true
if ! node -e "require('better-sqlite3')" >>"$LOG" 2>&1; then
  die "better-sqlite3 nativo NO carga. Revisa $LOG. NO se cae a sql.js (cargaría toda la DB en RAM)."
fi
log "better-sqlite3 nativo OK"

# --- 4. Build ---
log "npm run build…"
NODE_OPTIONS=--max-old-space-size=4096 npm run build >>"$LOG" 2>&1 || die "build falló"

# --- 5. Entorno de ejecución ---
mkdir -p "$DATA_DIR" || die "DATA_DIR $DATA_DIR no escribible"
[ -w "$DATA_DIR" ] || die "DATA_DIR $DATA_DIR no escribible"
export DATA_DIR
export APP_BIND_HOST=127.0.0.1
export PORT=20128
export REQUIRE_API_KEY=false
export NODE_OPTIONS=--max-old-space-size=4096
# NO usar modo COMBO (OOM abierto en 3.8.50 al rotar cuentas).

# --- 6. Mantenimiento inicial de la DB (seguro si no existe) ---
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "$SCRIPT_DIR/mantenimiento_db.py" >>"$LOG" 2>&1 || log "WARN: mantenimiento_db falló (no bloqueante)"

# --- 7. Arranque vía supervisor (lock, backoff, healthcheck, límite RAM) ---
log "Lanzando supervisor_omniroute.py…"
exec python3 "$SCRIPT_DIR/supervisor_omniroute.py" >>"$LOG" 2>&1
