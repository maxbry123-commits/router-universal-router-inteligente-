#!/usr/bin/env bash
# Levanta los motores de memoria (servicios HTTP con el contrato de ComponentAdapter) y exporta RIU_<MOTOR>_URL.
# Uso: . 'chat router/memoria/motores/levantar_motores.sh'   (con source, para llevar las variables a tu shell)
# Requiere (entorno de pruebas): /tmp/v-graphiti (graphiti-core[kuzu]), /tmp/v-graphify (graphifyy) y AgentDB compilado (npm run build:ts).
RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
M="$RAIZ/chat router/memoria/motores"
DATOS="${RIU_MOTORES_DIR:-/tmp/riu-motores}"; mkdir -p "$DATOS"
AGENTDB="$RAIZ/router inteligente universal/Componentes del Router/router inteligente software/componentes todos/componentes descargados/AgentDB/dist/src/index.js"
libre() { ! (echo > "/dev/tcp/127.0.0.1/$1") 2>/dev/null; }
arrancar() { local puerto="$1"; shift; if libre "$puerto"; then nohup "$@" > "$DATOS/motor-$puerto.log" 2>&1 & echo "motor :$puerto arrancado"; else echo "motor :$puerto ya estaba"; fi; }
arrancar 9101 /tmp/v-graphiti/bin/python "$M/graphiti_sidecar.py" --port 9101 --db "$DATOS/graphiti.kuzu"
arrancar 9103 /tmp/v-graphify/bin/python "$M/graphify_sidecar.py" --port 9103 --corpus "$RAIZ/chat router/memoria" "$RAIZ/router inteligente universal/integration/chat_mvp"
arrancar 9104 node "$M/agentdb_sidecar.mjs" --port 9104 --dist "$AGENTDB" --db "$DATOS/agentdb.sqlite"
export RIU_GRAPHITI_URL=http://127.0.0.1:9101 RIU_GRAPHIFY_URL=http://127.0.0.1:9103 RIU_AGENTDB_URL=http://127.0.0.1:9104
