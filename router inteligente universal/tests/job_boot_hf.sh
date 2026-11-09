#!/bin/bash
# Job HF cpu-basic: Router real + job_cierre_total en modo REAL + flujo chat->harness->memoria->HTTP->fichas
set -u
exec 2>&1
B="router inteligente universal"
cd /tmp && rm -rf r && git clone -q --depth 1 --filter=blob:none --sparse "https://github.com/maxbry123-commits/router-universal-router-inteligente-.git" r || { echo CLONE_FAIL; exit 3; }
cd r && git sparse-checkout set --cone "$B/integration" "$B/plugins" "$B/security" "$B/red" "$B/agent-microkernel" "$B/Banco de claves" "$B/tests" "chat router" "$B/Componente open soure router inteligente universal/graphiti" "$B/Componente open soure router inteligente universal/graphify" >/dev/null 2>&1
ls "$B" | head -20
(apt-get update -qq && apt-get install -y -qq nodejs >/dev/null) 2>&1 | tail -1
pip install -q --break-system-packages -r "$B/requirements.txt" fastapi uvicorn pydantic huggingface_hub cryptography pyyaml requests httpx psutil neo4j 2>&1 | tail -3
export RIU_ROUTER_API_KEY=e2e-$(date +%s) RIU_DATA_DIR=/tmp/riu RIU_GRAPHITI_ENABLE=1 RIU_ROUTER_URL=http://127.0.0.1:8000
export RIU_AGENT_API_KEYS="{\"$RIU_ROUTER_API_KEY\":\"e2e\"}"
mkdir -p $RIU_DATA_DIR
cd "$B"
export PYTHONPATH="$PWD:$PWD/security:$PWD/integration:$PWD/../chat router"
export RIU_VAULT_PATH=/tmp/riu_vault.db RIU_CHAT_ALLOW_PROVIDER_LIVE=1
python - <<'P2'
import base64,gzip,glob,os
mk='agent-microkernel'
p=mk+'/runtime-bank.db.gz.b64'
if os.path.exists(p) and open(p).read().strip().startswith('H4sI'): s=open(p).read().strip()
else: s=''.join(open(f).read().strip() for f in sorted(glob.glob(mk+'/runtime-bank-v2.part*')))
open(os.environ['RIU_VAULT_PATH'],'wb').write(gzip.decompress(base64.b64decode(s))); print('BANCO_CIFRADO_ESCRITO',os.path.getsize(os.environ['RIU_VAULT_PATH']))
P2
nohup python -m uvicorn integration.chat_mvp.app:app --host 0.0.0.0 --port 8000 > /tmp/app.log 2>&1 &
for i in $(seq 1 60); do python - <<'PY' && break
import socket,sys
s=socket.socket();s.settimeout(1)
try: s.connect(('127.0.0.1',8000))
except Exception: sys.exit(1)
PY
sleep 2; done
export RIU_URL=http://127.0.0.1:8000
H="Authorization: Bearer $RIU_ROUTER_API_KEY"
echo "--- vault/status"
curl -s -m 20 localhost:8000/vault/status -H "$H" | python -c "import sys,json;d=json.load(sys.stdin);print({'exists':d.get('exists'),'unlocked':d.get('unlocked'),'credentials':len(d.get('credentials') or [])})"
python /tmp/t.py $TEST_ARGS
RC=$?
echo "--- app.log"; tail -12 /tmp/app.log | cut -c1-250
echo "E2E_DONE rc=$RC"
exit $RC
