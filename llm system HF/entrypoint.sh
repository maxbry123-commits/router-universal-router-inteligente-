#!/usr/bin/env bash
# entrypoint.sh v2 — Auto-pull + descarga + arranque con manager_v2 (cierre-hf P1)
set -euo pipefail

: "${GITHUB_TOKEN:?Falta GITHUB_TOKEN}"
: "${GITHUB_BRANCH:=ccr-f01c3de9-bmry0s}"
: "${ROUTER_API_KEY:?Falta ROUTER_API_KEY}"

REPO_URL="https://x-access-token:${GITHUB_TOKEN}@github.com/maxbry123-commits/router-universal-router-inteligente-.git"
APP_DIR="/app"

if [ -d "$APP_DIR/.git" ]; then
  git -C "$APP_DIR" fetch origin "$GITHUB_BRANCH"
  git -C "$APP_DIR" reset --hard "origin/$GITHUB_BRANCH"
else
  git clone --depth 1 --branch "$GITHUB_BRANCH" "$REPO_URL" "$APP_DIR"
fi

cd "$APP_DIR/llm system HF"
python3 download_model.py

# Preferir manager_v2.py (idle unload 15 min); fallback a manager.py
if [ -f manager_v2.py ]; then
  exec python3 manager_v2.py
else
  exec python3 manager.py
fi
