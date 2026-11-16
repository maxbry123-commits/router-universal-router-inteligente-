"""patch_proxy_lifecycle.py — Añade startup/shutdown al proxy para power_daemon,
billing_monitor y storage_wiring; y la ruta /billing/status.
No reescribe el proxy: inserta bloques idempotentes.
"""
import re
from pathlib import Path

PROXY = Path("ROUTER MVP v1/system_prompt_py/openai_compatible_proxy.py")

LIFECYCLE_IMPORTS = """
# --- MINIMAX 4: ciclo de vida de infraestructura ---
from external.core.power_daemon import PowerDaemon
from external.core.billing_monitor import BillingMonitor
from external.core.storage_wiring import StorageWiring
_power_daemon = PowerDaemon()
_storage_ok = False
# --- FIN MINIMAX 4 ---
"""

LIFECYCLE_EVENTS = """
# --- MINIMAX 4: eventos de ciclo de vida ---
@app.on_event("startup")
async def _infra_startup():
    global _storage_ok
    _storage_ok = StorageWiring.verify_storage_connection()
    _power_daemon.start()
    print(f"[INFRA] storage_ok={_storage_ok} power_daemon=ON")

@app.on_event("shutdown")
async def _infra_shutdown():
    _power_daemon.stop()
    print("[INFRA] power_daemon=OFF")

@app.get("/billing/status")
def billing_status():
    return BillingMonitor.check_runtime_cost()
# --- FIN MINIMAX 4 ---
"""

def patch():
    text = PROXY.read_text(encoding="utf-8")
    if "MINIMAX 4: ciclo de vida" in text:
        print("Proxy ya parcheado (idempotente).")
        return
    # Insertar imports tras el último import existente
    lines = text.splitlines()
    last_import = max(i for i, l in enumerate(lines) if l.startswith(("import ", "from ")))
    lines.insert(last_import + 1, LIFECYCLE_IMPORTS)
    text = "\n".join(lines)
    # Insertar eventos tras la creación de app
    if "app = FastAPI()" in text:
        text = text.replace("app = FastAPI()", "app = FastAPI()\n" + LIFECYCLE_EVENTS, 1)
    elif "app = create_app()" in text:
        text = text.replace("app = create_app()", "app = create_app()\n" + LIFECYCLE_EVENTS, 1)
    else:
        raise RuntimeError("No se encontró app = FastAPI() ni app = create_app()")
    PROXY.write_text(text, encoding="utf-8")
    print("Proxy parcheado: lifecycle + /billing/status.")

if __name__ == "__main__":
    patch()
