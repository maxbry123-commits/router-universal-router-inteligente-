"""ops/job_status.py — estado de un job leido del Dataset (fuente durable de los resultados).

D-53: la cadena consultaba /tmp/out/<job>/result.json, que es volatil (se pierde al
reiniciar el sandbox) y que la cadena misma borra antes de relanzar un job. Con este
lector el estado se toma siempre del Dataset, donde cada job publica su resultado.
Uso: python ops/job_status.py <job>
Salida: PASS | FAIL | SIN_RESULTADO | ERROR
"""
import json, os, sys

def status(job, run_id=None, ds=None):
    run_id = run_id or os.environ.get("RUN_ID", "20261104-kernel01")
    ds = ds or os.environ.get("DATASET_REPO", "COMAND-CENTER-1/router-universal-router-inteligente-auditoria")
    from huggingface_hub import hf_hub_download
    p = hf_hub_download(ds, repo_type="dataset",
                         filename=f"{run_id}/{job}/result.json",
                         token=os.environ.get("HF_TOKEN"))
    return json.load(open(p)).get("status", "SIN_RESULTADO")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("SIN_RESULTADO")
        sys.exit(0)
    try:
        print(status(sys.argv[1]))
    except Exception as e:
        print("SIN_RESULTADO")
        sys.exit(0)
