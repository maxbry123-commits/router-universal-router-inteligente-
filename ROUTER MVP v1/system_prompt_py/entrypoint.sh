#!/usr/bin/env bash
set -e

export IDLE_UNLOAD_S="${IDLE_UNLOAD_S:-900}"
export RAM_SCALE_THRESHOLD="${RAM_SCALE_THRESHOLD:-85}"

python3 scaler_ram.py &
python3 manager.py &

exec uvicorn openai_compatible_proxy:app --host 0.0.0.0 --port 7860
