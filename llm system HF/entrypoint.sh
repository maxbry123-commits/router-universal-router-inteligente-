#!/usr/bin/env bash
set -e

export IDLE_UNLOAD_S="${IDLE_UNLOAD_S:-900}"
export RAM_SCALE_THRESHOLD="${RAM_SCALE_THRESHOLD:-85}"

echo "=== Iniciando Edificio 1 ==="
python3 /app/download_model.py
python3 /app/manager.py
