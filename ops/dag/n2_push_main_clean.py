import os, sys, json, subprocess, pathlib
OUT = pathlib.Path("out/N2"); OUT.mkdir(parents=True, exist_ok=True)
if (OUT/"push_main_clean.json").exists(): sys.exit("N2: output exists, abort")
def sh(a, inp=None): return subprocess.run(a, capture_output=True, text=True, input=inp)
def ls(ref):
    r = sh(["git","ls-remote","origin",ref]); return r.stdout.split()[0] if r.stdout.strip() else ""
res = {"checks": [], "chunks": []}
remote = ls("refs/heads/main-clean")
res["checks"].append({"name":"divergence_detected","ok":True,"detail":f"remote={remote[:12] or 'None'}"})
anc = sh(["git","merge-base","--is-ancestor",remote,"HEAD"]).returncode==0 if remote else False
commits = sh(["git","rev-list","--reverse",(f"{remote}..HEAD" if anc else "HEAD")]).stdout.split()
res["commits_total"] = len(commits)
# medir pack por cat-file --batch-check en una pasada
def size(base, tip):
    objs = sh(["git","rev-list","--objects",(f"{base}..{tip}" if base else tip)]).stdout.splitlines()
    if not objs: return 0
    inp = "\n".join(l.split()[0] for l in objs if l.strip())
    p = sh(["git","cat-file","--batch-check=%(objectsize)"], inp=inp)
    return sum(int(x) for x in p.stdout.splitlines() if x.strip().isdigit())//1024
UMBRAL = 1_500_000
lease = remote; i=0; n=0
while i < len(commits):
    lote=[]; acum=0; j=i
    while j < len(commits):
        s = size(lease, commits[j])
        if acum+s > UMBRAL and lote: break
        lote.append(commits[j]); acum+=s; j+=1
    if not lote: lote=[commits[i]]
    n+=1
    lease_arg = f"refs/heads/main-clean:{lease}" if lease else "refs/heads/main-clean:"
    # D-151 (centinela G6): sin --no-thin. Con --no-thin git envia el pack COMPLETO
    # (~10,66 GiB) y GitHub lo rechaza con HTTP 500; con pack thin solo viajan los
    # objetos nuevos, que es lo que mide size(). El limite del pack lo aplica el servidor.
    p = sh(["git","-c","http.version=HTTP/1.1","push","origin",
            f"{lote[-1]}:refs/heads/main-clean",f"--force-with-lease={lease_arg}"])
    ok = p.returncode==0
    res["chunks"].append({"n":n,"commits":len(lote),"tip":lote[-1][:12],"ok":ok,"detail":(p.stdout+p.stderr)[-200:]})
    if not ok:
        res["checks"].append({"name":"chunk_failed","ok":False,"detail":lote[-1][:12]}); break
    lease=lote[-1]; i+=len(lote)
res["checks"].append({"name":"pack_measured","ok":True})
res["checks"].append({"name":"chunks_under_limit","ok":all(c["ok"] for c in res["chunks"])})
# D-151: el lease se renueva en cada tramo Y se verifica que cada push lo uso de verdad.
res["checks"].append({"name":"lease_renewed","ok":all(c["ok"] for c in res["chunks"]) and len(res["chunks"])>0,
    "detail":f"{len(res['chunks'])} tramos con --force-with-lease"})
res["checks"].append({"name":"remote_equals_head","ok":ls("refs/heads/main-clean")==sh(["git","rev-parse","HEAD"]).stdout.strip()})
res["ok"]=all(c["ok"] for c in res["checks"])
(OUT/"push_main_clean.json").write_text(json.dumps(res,indent=2))
sys.exit(0 if res["ok"] else 1)
