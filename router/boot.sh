#!/usr/bin/env bash
set -euo pipefail
mkdir -p /data
git config --global --add safe.directory /tmp/repo
echo "REPO_COMMIT=$(git -C /tmp/repo rev-parse HEAD)"
cd /tmp/repo/router
export PYTHONPATH="/tmp/repo/router:/tmp/repo/router/banco:/tmp/repo"
export RIU_VAULT_PASSPHRASE="${RIU_VAULT_PASSPHRASE:-${RIU_BANK_MASTER:-}}"
exec python /tmp/repo/router/boot_run.py
