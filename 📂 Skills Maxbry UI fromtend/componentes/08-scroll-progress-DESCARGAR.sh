#!/usr/bin/env bash
set -euo pipefail

OUT_DIR="${1:-RUI-22-TSX}"
mkdir -p "$OUT_DIR"

URL="https://raw.githubusercontent.com/swamimalode07/rare-ui/1d572f4b1862f5f6b1be61bb33380fede433e1df/components/ui/scroll-progress.tsx"
OUT="$OUT_DIR/scroll-progress.tsx"

echo "Descargando: scroll-progress.tsx"
curl -fL "$URL" -o "$OUT"

if [ ! -s "$OUT" ]; then
  echo "ERROR: archivo vacío o no descargado: $OUT"
  exit 1
fi

echo "OK: $OUT"
