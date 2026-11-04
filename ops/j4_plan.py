from common import *
import csv,collections,fnmatch,pathlib,yaml,hashlib
def main():
    inv=list(csv.DictReader(open(dl("j1_inventory","inventory.csv"))))
    g=json.load(open(dl("j2_graph","graph.json")))
    touched=set(open(dl("j3_history","touched.txt")).read().split("\n"))
    d=clone("/tmp/p");kp=pathlib.Path(d)/"kernel/KERNEL.yaml"
    k=yaml.safe_load(kp.read_text()) if kp.exists() else {}
    prot=k.get("protected",[]);prot_f=lambda p:any(fnmatch.fnmatch(p,x) for x in prot)
    inb=collections.Counter(b for a,b in g["edges"]);ent=set(g["entrypoints"]);dyn=g["dynamic"]
    code=[r["path"] for r in inv if r["class"]=="code"]
    cand=[p for p in code if inb[p]==0 and p not in ent and not prot_f(p)]
    orphans=[];kept=[]
    # D-15 (§20 ruta 8 smaller_scope + ruta 1 existing_code): un SOLO barrido del repo
    # con `git grep -f` (patrones multiples) en vez de hasta 3000 barridos completos.
    # Medido: 74 s por barrido => 3000 barridos = 61 h (inviable). Un barrido = misma
    # semantica de "no_text_ref" (referencias fuera del propio fichero).
    pats=cand[:int(os.environ.get("MAX_GREP","3000"))]
    refs=collections.defaultdict(set)
    if pats:
        pf="/tmp/j4_stems.txt"
        pathlib.Path(pf).write_text("\n".join(sorted({pathlib.Path(p).stem for p in pats if pathlib.Path(p).stem}))+"\n")
        # fase 1: ficheros que contienen algun stem (salida corta, sin -o)
        r1=sh(["git","grep","-I","-l","-F","-f",pf,"--","."],cwd=d,check=False)
        mfiles=[x for x in r1.stdout.splitlines() if x]
        # fase 2: solo sobre esos ficheros, con -o para saber que stem aparece donde
        if mfiles:
            ff="/tmp/j4_files.txt"
            pathlib.Path(ff).write_text("\n".join(mfiles)+"\n")
            r2=sh(["git","grep","-I","-o","-F","-f",pf,"--pathspec-from-file="+ff],cwd=d,check=False)
            for line in r2.stdout.splitlines():
                f,_,m=line.partition(":")
                refs[m].add(f)
    for p in pats:
        stem=pathlib.Path(p).stem
        par=str(pathlib.Path(p).parent)+"/"
        others={f for f in refs.get(stem,()) if f!=p}
        s={"no_inbound":True,"no_text_ref":not others,"not_recent":p not in touched,"no_dynamic_loader_nearby":not any(x.startswith(par) for x in dyn)}
        (orphans if all(s.values()) else kept).append({"path":p,"signals":s})
    heavy=sorted({"/".join(r["path"].split("/")[:r["path"].split("/").index(h)+1]) for r in inv if r["class"]=="heavy" for h in r["path"].split("/") if h in("node_modules","venv",".venv","__pycache__","dist","build",".next",".cache","site-packages")})
    plan={"quarantine":[o["path"] for o in orphans],"untrack":heavy,"purge_paths":heavy,
          "dedupe_report_only":"see j1 duplicates_sample","kept_with_reason":kept[:200],"code_files":len(code)}
    plan["plan_sha256"]=hashlib.sha256(json.dumps({k2:plan[k2] for k2 in("quarantine","untrack","purge_paths")},sort_keys=True).encode()).hexdigest()
    (OUT/"plan.json").write_text(json.dumps(plan,indent=1))
    check("plan_built",True,f"q={len(orphans)} untrack={len(heavy)}")
    check("protected_not_in_plan",not [p for p in plan["quarantine"] if prot_f(p)])
    check("quarantine_le_40pct_of_code",len(orphans)<=0.4*max(len(code),1),f"{len(orphans)}/{len(code)}")
    finish({"plan_sha256":plan["plan_sha256"],"quarantine":len(orphans),"untrack_dirs":len(heavy)},commit=head(d))
if __name__=="__main__":run(main)
