#!/usr/bin/env bash
set -euo pipefail
DEST="${1:-RARE-UI-ORIGINAL}"
REPO="https://github.com/swamimalode07/rare-ui.git"
COMMIT="1d572f4b1862f5f6b1be61bb33380fede433e1df"

if [ -e "$DEST" ]; then
  echo "ERROR: ya existe $DEST"
  exit 1
fi

git clone "$REPO" "$DEST"
cd "$DEST"
git checkout "$COMMIT"

echo "DESCARGADO: $DEST"
echo "COMMIT: $(git rev-parse HEAD)"
echo "COMPONENTES: components/ui"
