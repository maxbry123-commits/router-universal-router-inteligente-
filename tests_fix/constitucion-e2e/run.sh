#!/bin/sh
# E2E Android simulado (412 px, 4G) de la Constitucion sentinela: frontend real + plugins reales, modelo simulado en la frontera del Harness.
# Requisitos: python con fastapi/pydantic/cryptography/networkx/tree-sitter (requirements.txt), node + playwright-core, Chrome en CHROME (por defecto /usr/bin/google-chrome).
# Uso: sh tests_fix/constitucion-e2e/run.sh   (no toca produccion: todo lo externo se bloquea)
set -e
cd "$(dirname "$0")"; WT="$(cd ../.. && pwd)"; PY="${PY:-python3}"
PORT=$($PY -c "import socket;s=socket.socket();s.bind(('127.0.0.1',0));print(s.getsockname()[1])"); echo "$PORT" > port.txt; rm -f sim.log
DATA=$(mktemp -d); PYTHONDONTWRITEBYTECODE=1 RIU_DATA_DIR="$DATA" $PY sim_router.py "$WT" "$PORT" "$PWD/sim.log" > sim_server.out 2>&1 & SIM=$!
trap 'kill $SIM 2>/dev/null; rm -rf "$DATA"' EXIT; sleep 2
node e2e.mjs
