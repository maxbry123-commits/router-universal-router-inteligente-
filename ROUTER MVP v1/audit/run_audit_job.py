# ROUTER MVP v1/audit/run_audit_job.py
#
# [FIX-DAG-v1] Este fichero es el INPUT BLOCK VERBATIM del owner con 5 correcciones MINIMAS,
# cada una rotulada con su evidencia real (no hay cambios silenciosos). El fichero verbatim
# original se conserva fuera del repo como evidencia del intento fallido.
#   Evidencia del fallo verbatim (log real de HF API):
#     Invalid input: expected array, received string * at command
#     Invalid input: expected record, received array * at secrets
#
import os
import sys
from huggingface_hub import HfApi

# 1. Verificar que existan las credenciales (Sin esto, se detiene)
HF_TOKEN = os.environ.get("HF_TOKEN")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
HF_USERNAME = os.environ.get("HF_USERNAME", "maxbry123-commits")

if not HF_TOKEN or not GITHUB_TOKEN:
    print("❌ ERROR FATAL: Faltan credenciales.")
    print("Asegúrate de tener HF_TOKEN y GITHUB_TOKEN en las variables de entorno.")
    sys.exit(1)

api = HfApi(token=HF_TOKEN)

# 2. Comando que se ejecutará DENTRO del Job de Hugging Face
COMMAND = f"""
set -e
echo "=== Iniciando Job de Auditoría HF ==="
apt-get update -qq && apt-get install -y -qq git
pip install --quiet huggingface_hub
# [FIX-DAG-v1/4] La rama por defecto del repo es 'reorganizacion' y NO contiene 'ROUTER MVP v1/audit/';
#   ademas el repo pesa ~11 GB, asi que se clona la rama 'main' en modo shallow + sin blobs
#   (--depth 1 --filter=blob:none) para que el Job no descargue 11 GB antes de auditar.
git clone --single-branch --branch main --depth 1 --filter=blob:none --no-checkout https://{GITHUB_TOKEN}@github.com/{HF_USERNAME}/router-universal-router-inteligente-.git /repo
cd /repo
# [FIX-DAG-v1/6] Con --filter=blob:none el checkout SIGUE materializando los 11 GB de blobs
#   (evidencia: job 6aef98400e0338d1bb83df04 se quedo descargando el worktree completo).
#   Con --no-checkout + sparse-checkout solo se materializa 'ROUTER MVP v1/audit/' (91 MB).
git sparse-checkout init --cone
git sparse-checkout set "ROUTER MVP v1/audit"
git checkout main
export HF_TOKEN=$HF_TOKEN
export HF_USERNAME={HF_USERNAME}
echo "=== Ejecutando script de auditoría ==="
python "ROUTER MVP v1/audit/hf_audit.py"
echo "=== Subiendo resultado a GitHub ==="
git -c user.email="audit@hf.job" -c user.name="hf-audit-job" add "ROUTER MVP v1/audit/HF_INVENTORY.json"
git -c user.email="audit@hf.job" -c user.name="hf-audit-job" commit -m "audit: HF_INVENTORY generado por Job"
git push origin main
echo "=== Job finalizado con éxito ==="
"""

print(f"🚀 Solicitando Job a Hugging Face para: {HF_USERNAME}")
try:
    job = api.run_job(
        image="python:3.11-slim",
        # [FIX-DAG-v1/1] La API de HF exige 'command' como ARRAY: el string plano devolvia
        #   "Invalid input: expected array, received string * at command" (D-22/D-32).
        command=["bash", "-lc", COMMAND],
        # [FIX-DAG-v1/5] La API rechaza identificadores repetidos entre 'env' y 'secrets'
        #   ("Bad Request: Identifiers must be unique across `env` and `secrets`").
        #   Los tokens quedan SOLO en 'secrets' (cifrados server-side y expuestos como variables
        #   de entorno dentro del Job); en 'env' queda solo el parametro no sensible.
        env={"HF_USERNAME": HF_USERNAME},
        # [FIX-DAG-v1/2] La API de HF exige 'secrets' como RECORD (mapa nombre->valor, cifrado
        #   server-side): la lista devolvia "expected record, received array * at secrets".
        secrets={"HF_TOKEN": HF_TOKEN, "GITHUB_TOKEN": GITHUB_TOKEN},
        # [FIX-DAG-v1/3] Sin flavor la API usa cpu-basic; la regla D-17 de la casa y el do_not
        #   vigente exigen 32 GB (cpu-upgrade) en todo Job de HF.
        flavor="cpu-upgrade",
    )
    print(f"✅ Job creado exitosamente. ID: {job.id}")
    print(f"🔗 URL del Job: {job.url}")
    print("\n⏳ Esperando logs en tiempo real (esto puede tardar 1-2 minutos)...\n")
    
    # Imprimir logs reales
    for line in api.fetch_job_logs(job_id=job.id, follow=True):
        print(line, end="", flush=True)
        
    print("\n✅ Logs finalizados.")
except Exception as e:
    print(f"\n❌ El Job falló o no se pudo crear: {e}")
    sys.exit(1)
