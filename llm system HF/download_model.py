import os
from huggingface_hub import hf_hub_download, HfApi

def download():
    model_id = os.getenv("MODEL_ID", "Qwen/Qwen2.5-Coder-0.5B-Instruct-GGUF")
    filename = os.getenv("MODEL_FILE", "qwen2.5-coder-0.5b-instruct-q5_k_m.gguf")
    target_dir = "/data/models"
    os.makedirs(target_dir, exist_ok=True)

    print(f"Intentando descargar {filename} de {model_id}...")
    try:
        path = hf_hub_download(repo_id=model_id, filename=filename, local_dir=target_dir)
        print(f"MODEL_DOWNLOADED: {path}")
    except Exception as e:
        print(f"ERROR descargando {filename}: {e}")
        print("El manager arrancara, pero el modelo fallara hasta que se corrija la ruta.")
        try:
            files = HfApi().list_repo_files(repo_id=model_id)
            gguf_files = [f for f in files if f.endswith('.gguf')]
            print(f"Archivos GGUF disponibles: {gguf_files}")
        except Exception:
            pass

if __name__ == "__main__":
    download()
