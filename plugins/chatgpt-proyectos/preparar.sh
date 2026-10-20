#!/usr/bin/env bash
# Descarga el kit oficial de OpenAI y compila solo @siwc/local (no se copia el kit al repo).
set -euo pipefail
cd "$(dirname "$0")"
rm -rf .kit && git clone -q --depth 1 https://github.com/openai/sign-in-with-chatgpt-devkit .kit
(cd .kit && npm ci --silent && npm run build --workspace @siwc/local --silent)
mkdir -p node_modules/@siwc && rm -rf node_modules/@siwc/local && cp -r .kit/packages/local node_modules/@siwc/local
(cd node_modules/@siwc/local && npm install --omit=dev --silent)
