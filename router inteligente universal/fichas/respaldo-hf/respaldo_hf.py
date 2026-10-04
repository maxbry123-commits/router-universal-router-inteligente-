"""Router de respaldo HF (ficha respaldo-hf). Uso: HF_TOKEN=... python3 respaldo_hf.py start|status|stop [job_id]

start  -> enciende un L4 con llama.cpp en modo router (un modelo a la vez) y muestra la URL para el harness.
status -> estado del job.  stop -> apaga el job.
La URL solo responde con un token de Hugging Face valido (Authorization: Bearer <HF_TOKEN>).
"""
import os
import sys

from huggingface_hub import HfApi, Volume

NS = "COMAND-CENTER-1"
CMD = ["/app/llama-server", "--host", "0.0.0.0", "--port", "8080", "--models-dir", "/modelos", "--models-max", "1",
       "-ngl", "999", "-fa", "on", "-np", "1", "-b", "128", "-c", "16384", "--temp", "0", "--top-k", "20",
       "--top-p", "0.95", "--no-mmproj", "--reasoning-budget", "0", "--spec-type", "draft-mtp",
       "--spec-draft-n-max", "2", "--jinja"]


def main() -> None:
    api = HfApi(token=os.environ["HF_TOKEN"])
    accion = sys.argv[1] if len(sys.argv) > 1 else "status"
    if accion == "start":
        job = api.run_job(image="ghcr.io/ggml-org/llama.cpp:server-cuda", command=CMD, flavor="l4x1", timeout="2h",
                          namespace=NS, expose=[8080], name="router-respaldo-l4",
                          volumes=[Volume(type="bucket", source=f"{NS}/yaiwes-memoria-storage", mount_path="/modelos",
                                          path="router-respaldo/modelos", read_only=True)])
        print("JOB", job.id)
        print("RESPALDO_HF_URL=https://" + job.id + "--8080.hf.jobs")
    elif accion == "status":
        print(api.inspect_job(job_id=sys.argv[2], namespace=NS).status)
    elif accion == "stop":
        api.cancel_job(job_id=sys.argv[2], namespace=NS)
        print("apagado", sys.argv[2])


if __name__ == "__main__":
    main()
