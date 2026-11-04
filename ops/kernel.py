import sys,yaml,json,time,os,pathlib
sys.path.insert(0,str(pathlib.Path(__file__).parent))
from common import sh,redact,dl
P="kernel/KERNEL.yaml"
ORDER=["j0_preflight","j1_inventory","j2_graph","j3_history","j4_plan","j5_apply","j7_mirror","j8_audit","j6_rewrite","j9_remirror","j10_final_audit"]
load=lambda:yaml.safe_load(open(P))
def save(k):open(P,"w").write(yaml.safe_dump(k,sort_keys=False,allow_unicode=True))
def validate(k):
    e=[f"missing:{r}" for r in("authority","objective","domains","jobs","approvals","handoff","protected","entrypoints","lint_mode") if r not in k];J=k.get("jobs",{});seen=set()
    for j,v in J.items():
        e+=[f"{j}->unknown {d}" for d in v.get("needs",[]) if d not in J]
        if not v.get("script"):e.append(f"{j}->missing script")
        if not v.get("timeout"):e.append(f"{j}->missing timeout")
        for d in v.get("needs",[]):seen.add((d,j))
    def cyc(n,stack):
        if n in stack:return [n]
        for d in J.get(n,{}).get("needs",[]):
            r=cyc(d,stack+[n])
            if r:return r
        return None
    for j in J:
        c=cyc(j,[])
        if c:e.append(f"cycle:{j}:{c}");break
    for a,ap in k.get("approvals",{}).items():
        if not isinstance(ap,dict):e.append(f"approval:{a}:not_dict")
        elif "approved" not in ap:e.append(f"approval:{a}:no_approved_field")
    h=k.get("handoff",{})
    for f in("next","log","flags"):
        if f not in h:e.append(f"handoff:{f}:missing")
    return e
def result_of(job):
    try:
        return json.load(open(dl(job,"result.json")))
    except Exception as ex:return {"job":job,"status":"MISSING","error":redact(str(ex))[:200]}
def cmd_validate():
    k=load();e=validate(k)
    print(json.dumps({"cmd":"validate","errors":e,"jobs":len(k.get("jobs",{})),"next":k.get("handoff",{}).get("next"),"progress_pct":k.get("progress_pct")},indent=1,ensure_ascii=False))
    sys.exit(1 if e else 0)
def cmd_next():
    k=load();order=ORDER or list(k["jobs"]);cur=k.get("handoff",{}).get("next")
    for j in order:
        if j!=cur:continue
        r=result_of(j)
        if r.get("status")=="PASS":
            print(json.dumps({"cmd":"next","job":None,"reason":f"{j} already PASS with same commit","commit":r.get("commit")},indent=1));return
        print(json.dumps({"cmd":"next","job":j,"status":r.get("status"),"commit":r.get("commit")},indent=1));return
    for j in order:
        r=result_of(j)
        if r.get("status")!="PASS":
            print(json.dumps({"cmd":"next","job":j,"status":r.get("status"),"reason":"first_unmet"},indent=1));return
    print(json.dumps({"cmd":"next","job":None,"reason":"queue_empty"},indent=1))
def cmd_apply():
    job=sys.argv[2] if len(sys.argv)>2 else os.environ.get("JOB_NAME")
    if not job:print(json.dumps({"cmd":"apply","error":"missing job"}));sys.exit(2)
    k=load();r=result_of(job);st=r.get("status")
    h=k.setdefault("handoff",{"next":job,"log":[],"flags":[]})
    h["log"].append({"job":job,"status":st,"commit":r.get("commit"),"ts":time.strftime("%FT%TZ",time.gmtime()),"run_id":os.environ.get("RUN_ID")})
    if st!="PASS":h["flags"].append(f"🚩 {job} {st}")
    done=[x["job"] for x in h["log"] if x["status"]=="PASS"]
    done=[j for j in ORDER if j in done]   # el progreso se mide sobre el DAG, no sobre tareas extra
    h["next"]=next((j for j in ORDER if j not in done),None)
    k["progress_pct"]=int(100*len(done)/len(ORDER))
    save(k)
    msg=f"kernel: {job} {st}"
    sh(["git","add",P],check=False)
    sh(["git","-c","user.name=kernel-bot","-c","user.email=bot@local","commit","-m",msg],check=False)
    print(json.dumps({"cmd":"apply","job":job,"status":st,"next":h["next"],"progress_pct":k["progress_pct"],"flags":h["flags"]},indent=1,ensure_ascii=False))
if __name__=="__main__":
    c=(sys.argv[1] if len(sys.argv)>1 else "validate")
    {"validate":cmd_validate,"next":cmd_next,"apply":cmd_apply}.get(c,cmd_validate)()
