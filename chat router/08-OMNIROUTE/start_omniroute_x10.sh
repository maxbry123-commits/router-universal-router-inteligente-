#!/usr/bin/env bash
# Compatibilidad con el antiguo launcher x10.
# 2026-09-28: 9 instancias quedan PAUSADAS. T03 usa una sola instancia estable
# porque OmniRoute/SQLite es single-writer y una instancia ya enruta múltiples
# proveedores/keys. El arranque real vive en start_omniroute.sh.
set -euo pipefail

export OMNIROUTE_INSTANCIAS=1
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "[$(date -u +%FT%TZ)] OmniRoute: 1 instancia activa; 9 pausadas; launcher precompilado"
exec bash "$SCRIPT_DIR/start_omniroute.sh"
