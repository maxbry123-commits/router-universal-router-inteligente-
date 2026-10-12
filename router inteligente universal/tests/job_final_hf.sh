#!/bin/bash
# Job final HF cpu-basic. Secretos por env del job (FICHA_CLAVE_BANCO y RIU_VAULT_PASSPHRASE SEPARADOS). No imprime secretos.
set -u
exec 2>&1
B="router inteligente universal"
cd /tmp && rm -rf r && git clone -q --depth 1 --filter=blob:none --sparse "https://github.com/maxbry123-commits/router-universal-router-inteligente-.git" r || { echo CLONE_FAIL; exit 3; }
cd r && git sparse-checkout set --cone "$B/integration" "$B/plugins" "$B/security" "$B/red" "$B/agent-microkernel" "$B/Banco de claves" "$B/tests" "chat router" "$B/Componente open soure router inteligente universal/graphiti" "$B/Componente open soure router inteligente universal/graphify" || exit 3
(apt-get update -qq && apt-get install -y -qq nodejs >/dev/null) 2>&1 | tail -1
pip install -q --break-system-packages -r "$B/requirements.txt" fastapi uvicorn pydantic huggingface_hub cryptography pyyaml requests httpx psutil neo4j 2>&1 | tail -3
export RIU_DATA_DIR=/data RIU_VAULT_PATH=/data/riu_vault.db RIU_GRAPHITI_ENABLE=1 RIU_CHAT_ALLOW_PROVIDER_LIVE=1 RIU_AUTOSYNC_SECONDS=60 RIU_ROUTER_URL=http://127.0.0.1:8000
mkdir -p /data; cd "$B"
export PYTHONPATH="$PWD:$PWD/security:$PWD/integration:$PWD/../chat router"
python - <<'P2'
import base64,gzip,glob,os
v=os.environ['RIU_VAULT_PATH']
if not os.path.exists(v):
    mk='agent-microkernel'; p=mk+'/runtime-bank.db.gz.b64'
    s=open(p).read().strip() if os.path.exists(p) and open(p).read().strip().startswith('H4sI') else ''.join(open(f).read().strip() for f in sorted(glob.glob(mk+'/runtime-bank-v2.part*')))
    open(v,'wb').write(gzip.decompress(base64.b64decode(s)))
print('BANCO_CIFRADO',os.path.getsize(v))
P2
cat > /tmp/start.sh <<'ES'
cd "/tmp/r/router inteligente universal"
nohup python -m uvicorn integration.chat_mvp.app:app --host 0.0.0.0 --port 8000 > /tmp/app.log 2>&1 &
echo $! > /tmp/uv.pid
for i in $(seq 1 90); do python -c "import socket;s=socket.socket();s.settimeout(1);s.connect(('127.0.0.1',8000))" 2>/dev/null && break; sleep 2; done
ES
bash /tmp/start.sh
python tests/job_final_t.py; rc=$?
echo ---app.log; tail -15 /tmp/app.log | cut -c1-200
echo E2E_DONE rc=$rc
