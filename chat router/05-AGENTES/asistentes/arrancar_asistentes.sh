#!/usr/bin/env bash
set -euo pipefail

ROOT="${YAIWES_ASSISTANTS_ROOT:-/tmp/yaiwes-assistants}"
HERMES_REPO="https://github.com/maxbry123-commits/hermes-agent.git"
OPENCLAW_REPO="https://github.com/maxbry123-commits/openclaw.git"
HERMES_REF="${HERMES_REF:-ca16be564d0a95f86bd6da44bb41d39cde9db089}"
OPENCLAW_REF="${OPENCLAW_REF:-038b10b48de03f67c191ec6db15b484aebae8a9c}"
HERMES_DIR="$ROOT/hermes-agent"
OPENCLAW_DIR="$ROOT/openclaw"

export OPENAI_BASE_URL="${OPENAI_BASE_URL:-https://integrate.api.nvidia.com/v1}"
export OPENAI_API_KEY="${OPENAI_API_KEY:-${NVIDIA_API_KEY:-}}"
export YAIWES_ASSISTANT_MODEL="${YAIWES_ASSISTANT_MODEL:-kimi-k3}"

clone_ref() {
  local repo="$1" dir="$2" ref="$3"
  rm -rf "$dir"
  git clone --depth 1 "$repo" "$dir"
  git -C "$dir" fetch --depth 1 origin "$ref"
  git -C "$dir" checkout --detach "$ref"
}

mkdir -p "$ROOT"
clone_ref "$HERMES_REPO" "$HERMES_DIR" "$HERMES_REF"
clone_ref "$OPENCLAW_REPO" "$OPENCLAW_DIR" "$OPENCLAW_REF"

if [[ "${SIMULADO:-0}" == "1" ]]; then
  echo "SIMULADO: asistentes preparados sin instalación ni red de modelos"
  exit 0
fi

python3 -m pip install -e "$HERMES_DIR"
# Contrato Hermes real: hermes gateway / hermes gateway start.
nohup hermes gateway start > /tmp/yaiwes-hermes.log 2>&1 &

corepack enable
(
  cd "$OPENCLAW_DIR"
  pnpm install --frozen-lockfile
  pnpm build
)
# Contrato OpenClaw real: openclaw gateway; desde source usamos su entrypoint.
nohup node "$OPENCLAW_DIR/openclaw.mjs" gateway > /tmp/yaiwes-openclaw.log 2>&1 &

echo "Hermes y OpenClaw iniciados; logs: /tmp/yaiwes-hermes.log /tmp/yaiwes-openclaw.log"
