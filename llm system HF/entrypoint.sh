#!/usr/bin/env bash
set -euo pipefail

: "${GITHUB_BRANCH:=ccr-f01c3de9-bmry0s}"
: "${GITHUB_TOKEN:?GITHUB_TOKEN requerido}"
: "${GITHUB_REPO:=maxbry123-commits/router-universal-router-inteligente-}"
: "${MODEL_ID:?MODEL_ID requerido}"
: "${MODEL_FILE:?MODEL_FILE requerido}"

REPO_URL="https://${GITHUB_TOKEN}@github.com/${GITHUB_REPO}.git"
TARGET_DIR="/tmp/repo"

echo "[entrypoint] branch=${GITHUB_BRANCH} model=${MODEL_ID}"

if [ -d "${TARGET_DIR}/.git" ]; then
  cd "${TARGET_DIR}"
  git fetch origin "${GITHUB_BRANCH}"
  git reset --hard "origin/${GITHUB_BRANCH}"
else
  git clone --depth 1 --branch "${GITHUB_BRANCH}" "${REPO_URL}" "${TARGET_DIR}"
fi

cd "${TARGET_DIR}/llm system HF"
python3 download_model.py || { echo "[entrypoint] FALLO descarga modelo"; exit 1; }

exec python3 manager.py
