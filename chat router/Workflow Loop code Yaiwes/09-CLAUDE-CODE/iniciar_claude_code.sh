#!/usr/bin/env bash
# Arranca la pasarela Anthropic->NVIDIA y lanza Claude Code contra ella.
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PUERTO="${PUERTO_PASARELA:-8082}"
export MODELO="${MODELO:-moonshotai/kimi-k2.5}"

# Clave NVIDIA: acepta NVIDIA_API_KEY o NVIDIA_API_KEY_1 (no imprimirla)
if [ -z "${NVIDIA_API_KEY:-}" ] && [ -n "${NVIDIA_API_KEY_1:-}" ]; then
  export NVIDIA_API_KEY="${NVIDIA_API_KEY_1}"
fi
if [ -z "${NVIDIA_API_KEY:-}" ]; then
  echo "ERROR: define NVIDIA_API_KEY (o NVIDIA_API_KEY_1)" >&2
  exit 1
fi

echo "[pasarela] arrancando en 127.0.0.1:${PUERTO} con MODELO=${MODELO}"
python "${DIR}/pasarela.py" &
PID_PASARELA=$!
trap 'kill ${PID_PASARELA} 2>/dev/null || true' EXIT

# Espera a que la pasarela responda
for _ in $(seq 1 30); do
  if curl -sf "http://127.0.0.1:${PUERTO}/" >/dev/null 2>&1; then
    break
  fi
  sleep 0.5
done

export ANTHROPIC_BASE_URL="http://127.0.0.1:${PUERTO}"
export ANTHROPIC_AUTH_TOKEN="${ANTHROPIC_AUTH_TOKEN:-pasarela-local}"
export ANTHROPIC_DEFAULT_OPUS_MODEL="claude-opus-4-1"
export ANTHROPIC_DEFAULT_SONNET_MODEL="claude-sonnet-4-5"
export ANTHROPIC_DEFAULT_HAIKU_MODEL="claude-haiku-4-5"
export CLAUDE_CODE_SUBAGENT_MODEL="claude-sonnet-4-5"

if ! command -v claude >/dev/null 2>&1; then
  echo "ERROR: no se encontró el CLI 'claude' en PATH" >&2
  exit 1
fi

# --bare desactiva plugins (causan 400 en algunos proveedores); si no existe
# la opción en esta versión, se reintenta sin ella.
if claude --help 2>/dev/null | grep -q -- '--bare'; then
  exec claude --bare "$@"
else
  exec claude "$@"
fi
