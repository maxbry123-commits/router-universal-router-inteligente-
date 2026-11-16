"""patch_storage_memory.py — Configura MCP_MEMORY_URL desde el bucket y lo
inyecta en el entorno del proxy antes de que arranque.
"""
import os
from pathlib import Path

PROXY = Path("ROUTER MVP v1/system_prompt_py/openai_compatible_proxy.py")
BUCKET_ID = "COMAND-CENTER-1/yaiwes-memoria-storage"

BLOCK = f"""
# --- MINIMAX 4: MCP_MEMORY_URL desde bucket ---
import os as _os
if not _os.getenv("MCP_MEMORY_URL"):
    _os.environ["MCP_MEMORY_URL"] = "https://huggingface.co/buckets/{BUCKET_ID}"
    print("[INFRA] MCP_MEMORY_URL configurada desde bucket.")
# --- FIN MINIMAX 4 ---
"""

def patch():
    text = PROXY.read_text(encoding="utf-8")
    if "MINIMAX 4: MCP_MEMORY_URL" in text:
        print("Proxy ya tiene MCP_MEMORY_URL (idempotente).")
        return
    if "app = FastAPI()" in text:
        text = text.replace("app = FastAPI()", "app = FastAPI()\n" + BLOCK, 1)
    elif "app = create_app()" in text:
        text = text.replace("app = create_app()", "app = create_app()\n" + BLOCK, 1)
    else:
        raise RuntimeError("No se encontró app = FastAPI() ni app = create_app()")
    PROXY.write_text(text, encoding="utf-8")
    print("Proxy parcheado: MCP_MEMORY_URL desde bucket.")

if __name__ == "__main__":
    patch()
