"""patch_storage_memory.py — Configura MCP_MEMORY_URL con el esquema correcto
de HF para buckets: hf://buckets/<owner>/<repo>.
"""
from pathlib import Path

PROXY = Path("ROUTER MVP v1/system_prompt_py/openai_compatible_proxy.py")
BUCKET_URI = "hf://buckets/COMAND-CENTER-1/yaiwes-memoria-storage"

BLOCK = f"""
# --- MINIMAX 4: MCP_MEMORY_URL ---
import os as _os
if not _os.getenv("MCP_MEMORY_URL"):
    _os.environ["MCP_MEMORY_URL"] = "{BUCKET_URI}"
    print("[INFRA] MCP_MEMORY_URL configurada: {BUCKET_URI}")
# --- FIN MINIMAX 4 ---
"""

def patch():
    if not PROXY.exists():
        raise FileNotFoundError(f"No existe {PROXY} — revisa la ruta real.")
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
    print("Proxy parcheado: MCP_MEMORY_URL con esquema hf://buckets.")

if __name__ == "__main__":
    patch()
