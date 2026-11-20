#!/usr/bin/env bash
set -e
REPO_URL="https://x-access-token:${GITHUB_TOKEN}@github.com/maxbry123-commits/router-universal-router-inteligente-.git"
BRANCH="${GITHUB_BRANCH:-ccr-f01c3de9-bmry0s}"
TARGET_DIR="/tmp/repo"

if [ -d "$TARGET_DIR/.git" ]; then
    cd "$TARGET_DIR" && git fetch --depth 1 origin "$BRANCH" && git reset --hard "origin/$BRANCH"
else
    git clone --depth 1 --filter=blob:none --sparse --branch "$BRANCH" "$REPO_URL" "$TARGET_DIR"
fi

cd "$TARGET_DIR"
git sparse-checkout set "llm system HF" "ROUTER MVP v1" "external" "router_llm_hf"
cd "$TARGET_DIR/llm system HF"

# PARCHE CRÍTICO: Desactivar reasoning en s3 (Qwen3.5)
if [ -f manager_v2.py ] && ! grep -q '"--reasoning", "off"' manager_v2.py; then
    sed -i 's/"--n-gpu-layers", "0"\]/"--n-gpu-layers", "0", "--reasoning", "off"]/' manager_v2.py
    echo "patch aplicado: llama-server --reasoning off"
fi

pip3 install --break-system-packages -q -r requirements.txt
python3 download_model.py || echo "Aviso: Fallo la descarga, arrancando en modo degradado."
if [ -f manager_v2.py ]; then
    exec python3 manager_v2.py
else
    exec python3 manager.py
fi
