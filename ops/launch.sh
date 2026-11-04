#!/usr/bin/env bash
# ops/launch.sh — lanzador único de los Jobs del kernel (R1 clone con --branch, R5 clona para cada job, R6 --timeout).
# improved_over_minimax: token solo en cabecera de entorno (nunca URL/argv/logs); un clon por job (idempotente); python <path> en vez de exec(open()).
set -euo pipefail
JOB="${1:?uso: launch.sh <job_id> [script]}"
SCRIPT="${2:-$JOB}"
: "${GH_REPO:?}"; : "${GH_BRANCH:?}"; : "${RUN_ID:?clave de idempotencia}"
export DATASET_REPO="${DATASET_REPO:-COMAND-CENTER-1/router-universal-router-inteligente-auditoria}"
export JOB_NAME="$JOB"
# D-17: todo Job de Hugging Face se crea con 32 GB RAM + CPU (flavor=cpu-upgrade) via ops/hf_job.py
export HF_FLAVOR="${HF_FLAVOR:-cpu-upgrade}"
if [ -n "${GH_TOKEN:-}" ]; then
  B=$(printf 'x-access-token:%s' "$GH_TOKEN" | base64 | tr -d '\n')
  export GIT_CONFIG_COUNT=1
  export GIT_CONFIG_KEY_0="http.https://github.com/.extraheader"
  export GIT_CONFIG_VALUE_0="AUTHORIZATION: basic $B"
  export GIT_TERMINAL_PROMPT=0
fi
SRC="$PWD"
if [ ! -f "ops/$SCRIPT.py" ]; then          # R5: el script se obtiene SIEMPRE del repo
  WORK="${WORK:-/tmp/kernel-$RUN_ID}"
  rm -rf "$WORK"; mkdir -p "$WORK"
  git clone --filter=tree:0 --depth 1 --sparse --branch "$GH_BRANCH" "https://github.com/$GH_REPO.git" "$WORK/repo"
  git -C "$WORK/repo" sparse-checkout set ops kernel connections
  SRC="$WORK/repo"
fi
cd "$SRC"
export PYTHONPATH="$SRC/ops"
# D-11: los scripts de la guia importan yaml; su comando solo instalaba huggingface_hub.
PY="${PYTHON:-python3}"
$PY -c "import yaml, huggingface_hub" >/dev/null 2>&1 || pip install -q huggingface_hub pyyaml
exec $PY "ops/$SCRIPT.py"
