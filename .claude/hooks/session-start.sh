#!/bin/bash
# Sesiones en la nube: dependencias del Router MVP (router-mvp/mvp/requirements.txt) y de sus pruebas (pytest + httpx para TestClient + pyflakes);
# PYTHONPATH = router-mvp:chat-router (idempotente: una sola definicion en CLAUDE_ENV_FILE y sin duplicar entradas aunque se cargue varias veces).
set -euo pipefail
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi
cd "$CLAUDE_PROJECT_DIR"
python3 -m pip install --quiet -r router-mvp/mvp/requirements.txt pytest httpx pyflakes
if [ -n "${CLAUDE_ENV_FILE:-}" ] && ! grep -qs 'PYTHONPATH.*router-mvp' "$CLAUDE_ENV_FILE"; then
  A="$CLAUDE_PROJECT_DIR/router-mvp"; B="$CLAUDE_PROJECT_DIR/chat-router"
  echo "case \":\${PYTHONPATH:-}:\" in *\":$A:\"*) ;; *) export PYTHONPATH=\"$A:$B\${PYTHONPATH:+:\$PYTHONPATH}\" ;; esac" >> "$CLAUDE_ENV_FILE"
fi
