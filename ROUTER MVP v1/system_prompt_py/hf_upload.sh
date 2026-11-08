#!/usr/bin/env bash
set -e

if [ -z "$HF_TOKEN" ]; then
    echo "Error: HF_TOKEN no esta configurado."
    exit 1
fi

SPACE_ID="COMAND-CENTER-1/riu-router"
FOLDER="ROUTER MVP v1/system_prompt_py"

echo "Subiendo codigo a $SPACE_ID..."
python3 -c "
from huggingface_hub import HfApi
import os
api = HfApi(token=os.getenv('HF_TOKEN'))
api.upload_folder(
    folder_path='$FOLDER',
    repo_id='$SPACE_ID',
    repo_type='space',
    ignore_patterns=['*.pyc', '__pycache__', '.checkpoints', '*.db']
)
print('Subida completada.')
"
