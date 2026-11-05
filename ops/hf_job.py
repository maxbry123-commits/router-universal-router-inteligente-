"""Crea Jobs de Hugging Face con el perfil de 32 GB (flavor=cpu-upgrade) y secretos via entorno.
D-21: la imagen por defecto es python:3.12 (CON git y curl). python:3.12-slim NO trae git ni curl:
los jobs no podian clonar el repo ni publicar sus artefactos y el API los reportaba COMPLETED.
REGLA (D-17): todo Job de HF usa 32 GB RAM + CPU. El perfil se fija aqui, no a mano en cada llamada.
flavors: cpu-basic(16GB) | cpu-upgrade(32GB) | cpu-performance(64GB) | cpu-xl(128GB)."""
import os,sys,json,urllib.request
API="https://huggingface.co/api/jobs/"+os.environ.get("HF_NAMESPACE","COMAND-CENTER-1")
FLAVOR=os.environ.get("HF_FLAVOR","cpu-upgrade")          # 32 GB RAM + 8 vCPU
def create(name,docker_image="python:3.12",command=None,secrets=None,environment=None,flavor=None):
    # D-22: el comando va en el campo "command" (array), NO en environment.CMD: con CMD el
    # contenedor arranco sin ejecutar nada y la API lo reportaba COMPLETED (jobs 6aebaf2c..6aebc60b).
    env=dict(environment or {})
    cmd=None
    if command:
        cmd=["bash","-lc",command] if command.startswith("bash -lc ") else command.split()
    body={"name":name,"dockerImage":docker_image,"flavor":flavor or FLAVOR,"environment":env,"secrets":secrets or {}}
    if cmd: body["command"]=cmd
    req=urllib.request.Request(API,data=json.dumps(body).encode(),
        headers={"Authorization":"Bearer "+os.environ["HF_TOKEN"],"Content-Type":"application/json"})
    with urllib.request.urlopen(req,timeout=60) as r: return json.loads(r.read())

def legacy_command(script, repo_env="GH_REPO", branch_env="GH_BRANCH", report_env="HF_REPORT_REPO"):
    """Comando para los jobs heredados de la guia anterior (JOB 2 / JOB 3).
    D-28: `upload_file` de huggingface_hub >= 2.x exige el path como ARGUMENTO CON NOMBRE
    (`upload_file(path=...)`): con el path posicional lanza TypeError y el artefacto nunca
    se publica (el job 6aebc8980e0338d1bb804a42 fallo por eso).
    D-29: el log del contenedor se imprime al final (`cat /tmp/job.log`): la evidencia del job
    queda en el stdout de HF y no solo dentro del contenedor.
    D-30: un solo envoltorio `bash -lc` (antes el comando venia doblemente envuelto)."""
    import base64
    up=base64.b64encode((
        "import os\n"
        "from huggingface_hub import upload_file\n"
        "upload_file(path='/tmp/job.log',repo_id=os.environ['"+report_env+"'],repo_type='dataset',path_in_repo='job-evidencia/"+script+".log')\n"
        ).encode()).decode()
    return ("set +e; pip install -q huggingface_hub; "
        "echo inicio $(date -u) > /tmp/job.log; "
        "echo repo=$"+repo_env+" branch=$"+branch_env+" >> /tmp/job.log; "
        "git clone --single-branch --branch $"+branch_env+" --depth 1 https://github.com/$"+repo_env+".git /tmp/repo >> /tmp/job.log 2>&1; echo clone_rc=$? >> /tmp/job.log; "
        "cd /tmp/repo && python ops/"+script+" >> /tmp/job.log 2>&1; echo rc=$? >> /tmp/job.log; "
        "echo "+up+" | base64 -d > /tmp/up.py; python /tmp/up.py >> /tmp/job.log 2>&1; echo upload_rc=$? >> /tmp/job.log; "
        "cat /tmp/job.log")

if __name__=="__main__":
    print(json.dumps(create(sys.argv[1],command=sys.argv[2] if len(sys.argv)>2 else None),indent=1)[:600])
