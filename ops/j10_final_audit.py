from common import *
from wiring_check import run as wc
# ops/j10_final_audit.py — auditoria final de cierre (S12_final).
# Guia: kernel/GUIDE.md S12_final: {jobs: [j9_remirror, j10_final_audit], gate: [Space==new HEAD, audit PASS]}
# D-23: la guia DECLARA este job pero NO incluye su codigo. Implementado aqui con el patron
# exacto de ops/j8_audit.py (mismo helper, mismos gates) + la validacion final del kernel.
def main():
    jobs=need("AUDIT_JOBS").split(",");res={}
    for j in jobs:
        try:
            r=json.load(open(dl(j,"result.json")));res[j]=r
            check(f"{j}_PASS",r["status"]=="PASS",r.get("commit"))
        except Exception as e:check(f"{j}_result_found",False,str(e)[:120])
    # D-146: reutiliza el clon disponible en modo SOLO LECTURA (REUSE_CLONE) o clona uno propio.
    d=clone(wd("fa"));w=wc(d)
    check("wiring_check_on_final_head",w["ok"],[c["name"] for c in w["checks"] if not c["ok"]])
    kh=head(d)
    (OUT/"final_audit.json").write_text(json.dumps({
        "phase":"final","audited_commit":kh,
        "per_job":{j:r["status"] for j,r in res.items()},
        "wiring":w},indent=1))
    finish({"audited_commit":kh,"phase":"final","per_job":{j:r["status"] for j,r in res.items()}},commit=kh)
if __name__=="__main__":run(main)
