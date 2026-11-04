from common import *
from wiring_check import run as wc
def main():
    jobs=need("AUDIT_JOBS").split(",");res={}
    for j in jobs:
        try:r=json.load(open(dl(j,"result.json")));res[j]=r;check(f"{j}_PASS",r["status"]=="PASS",r.get("commit"))
        except Exception as e:check(f"{j}_result_found",False,str(e)[:100])
    d=clone("/tmp/au");w=wc(d)
    check("wiring_check_on_target",w["ok"],[c["name"] for c in w["checks"] if not c["ok"]])
    (OUT/"audit.json").write_text(json.dumps({"phase":os.environ.get("PHASE","pre"),"audited_commit":head(d),
        "per_job":{j:r["status"] for j,r in res.items()},"wiring":w},indent=1))
    finish({"audited_commit":head(d),"phase":os.environ.get("PHASE","pre")},commit=head(d))
if __name__=="__main__":run(main)
