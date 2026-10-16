"""Router de respaldo HF (ficha respaldo-hf). Va DIRECTO al harness DeepSeek; no pasa por el Router de GitHub.

Enciende un L4 en Hugging Face con el token de HF del banco (huggingface/token-1-new) y le conecta tu almacenamiento
(bucket COMAND-CENTER-1/yaiwes-memoria-storage, carpeta router-respaldo/modelos) como disco: listo en ~73 s (probado).

Uso:  HF_TOKEN=... python3 respaldo_hf.py start 27b|35b   -> imprime job, url y modelo (JSON)
      HF_TOKEN=... python3 respaldo_hf.py status <job>
      HF_TOKEN=... python3 respaldo_hf.py stop <job>       -> apagado remoto (boton del chat)
Apagado automatico dentro del L4: 30 s despues de terminar una respuesta, o 5 min sin ningun pedido. Tope 2 h.
La URL https://<job>--8080.hf.jobs solo responde con el token de HF (Authorization: Bearer <HF_TOKEN>).
"""
import json
import os
import sys

from huggingface_hub import HfApi, Volume

NS = "COMAND-CENTER-1"
MODELOS = {
    "27b": ("Qwen3.8-27B-UD-Q3_K_XL.gguf", "qwen3.8-27b"),
    "35b": ("Qwen3.6-35B-A3B-UD-Q3_K_XL.gguf", "qwen3.6-35b"),
}
ARRANQUE = r"""/app/llama-server --host 0.0.0.0 --port 8080 -m "/modelos/$ARCHIVO" --alias "$ALIAS" -ngl 999 -fa on -np 1 -b 128 -c 16384 --temp 0 --top-k 20 --top-p 0.95 --no-mmproj --reasoning-budget 0 --spec-type draft-mtp --spec-draft-n-max 2 --jinja > /tmp/l.log 2>&1 &
P=$!
while kill -0 $P 2>/dev/null; do
  sleep 5
  I=$(( $(date +%s) - $(stat -c %Y /tmp/l.log) ))
  if grep -q print_timing /tmp/l.log && [ $I -ge 30 ]; then echo APAGADO_FIN_DE_SALIDA; kill $P; exit 0; fi
  if [ $I -ge 300 ]; then echo APAGADO_5_MIN_SIN_USO; kill $P; exit 0; fi
done
tail -n 20 /tmp/l.log
"""


def main() -> None:
    api = HfApi(token=os.environ["HF_TOKEN"])
    accion = sys.argv[1] if len(sys.argv) > 1 else "status"
    if accion == "start":
        archivo, alias = MODELOS[sys.argv[2] if len(sys.argv) > 2 else "35b"]
        job = api.run_job(image="ghcr.io/ggml-org/llama.cpp:server-cuda", command=["bash", "-c", ARRANQUE],
                          env={"ARCHIVO": archivo, "ALIAS": alias}, flavor="l4x1", timeout="2h", namespace=NS,
                          expose=[8080], name="router-respaldo-l4",
                          volumes=[Volume(type="bucket", source=f"{NS}/yaiwes-memoria-storage", mount_path="/modelos",
                                          path="router-respaldo/modelos", read_only=True)])
        print(json.dumps({"job_id": job.id, "url": "https://" + job.id + "--8080.hf.jobs", "modelo": alias}))
    elif accion == "status":
        print(api.inspect_job(job_id=sys.argv[2], namespace=NS).status.stage)
    elif accion == "stop":
        api.cancel_job(job_id=sys.argv[2], namespace=NS)
        print(json.dumps({"job_id": sys.argv[2], "status": "CANCELED"}))


if __name__ == "__main__":
    main()
