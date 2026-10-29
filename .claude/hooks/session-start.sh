#!/bin/bash
# Sesiones en la nube: dependencias del Router MVP (mvp/requirements.txt) y de sus pruebas (pytest + httpx para TestClient).
set -euo pipefail
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi
cd "$CLAUDE_PROJECT_DIR"
python3 -m pip install --quiet -r mvp/requirements.txt pytest httpx pyflakes
echo 'export PYTHONPATH="'"$CLAUDE_PROJECT_DIR"'${PYTHONPATH:+:$PYTHONPATH}"' >> "$CLAUDE_ENV_FILE"
