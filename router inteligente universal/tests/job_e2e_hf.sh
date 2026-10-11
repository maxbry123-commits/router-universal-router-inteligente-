#!/bin/bash
# Job HF cpu-basic: Router real + job_cierre_total en modo REAL + flujo chat->harness->memoria->HTTP->fichas
set -u
exec 2>&1
B="router inteligente universal"
cd /tmp && rm -rf r && git clone -q --depth 1 --filter=blob:none --sparse "https://github.com/maxbry123-commits/router-universal-router-inteligente-.git" r || { echo CLONE_FAIL; exit 3; }
cd r && git sparse-checkout set --cone "$B/integration" "$B/plugins" "$B/security" "$B/red" "$B/tests" "chat router" "$B/Componente open soure router inteligente universal/graphiti" "$B/Componente open soure router inteligente universal/graphify" >/dev/null 2>&1
ls "$B" | head -20
(apt-get update -qq && apt-get install -y -qq nodejs >/dev/null) 2>&1 | tail -1
pip install -q --break-system-packages -r "$B/requirements.txt" fastapi uvicorn pydantic huggingface_hub cryptography pyyaml requests httpx psutil neo4j 2>&1 | tail -3
export RIU_ROUTER_API_KEY=e2e-$(date +%s) RIU_DATA_DIR=/tmp/riu RIU_GRAPHITI_ENABLE=1 RIU_ROUTER_URL=http://127.0.0.1:8000 RIU_VAULT_PASSPHRASE="${FICHA_CLAVE_BANCO:-}"
export RIU_AGENT_API_KEYS="{\"$RIU_ROUTER_API_KEY\":\"e2e\"}"
mkdir -p $RIU_DATA_DIR
cd "$B"
export PYTHONPATH="$PWD:$PWD/security:$PWD/integration:$PWD/../chat router"
nohup python -m uvicorn integration.chat_mvp.app:app --host 0.0.0.0 --port 8000 > /tmp/app.log 2>&1 &
for i in $(seq 1 60); do python - <<'PY' && break
import socket,sys
s=socket.socket();s.settimeout(1)
try: s.connect(('127.0.0.1',8000))
except Exception: sys.exit(1)
PY
sleep 2; done
echo "--- app.log"; tail -25 /tmp/app.log
H="Authorization: Bearer $RIU_ROUTER_API_KEY"
echo "--- chat real"
curl -s -m 120 -X POST localhost:8000/plugins/puente_chat/call/chat -H "$H" -H 'Content-Type: application/json' -d '{"mensaje":"hola, responde OK","sesion":"e2e1","qwen":true,"modelo":"groq-qwen-3-8"}' | head -c 1500; echo
echo "--- ficha4 llm"
curl -s -m 120 -X POST localhost:8000/plugins/fichas_qwen/call/llm -H "$H" -H 'Content-Type: application/json' -d '{"task_type":"small","prompt":"di OK"}' | head -c 800; echo
echo "--- job_cierre_total REAL"
RIU_FICHA4_URL=http://127.0.0.1:8000/plugins/fichas_qwen/call/llm python tests/job_cierre_total.py
RC=$?
cat job_cierre_total.json 2>/dev/null | head -c 6000
echo; echo "--- app.log final"; tail -12 /tmp/app.log | cut -c1-300
echo "E2E_DONE rc=$RC"
exit $RC
