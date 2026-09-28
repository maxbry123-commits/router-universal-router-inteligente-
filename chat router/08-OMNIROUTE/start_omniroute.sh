#!/usr/bin/env bash
# T03 — OmniRoute v3.8.50 estable en HF cpu-basic 16 GB.
# Recuperación 2026-09-28: usar el bundle npm oficial PRECOMPILADO.
# No clonar ni compilar Next.js dentro del Job: ese build agotaba los 16 GB.
set -euo pipefail

LOG=/tmp/omniroute.log
DATA_DIR="${DATA_DIR:-/tmp/omniroute-data}"
OMNIROUTE_VERSION="3.8.50"
NODE_MAJOR=24
RUNTIME_DIR="${HOME:-/root}/.omniroute/runtime"

log(){ echo "[$(date -u +%FT%TZ)] $*" | tee -a "$LOG"; }
die(){ log "FATAL: $*"; exit 1; }

# 0. Clave fija: nunca regenerarla en cada arranque.
[ -n "${STORAGE_ENCRYPTION_KEY:-}" ] \
  || die "STORAGE_ENCRYPTION_KEY no definida"

# 1. Dependencias mínimas del host.
if ! command -v curl >/dev/null 2>&1 || ! command -v python3 >/dev/null 2>&1; then
  apt-get update -qq >>"$LOG" 2>&1 || true
  DEBIAN_FRONTEND=noninteractive apt-get install -y -qq curl ca-certificates python3 >>"$LOG" 2>&1 \
    || die "dependencias base"
fi

# 2. Node 24.
if ! command -v node >/dev/null 2>&1 || ! node -v | grep -q "^v${NODE_MAJOR}\."; then
  log "Instalando Node ${NODE_MAJOR}.x…"
  curl -fsSL "https://deb.nodesource.com/setup_${NODE_MAJOR}.x" | bash - >>"$LOG" 2>&1 \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y -qq nodejs >>"$LOG" 2>&1 \
    || die "Node ${NODE_MAJOR}"
fi
node -v | grep -q "^v${NODE_MAJOR}\." || die "Node incompatible: $(node -v)"
log "Node $(node -v) · npm $(npm -v)"

# 3. Bundle npm oficial. El paquete publicado ya contiene dist/server.js.
# --omit=optional evita ONNX/Transformers/Playwright pesados.
# --ignore-scripts evita postinstall transitorios; SQLite se instala de forma
# selectiva y verificable en el paso 4.
installed=""
if command -v omniroute >/dev/null 2>&1; then
  installed="$(omniroute --version 2>/dev/null | tail -1 | tr -d '\r' || true)"
fi
if [ "$installed" != "$OMNIROUTE_VERSION" ]; then
  log "Instalando bundle precompilado omniroute@${OMNIROUTE_VERSION}…"
  OMNIROUTE_SKIP_POSTINSTALL=1 \
    npm install -g "omniroute@${OMNIROUTE_VERSION}" \
      --omit=optional --ignore-scripts --no-audit --no-fund >>"$LOG" 2>&1 \
    || die "npm global install OmniRoute"
fi
installed="$(omniroute --version 2>/dev/null | tail -1 | tr -d '\r' || true)"
[ "$installed" = "$OMNIROUTE_VERSION" ] \
  || die "versión inesperada: '$installed' != '$OMNIROUTE_VERSION'"
log "OmniRoute $installed precompilado OK"

# 4. better-sqlite3 nativo en la ruta oficial de runtime.
mkdir -p "$RUNTIME_DIR"
if [ ! -f "$RUNTIME_DIR/package.json" ]; then
  printf '%s\n' '{"name":"omniroute-runtime","private":true,"type":"commonjs"}' \
    >"$RUNTIME_DIR/package.json"
fi

if ! RUNTIME_DIR="$RUNTIME_DIR" node - <<'NODE' >>"$LOG" 2>&1
const path = require("node:path");
const root = process.env.RUNTIME_DIR;
try {
  const DB = require(path.join(root, "node_modules", "better-sqlite3"));
  const db = new DB(":memory:");
  db.exec("CREATE TABLE IF NOT EXISTS probe(x INTEGER)");
  db.close();
  process.exit(0);
} catch {
  process.exit(1);
}
NODE
then
  log "Instalando better-sqlite3 nativo en runtime…"
  npm install --prefix "$RUNTIME_DIR" 'better-sqlite3@^13.0.2' \
    --no-audit --no-fund --silent >>"$LOG" 2>&1 \
    || die "better-sqlite3 runtime install"
fi

RUNTIME_DIR="$RUNTIME_DIR" node - <<'NODE' >>"$LOG" 2>&1 || exit 41
const path = require("node:path");
const DB = require(path.join(process.env.RUNTIME_DIR, "node_modules", "better-sqlite3"));
const db = new DB(":memory:");
db.exec("CREATE TABLE probe(x INTEGER)");
db.close();
console.log("BETTER_SQLITE3=PASS");
NODE
[ "$?" -eq 0 ] || die "better-sqlite3 nativo no carga"
log "better-sqlite3 nativo OK"

# 5. Entorno local-only.
mkdir -p "$DATA_DIR" "${HOME:-/root}/.cache"
[ -w "$DATA_DIR" ] || die "DATA_DIR no escribible: $DATA_DIR"
export DATA_DIR
export APP_BIND_HOST=127.0.0.1
export OMNIROUTE_SERVER_HOST=127.0.0.1
export PORT=20128
export API_PORT=20128
export REQUIRE_API_KEY=false
export NODE_OPTIONS=--max-old-space-size=4096
export OMNIROUTE_MEMORY_MB=4096

# 6. Retención/mmap/VACUUM antes de arrancar.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "$SCRIPT_DIR/mantenimiento_db.py" >>"$LOG" 2>&1 \
  || log "WARN: mantenimiento_db falló (no bloqueante)"

# 7. Supervisor T03: lock, backoff, healthcheck, puerto y límite RAM.
log "Lanzando supervisor T03 sobre bundle npm precompilado…"
exec python3 "$SCRIPT_DIR/supervisor_omniroute.py" >>"$LOG" 2>&1
