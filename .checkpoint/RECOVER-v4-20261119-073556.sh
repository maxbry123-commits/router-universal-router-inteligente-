#!/usr/bin/env bash
set -e
MODE="${1:-full}"; TAG="checkpoint-yaiwes-chat-v4-20261119-073556"
case "$MODE" in
  full)    git checkout "$TAG";;
  partial) rm -f "ROUTER MVP v1/system_prompt_py/ext_search.py";;
  verify)  cd .checkpoint && sha256sum -c patches/SHA256SUMS-v4 2>/dev/null || true;;
  *)       echo "Uso: $0 {full|partial|verify}"; exit 1;;
esac
