#!/usr/bin/env bash
set -euo pipefail
rm -rf /tmp/repo
git clone --depth 1 -b reorganizacion https://github.com/maxbry123-commits/router-universal-router-inteligente-.git /tmp/repo || git clone --filter=blob:none -b reorganizacion https://github.com/maxbry123-commits/router-universal-router-inteligente-.git /tmp/repo
echo "HEAD=$(git -C /tmp/repo rev-parse HEAD)"
exec bash /tmp/repo/router/boot.sh
