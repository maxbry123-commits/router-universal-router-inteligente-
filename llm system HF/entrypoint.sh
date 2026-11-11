#!/usr/bin/env bash
# entrypoint.sh — Auto-pull + descarga + arranque (Salida 1/3 HF)
# Ubicacion: llm system HF/entrypoint.sh
set -euo pipefail

: "${GITHUB_TOKEN:?Falta GITHUB_TOKEN}"
: "${GITHUB_BRANCH:=main}"
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
exec python3 manager.py
