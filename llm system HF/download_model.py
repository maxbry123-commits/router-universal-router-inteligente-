import os
from huggingface_hub import hf_hub_download

def download():
    model_id = os.getenv("MODEL_ID", "Qwen/Qwen2.5-Coder-0.5B-Instruct-GGUF")
    filename = os.getenv("MODEL_FILE", "qwen2.5-coder-0.5b-instruct-q5_k_m.gguf")
    target_dir = "/data/models"

    os.makedirs(target_dir, exist_ok=True)
    path = hf_hub_download(repo_id=model_id, filename=filename, local_dir=target_dir)
    print(f"MODEL_DOWNLOADED: {path}")

if __name__ == "__main__":
    download()
