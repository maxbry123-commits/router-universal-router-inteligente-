import os, sys, shutil, pathlib
sys.path.insert(0, os.getcwd())
import riu_kernel
riu_kernel.hydrate()  # banco de claves -> env (bootstrap sin Jobs)

# materializar el vault en RIU_VAULT_PATH y desbloquear el puente del chat
# (las claves de proveedores nvidia/groq/... llegan por vault_hook; el unlock
#  debe vivir en el MISMO proceso que la app: nada de exec aqui)
try:
    vp = pathlib.Path(os.environ.get("RIU_VAULT_PATH", "/data/riu_vault.db"))
    vp.parent.mkdir(parents=True, exist_ok=True)
    if not vp.exists():
        if os.path.isfile("/tmp/kernel-vault.db"):
            shutil.copy("/tmp/kernel-vault.db", str(vp))
        else:
            print("VAULT_TMP_AUSENTE", flush=True)
    from integration.chat_mvp.vault_bridge import bridge
    n = bridge.unlock(os.environ["RIU_VAULT_PASSPHRASE"])
    print("vault desbloqueado: %d credenciales" % n, flush=True)
except Exception as e:
    print("GAP vault unlock: %s" % type(e).__name__, flush=True)

import uvicorn
uvicorn.run("public_chat_app:app", host="0.0.0.0", port=7860, timeout_keep_alive=120)
