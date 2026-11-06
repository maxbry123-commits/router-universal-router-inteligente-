from common import *
from wiring_check import run as wc
def main():
    jobs=need("AUDIT_JOBS").split(",");res={}
    for j in jobs:
        try:r=json.load(open(dl(j,"result.json")));res[j]=r;check(f"{j}_PASS",r["status"]=="PASS",r.get("commit"))
        except Exception as e:check(f"{j}_result_found",False,str(e)[:100])
    reuse=os.environ.get("REUSE_CLONE","").strip()
    if reuse and os.path.isdir(os.path.join(reuse,".git")):
        # D-105: mismo criterio que D-104 en j7_mirror: si ya hay un clon materializado
        # (373.422 ficheros) se reutiliza en vez de clonar otra vez. El grafo se construye
        # sobre el MISMO arbol, asi que el resultado del gate es identico y el job es
        # idempotente. Sin REUSE_CLONE se comporta como antes (clon en WORK_DIR).
        d=reuse
    else:
        d=clone(os.path.join(os.environ.get("WORK_DIR","/workspace/work"),"au"))
    w=wc(d)   # G2: scratch en WORK_DIR (NAS)
    check("wiring_check_on_target",w["ok"],[c["name"] for c in w["checks"] if not c["ok"]])
    (OUT/"audit.json").write_text(json.dumps({"phase":os.environ.get("PHASE","pre"),"audited_commit":head(d),
        "per_job":{j:r["status"] for j,r in res.items()},"wiring":w},indent=1))
    finish({"audited_commit":head(d),"phase":os.environ.get("PHASE","pre")},commit=head(d))
if __name__=="__main__":run(main)
