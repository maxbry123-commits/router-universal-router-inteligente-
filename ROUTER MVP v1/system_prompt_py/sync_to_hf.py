import os
from huggingface_hub import HfApi

api = HfApi(token=os.getenv("HF_TOKEN"))
repo_id = "COMAND-CENTER-1/riu-router"

try:
    api.upload_folder(
        folder_path=".",
        repo_id=repo_id,
        repo_type="space",
        ignore_patterns=["*.pyc", "__pycache__", ".git", ".checkpoints", "*.db"]
    )
    print("SYNC_OK")
except Exception as e:
    print(f"SYNC_FAIL: {e}")
