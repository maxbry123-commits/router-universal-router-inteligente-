#!/usr/bin/env bash
set -euo pipefail
rm -rf /tmp/repo
: "${GITHUB_TOKEN:?GITHUB_TOKEN ausente}"
# Token solo via header efimero (-c): no queda en la URL, .git/config ni logs.
git -c http.https://github.com/.extraheader="Authorization: Basic $(printf 'x-access-token:%s' "$GITHUB_TOKEN" | base64 -w0)" \
  clone --depth 1 -b main https://github.com/maxbry123-commits/router-universal-router-inteligente-.git /tmp/repo
echo "HEAD=$(git -C /tmp/repo rev-parse HEAD)"
cd /tmp/repo
export PYTHONPATH=/tmp/repo  # server.py importa plugins.router_api_cliente
exec python -m uvicorn plugins.deepseek_harness.server:app --host 0.0.0.0 --port 7860
