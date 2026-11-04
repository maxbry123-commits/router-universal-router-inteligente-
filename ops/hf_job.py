"""Crea Jobs de Hugging Face con el perfil de 32 GB (flavor=cpu-upgrade) y secretos via entorno.
REGLA (D-17): todo Job de HF usa 32 GB RAM + CPU. El perfil se fija aqui, no a mano en cada llamada.
flavors: cpu-basic(16GB) | cpu-upgrade(32GB) | cpu-performance(64GB) | cpu-xl(128GB)."""
import os,sys,json,urllib.request
API="https://huggingface.co/api/jobs/"+os.environ.get("HF_NAMESPACE","COMAND-CENTER-1")
FLAVOR=os.environ.get("HF_FLAVOR","cpu-upgrade")          # 32 GB RAM + 8 vCPU
def create(name,docker_image="python:3.12-slim",command=None,secrets=None,environment=None,flavor=None):
    env=dict(environment or {})
    if command: env["CMD"]=command
    body={"name":name,"dockerImage":docker_image,"flavor":flavor or FLAVOR,"environment":env,"secrets":secrets or {}}
    req=urllib.request.Request(API,data=json.dumps(body).encode(),
        headers={"Authorization":"Bearer "+os.environ["HF_TOKEN"],"Content-Type":"application/json"})
    with urllib.request.urlopen(req,timeout=60) as r: return json.loads(r.read())
if __name__=="__main__":
    print(json.dumps(create(sys.argv[1],command=sys.argv[2] if len(sys.argv)>2 else None),indent=1)[:600])
