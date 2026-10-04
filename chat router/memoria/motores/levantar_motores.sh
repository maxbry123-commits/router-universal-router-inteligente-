#!/usr/bin/env bash
# Levanta los motores de memoria (servicios HTTP con el contrato de ComponentAdapter) y exporta sus URL.
# Uso: . 'chat router/memoria/motores/levantar_motores.sh'  (con source). Interpretes configurables por variable.
RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
M="$RAIZ/chat router/memoria/motores"
DATOS="${RIU_MOTORES_DIR:-/tmp/riu-motores}"; mkdir -p "$DATOS"
PY_GRAPHITI="${PY_GRAPHITI:-/tmp/v-graphiti/bin/python}"; PY_GRAPHIFY="${PY_GRAPHIFY:-/tmp/v-graphify/bin/python}"; PY="${PY:-python3}"
AGENTDB="$RAIZ/router inteligente universal/Componentes del Router/router inteligente software/componentes todos/componentes descargados/AgentDB/dist/src/index.js"
libre() { ! (echo > "/dev/tcp/127.0.0.1/$1") 2>/dev/null; }
arrancar() { local puerto="$1"; shift; if libre "$puerto"; then nohup "$@" > "$DATOS/motor-$puerto.log" 2>&1 & echo "motor :$puerto arrancado"; else echo "motor :$puerto ya estaba"; fi; }
arrancar 9101 "$PY_GRAPHITI" "$M/graphiti_sidecar.py" --port 9101 --db "$DATOS/graphiti.kuzu"
arrancar 9103 "$PY_GRAPHIFY" "$M/graphify_sidecar.py" --port 9103 --corpus "$RAIZ/chat router/memoria" "$RAIZ/router inteligente universal/integration/chat_mvp"
arrancar 9104 node "$M/agentdb_sidecar.mjs" --port 9104 --dist "$AGENTDB" --db "$DATOS/agentdb.sqlite"
export RIU_GRAPHITI_URL=http://127.0.0.1:9101 RIU_GRAPHIFY_URL=http://127.0.0.1:9103 RIU_AGENTDB_URL=http://127.0.0.1:9104
if ! libre 6390; then arrancar 9105 "$PY" "$M/falkordb_sidecar.py" --port 9105 --redis redis://127.0.0.1:6390; export RIU_FALKORDB_HTTP_URL=http://127.0.0.1:9105; fi
if [ -x /opt/pg/bin/psql ] && ! libre 5433; then arrancar 9106 "$PY" "$M/postgres_sidecar.py" --port 9106 --psql /opt/pg/bin/psql --dsn 'host=127.0.0.1 port=5433 user=memoria dbname=memoria'; export RIU_POSTGRESQL_HTTP_URL=http://127.0.0.1:9106; fi
