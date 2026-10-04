#!/usr/bin/env bash
# Prueba final en un job de HF (cpu-basic, 16 GB): clona la rama, instala y compila TODOS los motores desde el codigo
# bajado, los levanta y prueba el orquestador (CLI-Anything) de punta a punta. Uso dentro del job: bash prueba_hf.sh
set -u
BR="${BR:-devin/1790824641-chat-agent-plan}"
apt-get update -qq >/dev/null 2>&1; apt-get install -y -qq git nodejs npm >/dev/null 2>&1
git clone -q --depth 1 --branch "$BR" --filter=blob:none --sparse https://github.com/maxbry123-commits/router-universal-router-inteligente-.git /r && cd /r
C='router inteligente universal/Componente open soure router inteligente universal'
DL='router inteligente universal/Componentes del Router/router inteligente software/componentes todos/componentes descargados'
git sparse-checkout set 'chat router/memoria' 'router inteligente universal/integration/chat_mvp' "$C/graphiti" "$C/graphify" "$C/postgres" "$C/redis-py" "$C/haystack" "$C/pydantic-ai/pydantic-ai" "$DL/AgentDB" "$DL/FalkorDB"
echo "== PASO clon: $(git log -1 --format=%h)"
python -m venv /v-graphiti && /v-graphiti/bin/pip -q install "$C/graphiti/code[kuzu]" httpx > /tmp/pip1.log 2>&1; echo "== PASO graphiti: $?"
python -m venv /v-graphify && /v-graphify/bin/pip -q install "$C/graphify/code" > /tmp/pip2.log 2>&1; echo "== PASO graphify: $?"
pip -q install click pytest "$C/redis-py" "$C/haystack" > /tmp/pip3.log 2>&1; echo "== PASO redis-py+haystack: $?"
pip -q install "$C/pydantic-ai/pydantic-ai/pydantic_graph" "$C/pydantic-ai/pydantic-ai/pydantic_ai_slim" > /tmp/pip4.log 2>&1; echo "== PASO pydantic-ai: $? $(tail -1 /tmp/pip4.log | cut -c1-150)"
(cd "$DL/AgentDB" && npm install --no-audit --no-fund --loglevel=error && npm run build:ts) > /tmp/agentdb.log 2>&1; echo "== PASO agentdb: $([ -f "$DL/AgentDB/dist/src/index.js" ] && echo compilado || echo NO)"
bash 'chat router/memoria/motores/compilar_motores.sh' | sed 's/^/== PASO /'
grep -iE 'error|FALLO' /tmp/compilar_motores.log | tail -5 | cut -c1-200
export PY_GRAPHITI=/v-graphiti/bin/python PY_GRAPHIFY=/v-graphify/bin/python PY=python
. 'chat router/memoria/motores/levantar_motores.sh'
sleep 45
export PYTHONPATH='/r/chat router/memoria/agent-harness'
echo '== RESULTADO estado'; python -m cli_anything.memoria --json motores estado
echo '== RESULTADO guardar'; python -m cli_anything.memoria --json memoria guardar prueba:hf nota1 '{"texto": "orquesta en el job de HF"}'
echo '== RESULTADO cargar'; python -m cli_anything.memoria --json memoria cargar prueba:hf nota1
echo '== RESULTADO buscar'; python -m cli_anything.memoria --json memoria buscar prueba:hf orquesta
echo '== RESULTADO toolset'; python -c 'from cli_anything.memoria.core.toolset import crear_toolset; t = crear_toolset(); print(type(t).__name__, sorted(t.tools))' 2>&1 | tail -1
echo '== RESULTADO tests'; (cd 'chat router/memoria/agent-harness' && python -m pytest cli_anything/memoria/tests -q 2>&1 | tail -1)
for f in "${RIU_MOTORES_DIR:-/tmp/riu-motores}"/motor-*.log; do echo "-- $f"; tail -2 "$f" | cut -c1-160; done
echo '== FIN'
