#!/usr/bin/env bash
set -e
REPO_URL="https://${GITHUB_TOKEN}@github.com/maxbry123-commits/router-universal-router-inteligente-.git"
BRANCH="${GITHUB_BRANCH:-ccr-f01c3de9-bmry0s}"
TARGET_DIR="/tmp/repo"
if [ -d "$TARGET_DIR/.git" ]; then
    cd "$TARGET_DIR" && git fetch origin "$BRANCH" && git reset --hard "origin/$BRANCH"
else
    git clone --depth 1 --branch "$BRANCH" "$REPO_URL" "$TARGET_DIR"
fi
cd "$TARGET_DIR/llm system HF"
pip3 install --break-system-packages -q huggingface_hub
export PYTHONUNBUFFERED=1
python3 download_model.py || echo "Aviso: Fallo la descarga del modelo, arrancando manager en modo degradado."
exec python3 manager.py
