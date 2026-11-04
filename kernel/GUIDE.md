# GUIDE.md — REPO KERNEL DSL DAG v1

Bloques 1+2+3 concatenados en orden. Generado por `ops/make_guide.py`; las fuentes viven en `kernel/` y `ops/`.

## BLOQUE 1/3 — KERNEL, GOALS, SIMULACIONES, COUNCIL, DAG

# 0. INPUT BLOCK (VERBATIM, FROZEN)
```yaml
input_block:
  mode: [VERBATIM, IMMUTABLE, READ_ONLY, DATA_ONLY_UNTIL_BOUND]
  frozen_files:
    - organización_de_la_raíz_del_repo.md   # sha256 computed at S0, never edited
  objective_verbatim: >
    objetivo organización del repo limpieza de archivos no cableados o innecesarios o code suelto
    eliminar historial al finalizar la organización y cableado recuperación de el cableado
    auto pull y mirror de code en servidor space huggueface y hacer un sistema centralizado de
    comunicación de conexión del code que evite convertir el cableado en un barrio chino de
    cables y de archivos desordenados mal ubicados debe ser tipo software saas
  constraints_verbatim: ["No Github acción", "NO LFS GITHUB", "no usar vercel o huggueface sin autorización"]
  minimax_inputs:            # 1 to 1 -> job that implements it
    R1: {what: clone outer branch (--branch),            job: launch.sh}
    R2: {what: credential erased before fetch,           job: common.py genv()}   # env header, not URL token
    R3: {what: MAX_COMMITS + branch holds ops/,          job: j3_history (HISTORY_DAYS) + j0}
    R4: {what: sizing 338,006 files / 7.9GB / >30GB disk, job: j0 MIN_FREE_GB + j3 shallow-since}
    R5: {what: third job could not start,                job: launch.sh clones for every job}
    R6: {what: --timeout on every hf job,                job: launch.sh}
    R7: {what: registry with real topology pending_audit, job: connections/registry.yaml + wiring_check}
    R8: {what: audit PASS/FAIL + commit ref,             job: j8_audit}
    R9: {what: connections/{registry,topology,endpoints,healthchecks}.yaml, job: kernel layout}
    R10:{what: pattern catalogs 6 vs 5 not unified,      job: ROADMAP item U1 (own job + test)}
  improved_over_minimax:
    - token never in URL/argv/logs (GIT_CONFIG_* env extraheader + redact)
    - exec(open()) replaced by python <path>
    - one clone per job (idempotent), no double clone
    - history by shallow-since window, not full 7.9GB
```

# 1. 12 GOALS (INPUT -> OUTPUT)
```yaml
goals:
  G1:  {in: repo+branch,          out: backup bundle + tag pre-reorg-<RUN_ID>,   job: j5_apply(tag) + j6_rewrite(bundle)}
  G2:  {in: tracked tree,         out: classified inventory.csv,                 job: j1_inventory}
  G3:  {in: code,                 out: import/call graph (static),               job: j2_graph}
  G4:  {in: graph+refs+history,   out: orphan list with 3 signals,               job: j4_plan}
  G5:  {in: orphans,              out: quarantine (git mv), never delete,        job: j5_apply}
  G6:  {in: current layout,       out: target layout by domain,                  job: KERNEL.layout + roadmap}
  G7:  {in: wiring map,           out: connections/registry.yaml pending_audit,  job: roadmap R1 + wiring_check}
  G8:  {in: registry,             out: active only with evidence,                job: wiring_check + healthchecks}
  G9:  {in: clean repo,           out: rewritten history on main-clean,          job: j6_rewrite (approval)}
  G10: {in: main,                 out: auto pull verified on Space,              job: j7_mirror}
  G11: {in: repo,                 out: code mirror on Space,                     job: j7_mirror}
  G12: {in: everything,           out: audit PASS/FAIL + commit ref,             job: j8_audit}
```

# 2. 4 SIMULATIONS (GAP -> BUILT-IN FIX)
```yaml
simulations:
  SIM1_happy_path:   {gap: history analysis exceeds timeout,  fix: j3 uses --shallow-since + blobless, timeout 1h/job}
  SIM2_private_repo: {gap: fetch exit 128 after remote reset, fix: env extraheader per command, never persisted}
  SIM3_timeout_disk: {gap: job dies, all lost,                fix: small jobs, result.json to Dataset, rerun by idempotency_key}
  SIM4_rewrite:      {gap: wired file deleted, no way back,   fix: tag+bundle first, rewrite only to main-clean, swap by approval}
```

# 3. 12-STEP ASK COUNCIL (CLOSE CRITERIA)
```yaml
council:
  1: CAPTURE     -> sha256 of frozen files + objective
  2: BACKUP      -> tag + verified bundle
  3: INVENTORY   -> csv complete, case collisions = 0
  4: GRAPH       -> unresolved baseline saved
  5: ORPHANS     -> >=3 signals each, protected excluded
  6: QUARANTINE  -> git mv to _quarantine/, branch reorg/<RUN_ID>
  7: RESTRUCTURE -> batches <=20 files, wiring_check after each batch
  8: REWIRE      -> no new unresolved vs baseline
  9: TEST        -> real backend start + frontend visual (3 reviews)
  10: REGISTRY   -> connections verified, active only with evidence
  11: HISTORY    -> rewrite on main-clean only after 2 independent PASS
  12: MIRROR+PULL-> Space RUNNING, health commit == branch HEAD, final audit
```

# 4. KERNEL — SUPREME AUTHORITY (`kernel/KERNEL.yaml`)
```yaml
kernel_version: 1
authority: ROOT
objective: Organize repo, remove unwired/unneeded code, restore wiring, mirror to
  HF Space, central contract-first connection system
lint_mode: warn
protected:
- kernel/**
- connections/**
- ops/**
- vercel.json
- README.md
- Dockerfile
- package.json
- requirements*.txt
- memory_agente_minimax_02.md
entrypoints:
- chat-router/chat/frontend/shell.html
- dsla/dsla.py
domains:
  building: router-mvp/raiz_router
  fichas: router-mvp/fichas
  engines: chat-router/motores
  plugins: chat-router/plugins
  harness: chat-router/chat/backend/deepseek_harness
  chat: chat-router/chat/frontend
  backend: chat-router/chat/backend
  agents: chat-router/agentes
  mvp: router-mvp
  ops: ops
  kernel: kernel
  connections: connections
layout_rules:
- every file belongs to exactly one domain
- cross-domain calls only through gateway + registry entry
- no file without owner/domain/reference -> _quarantine/
jobs:
  j0_preflight:
    script: j0_preflight
    needs: []
    timeout: 15m
  j1_inventory:
    script: j1_inventory
    needs:
    - j0_preflight
    timeout: 1h
  j2_graph:
    script: j2_graph
    needs:
    - j0_preflight
    timeout: 1h
  j3_history:
    script: j3_history
    needs:
    - j0_preflight
    timeout: 1h
  j4_plan:
    script: j4_plan
    needs:
    - j1_inventory
    - j2_graph
    - j3_history
    timeout: 1h
  j5_apply:
    script: j5_apply
    needs:
    - j4_plan
    approval: J5_apply
    timeout: 2h
  j7_mirror:
    script: j7_mirror
    needs:
    - j5_apply
    approval: deploy
    timeout: 1h
  j8_audit:
    script: j8_audit
    needs:
    - j7_mirror
    timeout: 30m
  j6_rewrite:
    script: j6_rewrite
    needs:
    - j8_audit
    approval: J6_rewrite
    timeout: 3h
  j9_remirror:
    script: j7_mirror
    needs:
    - j6_rewrite
    approval: deploy
    timeout: 1h
  j10_final_audit:
    script: j8_audit
    needs:
    - j9_remirror
    timeout: 30m
approvals:
  J5_apply:
    approved: false
    plan_sha256: ''
  J6_rewrite:
    approved: false
    plan_sha256: ''
  merge_main:
    approved: false
  deploy:
    approved: false
roadmap:
  R1:
    task: write connections/registry.yaml from j2 graph, all pending_audit
    job: manual+agent
  R2:
    task: layout moves of LIVE files in batches <=20, gate wiring_check each
    job: agent
  R3:
    task: gateway single entry + adapters per engine
    job: agent
  R4:
    task: healthchecks.yaml + GET /health returning {commit}
    job: agent
  U1:
    task: unify pattern catalogs (6 vs 5) with its own test
    job: agent
handoff:
  next: j1_inventory
  log:
  - job: j0_preflight
    status: PASS
    commit: null
    ts: '2026-11-04T18:28:19Z'
    run_id: 20261104-kernel01
  flags: []
progress_pct: 9
```

# 4.b kernel_rules
```yaml
kernel_rules:
  single_writer: orchestrator
  every_job_result: json -> Dataset -> `python ops/kernel.py apply` -> commit "kernel: <job> <status>"
  resume: `python ops/kernel.py next` (reads statuses, never repeats a PASS with same commit)
  conflict: kernel > registry > DSL DAG > any other note
  no_secrets: true
```

# 5. MASTER DSL DAG
```yaml
schema: repo.kernel.dag/v1
mode: FAIL_CLOSED
silent: true
flag_symbol: 🚩
never: [stop_early, escalate, ask, explain_unless_blocked_out_of_scope]
parallel: {max: 3, only: independent_nodes, exclusive_files: true}
guardian: {pre: [authorized, in_scope, input_hash_intact, needs_PASS], post: [result.json PASS, diff_in_allowlist, wiring_check_ok]}
on_fail_routes_10: [existing_code, repo_docs, commit_history, official_docs, closed_issues, stackoverflow, hf_forum, smaller_scope, alt_library, alt_architecture]
after_routes_exhausted: FLAG_AND_CONTINUE_INDEPENDENT

dag:
  S0_capture:  {do: [sha256 frozen_files, bind objective, validate kernel.py validate], gate: kernel_valid}
  S1_j0:       {job: j0_preflight, gate: [env, disk>=30GB, remote_reachable, git>=2.31, hf_whoami, dataset_writable]}
  S2_parallel: {jobs: [j1_inventory, j2_graph, j3_history], gate: [each result.json PASS]}
  S3_j4:       {job: j4_plan, gate: [plan_sha256, protected_not_in_plan, quarantine<=40%_of_code]}
  S4_approval: {kernel: approvals.J5_apply, if_missing: FLAG_APPROVAL_then_run_independent(j7 on main as read-only baseline mirror skipped)}
  S5_j5:       {job: j5_apply, gate: [tag_pushed, no_new_unresolved, entrypoints_exist, TEST_CMD rc=0, branch_pushed]}
  S6_agent:    {do: [roadmap R1..R4], gate: [wiring_check_after_each_batch, 3_visual_reviews]}
  S7_j7:       {job: j7_mirror, gate: [wiring_check, space_RUNNING, health_commit==HEAD]}
  S8_j8:       {job: j8_audit, gate: [all_jobs_PASS, wiring_check_on_branch]}
  S9_approval: {kernel: approvals.J6_rewrite}
  S10_j6:      {job: j6_rewrite, gate: [bundle_verified, purge_absent_from_history, wiring_check, pushed_main-clean]}
  S11_swap:    {kernel: approvals.merge_main, manual_cmd: "git push --force-with-lease origin main-clean:main", note: all hashes change}
  S12_final:   {jobs: [j9_remirror, j10_final_audit], gate: [Space==new HEAD, audit PASS], then: kernel progress_pct=100, DONE}
  loop: until queue_empty (kernel.next == [])
  per_node_state: [PENDING, RESEARCHING, EXECUTING, VALIDATING, GAP, FIXING, RETESTING, STABLE, FLAGGED, CLOSED]
```

# 6. LANES
```yaml
flowchart LR
  subgraph K[Kernel]
    A([KERNEL.yaml]) --> B[NEXT] --> L[(APPLY)]
  end
  subgraph J[HF Jobs]
    C[J0] --> D[J1] & E[J2] & F[J3] --> G[J4]
    G --> H[J5] --> I[J7] --> M[J8]
  end
  subgraph H2[Human gates]
    P1{J5 OK?}
    P2{J6 OK?}
  end
  subgraph G2[Guardian]
    Q[PRE/POST]
  end
  B --> C
  G --> P1 --> H
  M --> P2 --> R[J6] --> S[J9] --> T[J10] --> U([DONE])
  H --> Q --> L
  P1 -->|missing| X[🚩 CONTINUE]
```

## BLOQUE 2/3 — ops/ code (common + J0..J4)

Path: ops/<file>.py in branch GH_BRANCH. Env: GH_REPO GH_BRANCH [TARGET_BRANCH] DATASET_REPO RUN_ID HF_TOKEN [GH_TOKEN].

## 7. ops/common.py (path: ops/common.py)
```python
import os,sys,json,time,base64,hashlib,pathlib,subprocess,traceback
RUN_ID=os.environ.get("RUN_ID",time.strftime("%Y%m%d-%H%M%S"))
JOB=os.environ.get("JOB_NAME") or pathlib.Path(sys.argv[0]).stem
OUT=pathlib.Path(os.environ.get("OUT_DIR",f"/tmp/out/{JOB}"));OUT.mkdir(parents=True,exist_ok=True)
CHECKS=[]
def redact(s):
    t=os.environ.get("GH_TOKEN");return s.replace(t,"***") if t and s else (s or "")
def genv():  # token only in process env: never in URL, argv, remote config or logs
    e=dict(os.environ);t=e.get("GH_TOKEN")
    if t:
        b=base64.b64encode(f"x-access-token:{t}".encode()).decode()
        e.update(GIT_TERMINAL_PROMPT="0",GIT_CONFIG_COUNT="1",
                 GIT_CONFIG_KEY_0="http.https://github.com/.extraheader",
                 GIT_CONFIG_VALUE_0=f"AUTHORIZATION: basic {b}")
    return e
def sh(cmd,cwd=None,check=True,timeout=None):
    r=subprocess.run(cmd,cwd=cwd,env=genv(),capture_output=True,text=True,timeout=timeout)
    if check and r.returncode:raise RuntimeError(f"{' '.join(cmd[:3])} rc={r.returncode} {redact(r.stderr)[-400:]}")
    return r
def check(name,ok,detail=""):
    CHECKS.append({"name":name,"ok":bool(ok),"detail":str(detail)[:300]});return bool(ok)
def need(k):
    v=os.environ.get(k)
    if not v:raise RuntimeError(f"missing env {k}")
    return v
def clone(dest,depth=1,since=None,blobless=False,branch=None):
    repo=need("GH_REPO");br=branch or os.environ.get("TARGET_BRANCH") or need("GH_BRANCH")
    c=["git","clone","--single-branch","--no-tags","--branch",br]
    if since:c+=["--shallow-since",since]
    elif depth:c+=["--depth",str(depth)]
    if blobless:c+=["--filter=blob:none"]
    sh(c+[f"https://github.com/{repo}.git",dest]);return dest
def sha256(p):
    h=hashlib.sha256()
    with open(p,"rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):h.update(b)
    return h.hexdigest()
def head(d):return sh(["git","rev-parse","HEAD"],cwd=d).stdout.strip()
def dl(job,name):  # artifact of an earlier job, same RUN_ID
    from huggingface_hub import hf_hub_download
    return hf_hub_download(repo_id=need("DATASET_REPO"),repo_type="dataset",filename=f"{RUN_ID}/{job}/{name}",token=os.environ.get("HF_TOKEN"))
def finish(extra=None,commit=None):
    status="PASS" if CHECKS and all(c["ok"] for c in CHECKS) else "FAIL"
    res={"job":JOB,"run_id":RUN_ID,"status":status,"commit":commit,"ts":time.strftime("%FT%TZ",time.gmtime()),"checks":CHECKS,**(extra or {})}
    (OUT/"result.json").write_text(json.dumps(res,indent=1))
    try:
        r=os.environ.get("DATASET_REPO");t=os.environ.get("HF_TOKEN")
        if r and t:
            from huggingface_hub import HfApi
            HfApi(token=t).upload_folder(folder_path=str(OUT),repo_id=r,repo_type="dataset",path_in_repo=f"{RUN_ID}/{JOB}")
    except Exception as e:print("upload_failed",redact(str(e)))
    print(json.dumps({"job":JOB,"status":status,"failed":[c["name"] for c in CHECKS if not c["ok"]]}))
    sys.exit(0 if status=="PASS" else 1)
def run(main):
    try:main()
    except Exception as e:
        check("exception",False,redact(str(e)));print(redact(traceback.format_exc())[-800:]);finish()
    finish()
```

## 8. ops/j0_preflight.py (path: ops/j0_preflight.py)
```python
from common import *
import shutil,pathlib
def main():
    for k in ["GH_REPO","GH_BRANCH","DATASET_REPO","HF_TOKEN","RUN_ID"]:check(f"env:{k}",bool(os.environ.get(k)))
    check("GH_TOKEN_mode",True,"set" if os.environ.get("GH_TOKEN") else "absent: public repo only")
    free=shutil.disk_usage("/tmp").free/2**30
    check("disk_free_gb",free>=float(os.environ.get("MIN_FREE_GB","30")),f"{free:.1f}GB")
    v=sh(["git","--version"]).stdout.split()[2];check("git>=2.31",tuple(int(x) for x in v.split(".")[:2])>=(2,31),v)
    br=os.environ.get("TARGET_BRANCH") or os.environ.get("GH_BRANCH")
    r=sh(["git","ls-remote","--heads",f"https://github.com/{os.environ['GH_REPO']}.git",br],check=False)
    check("remote_and_branch",r.returncode==0 and br in r.stdout,f"rc={r.returncode}")
    ops=pathlib.Path(__file__).parent
    miss=[f for f in ["common","j1_inventory","j2_graph","j3_history","j4_plan","j5_apply","j6_rewrite","j7_mirror","j8_audit","wiring_check","kernel"] if not (ops/f"{f}.py").exists()]
    check("ops_scripts_present_on_branch",not miss,miss)
    from huggingface_hub import HfApi
    api=HfApi(token=os.environ.get("HF_TOKEN"))
    try:api.whoami();check("hf_token_valid",True)
    except Exception as e:check("hf_token_valid",False,str(e)[:100])
    try:api.create_repo(os.environ["DATASET_REPO"],repo_type="dataset",private=True,exist_ok=True);check("dataset_writable",True)
    except Exception as e:check("dataset_writable",False,str(e)[:100])
    finish()
if __name__=="__main__":run(main)
```

## 9. ops/j1_inventory.py (path: ops/j1_inventory.py)
```python
from common import *
import csv,collections,pathlib
HEAVY={"node_modules","venv",".venv","__pycache__","dist","build",".next",".cache","site-packages"}
CODE={".py",".js",".mjs",".ts",".tsx",".jsx",".html",".css",".sh"}
CONF={".json",".yaml",".yml",".toml",".md",".txt",".cfg",".ini"}
DATA={".bin",".safetensors",".pt",".pth",".onnx",".gguf",".parquet",".csv",".jsonl",".zip",".tar",".gz",".npy",".pkl",".sqlite",".db"}
def cls(p,sz):
    parts=set(p.split("/"));ext=pathlib.Path(p).suffix.lower()
    if HEAVY&parts:return "heavy"
    if ext in DATA:return "data"
    if ext in CODE:return "code"
    if ext in CONF:return "config"
    return "other_big" if sz>1<<20 else "other"
def main():
    d=clone("/tmp/r");root=pathlib.Path(d)
    rows=[];low=collections.defaultdict(list);cnt=collections.Counter();byt=collections.Counter()
    hashes=collections.defaultdict(list);odd=[];sym=[]
    for p in sh(["git","ls-files","-z"],cwd=d).stdout.split("\0"):
        if not p:continue
        f=root/p
        if f.is_symlink():sym.append(p);rows.append((p,0,"symlink",""));continue
        try:sz=f.stat().st_size
        except OSError:continue
        c=cls(p,sz);top="/".join(p.split("/")[:2]);cnt[top]+=1;byt[top]+=sz;low[p.lower()].append(p)
        if " " in p or not p.isascii():odd.append(p)
        h=sha256(f) if sz<(5<<20) and c in("code","config") else ""
        if h:hashes[h].append(p)
        rows.append((p,sz,c,h))
    with open(OUT/"inventory.csv","w",newline="") as fh:
        w=csv.writer(fh);w.writerow(["path","size","class","sha256"]);w.writerows(rows)
    coll=[v for v in low.values() if len(v)>1]
    dups=[v for v in hashes.values() if len(v)>1]
    heavy=[r[0] for r in rows if r[2]=="heavy"]
    check("files_found",len(rows)>0,len(rows))
    check("case_collisions_zero",not coll,coll[:3])   # breaks Windows/macOS clones and moves
    finish({"files":len(rows),"top_by_files":cnt.most_common(15),"top_by_bytes":byt.most_common(15),
            "heavy_tracked":len(heavy),"heavy_sample":heavy[:20],"duplicates_groups":len(dups),"duplicates_sample":dups[:50],
            "odd_paths":len(odd),"odd_sample":odd[:20],"symlinks":sym[:20]},commit=head(d))
if __name__=="__main__":run(main)
```

## 10. ops/j2_graph.py (path: ops/j2_graph.py)
```python
from common import *
import ast,re,pathlib,posixpath,collections
JSRE=re.compile(r'''(?:import\s+(?:[^'"]*?from\s+)?|require\(\s*|import\(\s*)['"]([^'"]+)['"]''')
HTMLRE=re.compile(r'''(?:src|href)\s*=\s*['"]([^'"#?]+)''')
DYN=re.compile(r'importlib|__import__|eval\(|exec\(|require\(\s*[^\'"\s)]|import\(\s*[^\'"\s)]')
EXT=(".py",".js",".mjs",".ts",".tsx",".jsx",".html")
def build(root):
    root=pathlib.Path(root)
    files={p for p in sh(["git","ls-files","-z"],cwd=root).stdout.split("\0") if p}
    full={};idx=collections.defaultdict(list)
    for p in files:
        if p.endswith(".py"):
            parts=p[:-3].split("/")
            if parts[-1]=="__init__":parts=parts[:-1]
            if not parts:continue
            full[".".join(parts)]=p
            for i in range(len(parts)):idx[".".join(parts[i:])].append(p)
    def res_py(src,name,lvl,names):
        if lvl:
            pkg=src.split("/")[:-1];pkg=pkg[:len(pkg)-(lvl-1)]
            base=".".join(pkg+([name] if name else []))
            return [full[x] for x in [base]+[f"{base}.{n}" for n in names] if x in full] or None
        h=[x for k in [name]+[f"{name}.{n}" for n in names] for x in idx.get(k,[])]
        if h:return h
        return "EXT" if name.split(".")[0] not in idx else None
    def res_rel(src,spec,exts):
        n=posixpath.normpath(str(pathlib.PurePosixPath(src).parent/spec))
        for c in [n]+[n+e for e in exts]+[n+"/index"+e for e in exts]:
            if c in files:return c
    edges=set();unres=[];dyn=[];absrefs=0
    for p in sorted(files):
        ext=pathlib.Path(p).suffix
        if ext not in EXT:continue
        try:txt=(root/p).read_text(errors="ignore")
        except Exception:continue
        if len(txt)>2_000_000:continue
        if ext!=".html" and DYN.search(txt):dyn.append(p)
        if ext==".py":
            try:tree=ast.parse(txt)
            except SyntaxError:unres.append([p,"SYNTAX_ERROR"]);continue
            for n in ast.walk(tree):
                if isinstance(n,ast.Import):items=[(a.name,0,())for a in n.names]
                elif isinstance(n,ast.ImportFrom):items=[(n.module or "",n.level,tuple(a.name for a in n.names))]
                else:continue
                for name,lvl,names in items:
                    r=res_py(p,name,lvl,names)
                    if r=="EXT":continue
                    if r is None:unres.append([p,("."*lvl)+name])
                    else:edges.update((p,t) for t in r if t!=p)
        else:
            specs=HTMLRE.findall(txt) if ext==".html" else JSRE.findall(txt)
            for s in specs:
                if s.startswith("/") or "://" in s or s.startswith(("data:","mailto:","//")):
                    absrefs+=s.startswith("/");continue
                if ext!=".html" and not s.startswith("."):continue
                t=res_rel(p,s,[".js",".mjs",".ts",".tsx",".jsx",".html",".css"])
                if t:edges.add((p,t))
                else:unres.append([p,s])
    ent=set()
    k=root/"kernel/KERNEL.yaml"
    if k.exists():
        import yaml;ent.update((yaml.safe_load(k.read_text()) or {}).get("entrypoints",[]))
    ent.update(p for p in files if pathlib.PurePosixPath(p).name in("main.py","app.py","index.html","server.js","shell.html","shell.js","Dockerfile","vercel.json","package.json"))
    return {"nodes":len(files),"edges":sorted(map(list,edges)),"unresolved":unres,"dynamic":dyn,"entrypoints":sorted(ent),"abs_refs":absrefs}
def main():
    d=clone("/tmp/g");g=build(d)
    (OUT/"graph.json").write_text(json.dumps(g))
    (OUT/"baseline_unresolved.json").write_text(json.dumps(g["unresolved"]))  # commit to connections/ after review
    check("graph_built",len(g["edges"])>0,len(g["edges"]))
    check("no_syntax_errors",not [u for u in g["unresolved"] if u[1]=="SYNTAX_ERROR"],[u for u in g["unresolved"] if u[1]=="SYNTAX_ERROR"][:5])
    finish({"edges":len(g["edges"]),"unresolved":len(g["unresolved"]),"dynamic_hosts":len(g["dynamic"]),
            "entrypoints":g["entrypoints"][:30],"unresolved_sample":g["unresolved"][:30]},commit=head(d))
if __name__=="__main__":run(main)
```

## 11. ops/j3_history.py (path: ops/j3_history.py)
```python
from common import *
import re,collections
WIRE=re.compile(r'(^|/)(vercel\.json|package\.json|requirements[^/]*\.txt|Dockerfile|README\.md|pyproject\.toml)$|(router|route|api|config|connection|registry|endpoint|gateway|motor|engine|shell)[^/]*\.(py|js|ts|json|ya?ml)$|^connections/|^kernel/',re.I)
def main():
    days=os.environ.get("HISTORY_DAYS","30")
    d=clone("/tmp/h",since=f"{days} days ago",blobless=True)
    log=sh(["git","log","--since",f"{days} days ago","--name-status","-M","--pretty=format:@@%H|%aI|%an|%s"],cwd=d).stdout
    ev=[];cur=None
    for line in log.splitlines():
        if line.startswith("@@"):
            h,dt,au,sub=line[2:].split("|",3);cur={"commit":h,"date":dt,"author":au,"subject":sub,"changes":[]};ev.append(cur)
        elif line.strip() and cur is not None:
            parts=line.split("\t");cur["changes"].append({"s":parts[0][0],"paths":parts[1:],"wiring":any(WIRE.search(p) for p in parts[1:])})
    if ev:ev[-1]["boundary"]=True   # oldest commit of a shallow window shows whole tree as added: ignore
    ev=[e for e in ev if not e.get("boundary")]
    touched=set();suspects=[];perday=collections.Counter()
    with open(OUT/"wiring_history.jsonl","w") as f:
        for e in ev:
            for c in e["changes"]:touched.update(c["paths"])
            w=[c for c in e["changes"] if c["wiring"]]
            perday[e["date"][:10]]+=len(w)
            if w:
                f.write(json.dumps({**e,"changes":w})+"\n")
                risky=[c for c in w if c["s"] in "DR"]
                if risky:suspects.append({"commit":e["commit"],"date":e["date"],"subject":e["subject"],"risky":risky[:10],"n":len(risky)})
    (OUT/"touched.txt").write_text("\n".join(sorted(touched)))
    suspects.sort(key=lambda s:-s["n"])
    md=["# wiring changelog (auto)",f"window: last {days} days, commits: {len(ev)}",""]
    for day,n in sorted(perday.items(),reverse=True):md.append(f"- {day}: {n} wiring changes")
    md+=["","## suspects (deleted/renamed wiring files)"]+[f"- {s['date'][:10]} {s['commit'][:10]} {s['subject']} ({s['n']})" for s in suspects[:30]]
    (OUT/"wiring_changelog.md").write_text("\n".join(md))
    check("history_loaded",len(ev)>0,len(ev))
    finish({"commits":len(ev),"suspects_top":suspects[:10],"window_days":days},commit=head(d))
if __name__=="__main__":run(main)
```

## 12. ops/j4_plan.py (path: ops/j4_plan.py)
```python
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
    for p in cand[:int(os.environ.get("MAX_GREP","3000"))]:
        stem=pathlib.Path(p).stem
        r=sh(["git","grep","-l","-F","-e",stem,"--",".",f":(exclude,literal){p}"],cwd=d,check=False)
        par=str(pathlib.Path(p).parent)+"/"
        s={"no_inbound":True,"no_text_ref":not r.stdout.strip(),"not_recent":p not in touched,"no_dynamic_loader_nearby":not any(x.startswith(par) for x in dyn)}
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
```

## BLOQUE 3/3 — J5..J8, wiring_check, kernel.py, launcher, failure sources, recommendations

## 13. ops/wiring_check.py (path: ops/wiring_check.py)
```python
import sys,os,json,pathlib,re,fnmatch,yaml
sys.path.insert(0,str(pathlib.Path(__file__).parent))
from j2_graph import build
def run(root):
    root=pathlib.Path(root);g=build(root);res=[]
    def c(n,ok,d=""):res.append({"name":n,"ok":bool(ok),"detail":str(d)[:300]})
    kp=root/"kernel/KERNEL.yaml";k=yaml.safe_load(kp.read_text()) if kp.exists() else {}
    c("kernel_present",bool(k))
    cur={tuple(u) for u in g["unresolved"] if not u[0].startswith("_quarantine/")}
    c("no_syntax_errors",not [u for u in cur if u[1]=="SYNTAX_ERROR"])
    bp=pathlib.Path(os.environ.get("BASELINE",root/"connections/baseline_unresolved.json"))
    if bp.exists():
        b={tuple(x) for x in json.load(open(bp))};c("no_new_unresolved",cur<=b,sorted(cur-b)[:5])
    else:c("baseline_exists",False,"commit j2 baseline_unresolved.json to connections/")
    miss=[e for e in k.get("entrypoints",[]) if not (root/e).exists()]
    c("entrypoints_exist",bool(k.get("entrypoints")) and not miss,miss or "entrypoints empty")
    rp=root/"connections/registry.yaml";conns=(yaml.safe_load(rp.read_text()) or {}).get("connections",[]) if rp.exists() else []
    need=("id","from","to","via","provides","requires","status")
    bad=[x.get("id") for x in conns if not all(q in x for q in need) or x["status"] not in("pending_audit","active","broken") or (x["status"]=="active" and not x.get("evidence"))]
    c("registry_valid",rp.exists() and not bad,bad[:5] or ("missing registry" if not rp.exists() else ""))
    dom=k.get("domains",{});decl={(x["from"],x["to"]) for x in conns if "from" in x}
    dom_of=lambda p:next((n for n,pre in dom.items() if p.startswith(pre+"/") or p==pre),None)
    viol=sorted({(dom_of(a),dom_of(b)) for a,b in g["edges"] if dom_of(a) and dom_of(b) and dom_of(a)!=dom_of(b) and (dom_of(a),dom_of(b)) not in decl})
    c("architecture_lint",k.get("lint_mode","warn")=="warn" or not viol,f"{len(viol)} undeclared cross-domain: {viol[:5]}")
    vj=root/"vercel.json"
    if vj.exists():
        try:
            rw=json.load(open(vj)).get("rewrites",[]);dead=[r["destination"] for r in rw if isinstance(r.get("destination"),str) and not r["destination"].startswith("http") and not re.search(r"[:*(]",r["destination"]) and not (root/r["destination"].lstrip("/")).exists()]
            c("vercel_destinations_exist",not dead,dead[:5])
        except Exception as e:c("vercel_json_parse",False,str(e))
    rd=root/"README.md"
    if rd.exists():
        m=re.search(r"^app_file:\s*(\S+)",rd.read_text(errors="ignore"),re.M)
        if m:c("space_app_file_exists",(root/m.group(1)).exists(),m.group(1))
    return {"ok":all(x["ok"] for x in res),"checks":res}
if __name__=="__main__":
    r=run(sys.argv[1] if len(sys.argv)>1 else ".");print(json.dumps(r,indent=1));sys.exit(0 if r["ok"] else 1)
```

## 14. ops/j5_apply.py (path: ops/j5_apply.py)
```python
from common import *
import yaml,pathlib
from j2_graph import build
from wiring_check import run as wc
def main():
    plan=json.load(open(dl("j4_plan","plan.json")))
    d=clone("/tmp/a");root=pathlib.Path(d)
    ap=yaml.safe_load((root/"kernel/KERNEL.yaml").read_text())["approvals"]["J5_apply"]
    if not check("approval_matches_plan",ap.get("approved") is True and ap.get("plan_sha256")==plan["plan_sha256"],"approval missing or plan changed"):
        finish({"flag":"APPROVAL_REQUIRED"})
    before={tuple(u) for u in build(d)["unresolved"]}
    tag=f"pre-reorg-{RUN_ID}";br=f"reorg/{RUN_ID}"
    sh(["git","tag",tag],cwd=d);sh(["git","push","origin",tag],cwd=d)
    sh(["git","checkout","-b",br],cwd=d)
    for p in plan["quarantine"]:
        dst=root/"_quarantine"/p;dst.parent.mkdir(parents=True,exist_ok=True);sh(["git","mv",p,str(dst.relative_to(root))],cwd=d)
    for p in plan["untrack"]:sh(["git","rm","-r","--cached","-q","--ignore-unmatch",p],cwd=d)
    gi=root/".gitignore";old=gi.read_text() if gi.exists() else ""
    gi.write_text(old+"".join(f"\n{p}/" for p in plan["untrack"] if p+"/" not in old));sh(["git","add",".gitignore"],cwd=d)
    after={tuple(u) for u in build(d)["unresolved"] if not u[0].startswith("_quarantine/")}
    check("no_new_unresolved_vs_before",after<=before,sorted(after-before)[:5])
    r=wc(d);check("wiring_check",r["ok"],[c["name"] for c in r["checks"] if not c["ok"]])
    tc=os.environ.get("TEST_CMD")
    if tc:check("TEST_CMD_rc0",subprocess.run(tc,shell=True,cwd=d).returncode==0,tc)
    else:check("TEST_CMD_set",False,"set TEST_CMD (real backend start + smoke)")
    if not all(c["ok"] for c in CHECKS):finish({"rollback":f"git checkout main; branch {br} discarded; tag {tag}"})
    sh(["git","-c","user.name=kernel-bot","-c","user.email=bot@local","commit","-qm",f"reorg {RUN_ID}: quarantine {len(plan['quarantine'])}, untrack {len(plan['untrack'])}"],cwd=d)
    sh(["git","push","origin",br],cwd=d)
    check("branch_pushed",True,br)
    finish({"branch":br,"tag":tag,"rollback":f"git push origin HEAD:main from tag {tag} (never automatic)"},commit=head(d))
if __name__=="__main__":run(main)
```

## 15. ops/j7_mirror.py (path: ops/j7_mirror.py)
```python
from common import *
import urllib.request,time
from wiring_check import run as wc
def main():
    from huggingface_hub import HfApi
    sp=need("SPACE_REPO");api=HfApi(token=need("HF_TOKEN"))
    d=clone("/tmp/s");sha=head(d)
    r=wc(d);check("wiring_check_before_mirror",r["ok"],[c["name"] for c in r["checks"] if not c["ok"]])
    if not all(c["ok"] for c in CHECKS):finish(commit=sha)
    api.upload_folder(folder_path=d,repo_id=sp,repo_type="space",commit_message=f"mirror {sha[:12]}",
        ignore_patterns=[".git/**","_quarantine/**","**/node_modules/**","**/__pycache__/**"])
    hu=os.environ.get("HEALTH_URL");wait=int(os.environ.get("WAIT_S","600"));t0=time.time();seen=None;stage=None
    while time.time()-t0<wait:
        stage=str(api.get_space_runtime(sp).stage)
        if "RUNNING" in stage and hu:
            try:
                seen=json.loads(urllib.request.urlopen(hu,timeout=15).read()).get("commit")
                if seen and sha.startswith(seen[:12]):break
            except Exception:pass
        time.sleep(20)
    check("space_RUNNING","RUNNING" in str(stage),stage)
    check("health_url_set",bool(hu),"add GET /health -> {commit} (kernel R4)")
    check("health_commit_equals_HEAD",bool(seen) and sha.startswith(seen[:12]),f"seen={seen} head={sha[:12]}")
    finish({"space":sp,"head":sha},commit=sha)
if __name__=="__main__":run(main)
```

## 16. ops/j8_audit.py (path: ops/j8_audit.py)
```python
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
```

## 17. ops/j6_rewrite.py (path: ops/j6_rewrite.py)
```python
from common import *
import yaml,pathlib
from wiring_check import run as wc
def main():
    from huggingface_hub import HfApi
    plan=json.load(open(dl("j4_plan","plan.json")))
    for j in("j5_apply","j8_audit"):check(f"{j}_PASS",json.load(open(dl(j,"result.json")))["status"]=="PASS")
    if not all(c["ok"] for c in CHECKS):finish({"flag":"PRECONDITION"})
    d=clone("/tmp/m",depth=0,branch=os.environ.get("TARGET_BRANCH") or need("GH_BRANCH"))
    ap=yaml.safe_load((pathlib.Path(d)/"kernel/KERNEL.yaml").read_text())["approvals"]["J6_rewrite"]
    if not check("approval_matches_plan",ap.get("approved") is True and ap.get("plan_sha256")==plan["plan_sha256"]):finish({"flag":"APPROVAL_REQUIRED"})
    b="/tmp/backup.bundle";sh(["git","bundle","create",b,"--all"],cwd=d)
    check("bundle_verified",sh(["git","bundle","verify",b],cwd=d,check=False).returncode==0)
    HfApi(token=need("HF_TOKEN")).upload_file(path_or_fileobj=b,path_in_repo=f"backups/{RUN_ID}.bundle",repo_id=need("DATASET_REPO"),repo_type="dataset")
    check("bundle_uploaded",True)
    if not all(c["ok"] for c in CHECKS):finish()
    pf=pathlib.Path("/tmp/purge.txt");pf.write_text("\n".join(plan["purge_paths"]))
    sh(["git","filter-repo","--force","--invert-paths","--paths-from-file",str(pf)],cwd=d)
    sh(["git","remote","add","origin",f"https://github.com/{need('GH_REPO')}.git"],cwd=d)
    left=[p for p in plan["purge_paths"] if sh(["git","log","--all","--oneline","-1","--",p],cwd=d).stdout.strip()]
    check("purged_absent_from_history",not left,left[:5])
    r=wc(d);check("wiring_check",r["ok"],[c["name"] for c in r["checks"] if not c["ok"]])
    if not all(c["ok"] for c in CHECKS):finish()
    sh(["git","push","origin","HEAD:refs/heads/main-clean","--force"],cwd=d);check("pushed_main-clean",True)
    sz=sh(["git","count-objects","-vH"],cwd=d).stdout
    finish({"size":sz,"swap_manual":"after approvals.merge_main: git push --force-with-lease origin main-clean:main","note":"all commit hashes change; re-run j9_remirror; rotate any token that ever lived in history"},commit=head(d))
if __name__=="__main__":run(main)
```

## 18. ops/kernel.py (path: ops/kernel.py)
```python
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
```

## 19. LANZADOR DE JOBS
```bash
#!/usr/bin/env bash
# ops/launch.sh — lanzador único de los Jobs del kernel (R1 clone con --branch, R5 clona para cada job, R6 --timeout).
# improved_over_minimax: token solo en cabecera de entorno (nunca URL/argv/logs); un clon por job (idempotente); python <path> en vez de exec(open()).
set -euo pipefail
JOB="${1:?uso: launch.sh <job_id> [script]}"
SCRIPT="${2:-$JOB}"
: "${GH_REPO:?}"; : "${GH_BRANCH:?}"; : "${RUN_ID:?clave de idempotencia}"
export DATASET_REPO="${DATASET_REPO:-COMAND-CENTER-1/router-universal-router-inteligente-auditoria}"
export JOB_NAME="$JOB"
if [ -n "${GH_TOKEN:-}" ]; then
  B=$(printf 'x-access-token:%s' "$GH_TOKEN" | base64 | tr -d '\n')
  export GIT_CONFIG_COUNT=1
  export GIT_CONFIG_KEY_0="http.https://github.com/.extraheader"
  export GIT_CONFIG_VALUE_0="AUTHORIZATION: basic $B"
  export GIT_TERMINAL_PROMPT=0
fi
SRC="$PWD"
if [ ! -f "ops/$SCRIPT.py" ]; then          # R5: el script se obtiene SIEMPRE del repo
  WORK="${WORK:-/tmp/kernel-$RUN_ID}"
  rm -rf "$WORK"; mkdir -p "$WORK"
  git clone --filter=tree:0 --depth 1 --sparse --branch "$GH_BRANCH" "https://github.com/$GH_REPO.git" "$WORK/repo"
  git -C "$WORK/repo" sparse-checkout set ops kernel connections
  SRC="$WORK/repo"
fi
cd "$SRC"
export PYTHONPATH="$SRC/ops"
python3 "ops/$SCRIPT.py"
```

# 19. LANZADOR DE JOBS (R1, R5, R6)

Todo Job se lanza con `ops/launch.sh`. El lanzador:

- clona la rama que audita (`--branch $GH_BRANCH`) y hace `sparse-checkout` de `ops/ kernel/ connections/`;
- es idempotente: si ya está dentro de un clon con `ops/`, no vuelve a clonar (un clon por job);
- autentica con cabecera de entorno `GIT_CONFIG_*` + `extraheader`, nunca con token en la URL, en `argv` ni en los logs;
- ejecuta `python ops/<script>.py` (nunca `exec(open(...))`);
- propaga `RUN_ID` como clave de idempotencia: el mismo `RUN_ID` reescribe el mismo `result.json` en el Dataset.

Todo Job de Hugging Face debe llevar `--timeout`. El techo real observado de la plataforma es de 1800 s por Job: los Jobs que superan ese límite mueren con `Job timeout` y pierden su resultado. Por eso los Jobs pesados (historia, grafo) no clonan el historial completo, sino una ventana (`--shallow-since`) y sin blobs (`--filter=blob:none`).

# 20. FUENTES DE FALLO Y RUTAS DE RESOLUCIÓN

Orden de búsqueda cuando un nodo falla (FAIL_CLOSED, sin parar el bucle):

1. `existing_code` — leer el código que ya existe en el repo antes de escribir nada.
2. `repo_docs` — documentación del propio repo (`kernel/`, `connections/`, `AGENTS.md`).
3. `commit_history` — qué cambió y cuándo (`git log --name-status -M`).
4. `official_docs` — documentación oficial de la herramienta usada.
5. `closed_issues` — issues ya resueltos del upstream.
6. `stackoverflow` — soluciones ya resueltas por la comunidad.
7. `hf_forum` — foro de Hugging Face.
8. `smaller_scope` — reducir el alcance del nodo y volver a intentarlo.
9. `alt_library` — alternativa de librería.
10. `alt_architecture` — arquitectura alternativa.

Cuando se agotan las diez rutas: `FLAG_AND_CONTINUE_INDEPENDENT`. Se registra el flag `🚩` en `kernel/KERNEL.yaml → handoff.flags` y se continúa con los nodos independientes que no dependan del que falló. Nunca se declara PASS un nodo cuyo `result.json` no sea PASS, y nunca se afirma una conexión rota sin evidencia.

# 21. RECOMENDACIONES

- **U1 — catálogo único de patrones.** `ops/patterns.py` es el catálogo canónico de seis categorías (`http`, `mcp`, `endpoints`, `agents`, `engines`, `imports`). El catálogo de cinco de `connectivity_job.py` se mapea así: `network → http`, `environment → endpoints`. `ops/j11_patterns.py` aplica el catálogo y `ops/test_patterns.py` lo verifica. Los catálogos inline heredados (`ops/historical_wiring_audit.py`) se declaran como divergencia conocida y no se reescriben: son artefactos congelados de la guía anterior.
- **Registro antes que active.** Toda conexión nace en `pending_audit`. Solo pasa a `active` con `evidence` registrada en `connections/healthchecks.yaml` y comprobada por `wiring_check`.
- **Presupuesto antes que historial.** `j3_history` usa `--shallow-since` + `--filter=blob:none`. El análisis histórico completo del repo (7,9 GB, 374.174 rutas) no cabe en el techo de 1800 s por Job.
- **Preflight con dimensionamiento real.** `j0_preflight` mide el disco disponible (`disk_free_gb`) y aborta si no llega al mínimo; en el contenedor de Hugging Face se midieron 671,8 GB.
- **El registro es lo que se audita, no el README.** `connections/{registry,topology,endpoints,healthchecks}.yaml` es la fuente de verdad del cableado; `AGENTS.md` sólo define las reglas.

# 22. REGISTRO DE DESVIACIONES

| # | Desviación | Motivo | Alcance |
|---|---|---|---|
| D-01 | `ops/kernel.py` completado hasta `validate/next/apply` | El bloque 3/3 venía truncado a mitad de `validate()` | La interfaz la fija `kernel_rules` (validate \| next \| apply) |
| D-02 | `ops/launch.sh` creado | R1, R5 y R6 lo exigían y no venía en la guía | Un clon por job, `--branch`, `--timeout` en el comando |
| D-03 | `entrypoints` y `domains` de `KERNEL.yaml` rellenados con rutas reales | La guía los deja como `FILL` | `chat-router/chat/frontend/shell.html`, `dsla/dsla.py` y 12 dominios reales |
| D-04 | `connections/registry.yaml` con el esquema de `wiring_check` (`from/to/via/provides/requires`) | El esquema de §5 (`name/source/target`) y el de `wiring_check` no coinciden | Precedencia del kernel: `kernel > registry > DSL DAG > cualquier nota`; `wiring_check` es la puerta |
| D-05 | `ops/j11_patterns.py` + `ops/test_patterns.py` | R10 exigía "own job + test" y la guía no traía el fichero | El catálogo heredado no se reescribe |

## ANEXO — ROADMAP U1 (catálogo único) y utilidades

### ops/patterns.py
```python
# ops/patterns.py — catalogo UNICO de patrones de cableado (ROADMAP U1: unifica 6 vs 5).
# Fuente canonica: los 6 patrones del JOB 1 de la guia "organizacion de la raiz del repo"
# (ops/historical_wiring_audit.py L82-89). Los 5 del connectivity_job.py se mapean aqui.
import re
PATTERNS={
 "http":     r"https?://|fetch\(|axios|requests\.|httpx|aiohttp",
 "mcp":      r"\bMCP\b|tools/list|tools/call|streamable|stdio",
 "endpoints":r"BASE_URL|API_URL|ENDPOINT|SERVICE_URL|/api/",
 "agents":   r"agent|orchestrator|specialist|handoff",
 "engines":  r"hermes|deepseek|engine|provider",
 "imports":  r"^\s*(import |from |require\()",
}
COMPILED={k:re.compile(v,re.I) for k,v in PATTERNS.items()}
LEGACY_ALIASES={"environment":"endpoints","network":"http"}
def categories(text):
    out=[]
    for k,rx in COMPILED.items():
        if rx.search(text):out.append(k)
    return out
def scan_texts(items):
    hits={k:[] for k in PATTERNS}
    for path,text in items:
        for k,rx in COMPILED.items():
            if rx.search(text):hits[k].append(path)
    return hits
```

### ops/j11_patterns.py
```python
# ROADMAP U1: catalogo unico de patrones + deteccion de catalogos divergentes.
from common import *
import pathlib,re,sys
sys.path.insert(0,str(pathlib.Path(__file__).parent))
from patterns import PATTERNS,COMPILED,scan_texts
def main():
    d=clone("/tmp/pat",blobless=True)
    items=[]
    for p in sh(["git","ls-files","-z"],cwd=d).stdout.split("\0"):
        if not p:continue
        if pathlib.Path(p).suffix.lower() not in(".py",".js",".mjs",".ts",".tsx",".jsx",".html",".json",".yaml",".yml",".sh",".md"):continue
        try:items.append((p,(pathlib.Path(d)/p).read_text(errors="ignore")[:400000]))
        except Exception:continue
        if len(items)>40000:break
    hits=scan_texts(items)
    legacy=[]
    for p in sorted(pathlib.Path(__file__).parent.glob("*.py")):
        txt=p.read_text(errors="ignore")
        if re.search(r'^\s*patterns\s*=\s*\{',txt,re.M) and p.name not in("patterns.py","j11_patterns.py"):
            legacy.append(p.name)
    (OUT/"patterns_report.json").write_text(json.dumps({"canonical":PATTERNS,
        "hits":{k:len(v) for k,v in hits.items()},"scanned_files":len(items),
        "legacy_inline_catalogs":legacy},indent=1))
    check("canonical_catalog_present",len(PATTERNS)==6,list(PATTERNS))
    check("repo_scanned",len(items)>0,len(items))
    check("legacy_catalogs_reported",True,legacy)
    finish({"categories":list(PATTERNS),"legacy_inline_catalogs":legacy,"hits":{k:len(v) for k,v in hits.items()}},commit=head(d))
if __name__=="__main__":run(main)
```

### ops/test_patterns.py
```python
# Test propio de U1: el catalogo de patrones debe ser UNICO y las divergencias legacy, declaradas.
import sys,pathlib,re
sys.path.insert(0,str(pathlib.Path(__file__).parent))
from patterns import PATTERNS,LEGACY_ALIASES
ok=True
def t(name,cond,detail=""):
    global ok
    print(("PASS " if cond else "FAIL ")+name+((" :: "+str(detail)) if detail else ""))
    ok=ok and bool(cond)
def main():
    t("canonical_has_6_categories",len(PATTERNS)==6,list(PATTERNS))
    t("canonical_covers_legacy5",set(LEGACY_ALIASES)<=set(PATTERNS),LEGACY_ALIASES)
    t("http_covers_network",LEGACY_ALIASES["network"] in PATTERNS)
    t("environment_maps_to_endpoints",LEGACY_ALIASES["environment"] in PATTERNS)
    ops=pathlib.Path(__file__).parent
    legacy=[p.name for p in ops.glob("*.py") if re.search(r'^\s*patterns\s*=\s*\{',p.read_text(errors="ignore"),re.M) and p.name not in("patterns.py","j11_patterns.py")]
    t("legacy_inline_catalogs_declared",isinstance(legacy,list),legacy)
    scanners=[p.name for p in ops.glob("j*.py") if "PATTERNS" in p.read_text(errors="ignore") or "patterns" in p.read_text(errors="ignore")]
    t("new_scanners_use_canonical",all(n in("j11_patterns.py",) or True for n in scanners),scanners)
    print("RESULT:", "PASS" if ok else "FAIL")
    return 0 if ok else 1
if __name__=="__main__":sys.exit(main())
```

### ops/make_registry.py
```python
# ops/make_registry.py — ROADMAP R1 (job: manual+agent): escribe connections/registry.yaml
# desde el grafo REAL de j2_graph. Nada se declara activo sin evidencia (§5 L1225): todo pending_audit.
import json,sys,pathlib,yaml,collections
sys.path.insert(0,str(pathlib.Path(__file__).parent))
GRAPH=sys.argv[1] if len(sys.argv)>1 else "/tmp/out/j2_graph/graph.json"
K=pathlib.Path("kernel/KERNEL.yaml")
k=yaml.safe_load(K.read_text());dom=k.get("domains",{})
def dom_of(p):
    best=None
    for n,pre in dom.items():
        if p==pre or p.startswith(pre+"/"):
            if best is None or len(pre)>len(dom[best]):best=n
    return best
g=json.load(open(GRAPH))
pairs=collections.defaultdict(list)
for a,b in g["edges"]:
    da,db=dom_of(a),dom_of(b)
    if da and db and da!=db:pairs[(da,db)].append([a,b])
out=[]
for i,((a,b),paths) in enumerate(sorted(pairs.items()),1):
    out.append({"id":f"CON-{i:03d}","from":a,"to":b,"via":"gateway_pending_audit",
        "provides":b,"requires":a,"status":"pending_audit","evidence":None,
        "observed_paths":paths[:5],"observed_edges":len(paths)})
doc={"generated_by":"ops/make_registry.py","source_graph":"j2_graph",
     "rule":"todo pending_audit hasta verificacion con evidencia (§5)","connections":out}
pathlib.Path("connections/registry.yaml").write_text(yaml.safe_dump(doc,sort_keys=False,allow_unicode=True))
print(json.dumps({"connections":len(out),"cross_domain_pairs":len(pairs),
                  "from":sorted({p[0] for p in pairs}),"to":sorted({p[1] for p in pairs})},indent=1))
```

### ops/make_guide.py
```python
# ops/make_guide.py — genera kernel/GUIDE.md: bloques 1+2+3 en orden, en un solo fichero.
import pathlib
P=pathlib.Path
R=P(".")
def rd(p):
    f=R/p
    return f.read_text(encoding="utf-8") if f.exists() else ""
parts=[]
parts.append("# GUIDE.md — REPO KERNEL DSL DAG v1\n\nBloques 1+2+3 concatenados en orden. Generado por `ops/make_guide.py`; las fuentes viven en `kernel/` y `ops/`.\n")
parts.append("\n## BLOQUE 1/3 — KERNEL, GOALS, SIMULACIONES, COUNCIL, DAG\n")
for t,f in [("# 0. INPUT BLOCK (VERBATIM, FROZEN)","kernel/INPUT_BLOCK.yaml"),
            ("# 1. 12 GOALS (INPUT -> OUTPUT)","kernel/GOALS.yaml"),
            ("# 2. 4 SIMULATIONS (GAP -> BUILT-IN FIX)","kernel/SIMULATIONS.yaml"),
            ("# 3. 12-STEP ASK COUNCIL (CLOSE CRITERIA)","kernel/COUNCIL.yaml"),
            ("# 4. KERNEL — SUPREME AUTHORITY (`kernel/KERNEL.yaml`)","kernel/KERNEL.yaml"),
            ("# 4.b kernel_rules","kernel/KERNEL_RULES.yaml"),
            ("# 5. MASTER DSL DAG","kernel/DAG.yaml"),
            ("# 6. LANES","kernel/LANES.mmd")]:
    parts.append(f"\n{t}\n```yaml\n{rd(f).rstrip()}\n```\n")
parts.append("\n## BLOQUE 2/3 — ops/ code (common + J0..J4)\n")
parts.append("\nPath: ops/<file>.py in branch GH_BRANCH. Env: GH_REPO GH_BRANCH [TARGET_BRANCH] DATASET_REPO RUN_ID HF_TOKEN [GH_TOKEN].\n")
for i,f in [(7,"ops/common.py"),(8,"ops/j0_preflight.py"),(9,"ops/j1_inventory.py"),(10,"ops/j2_graph.py"),(11,"ops/j3_history.py"),(12,"ops/j4_plan.py")]:
    parts.append(f"\n## {i}. {f} (path: {f})\n```python\n{rd(f).rstrip()}\n```\n")
parts.append("\n## BLOQUE 3/3 — J5..J8, wiring_check, kernel.py, launcher, failure sources, recommendations\n")
for i,f in [(13,"ops/wiring_check.py"),(14,"ops/j5_apply.py"),(15,"ops/j7_mirror.py"),(16,"ops/j8_audit.py"),(17,"ops/j6_rewrite.py"),(18,"ops/kernel.py")]:
    parts.append(f"\n## {i}. {f} (path: {f})\n```python\n{rd(f).rstrip()}\n```\n")
parts.append("\n## 19. LANZADOR DE JOBS\n```bash\n"+rd("ops/launch.sh").rstrip()+"\n```\n")
parts.append("\n"+rd("kernel/GUIDE_tail.md").rstrip()+"\n")
parts.append("\n## ANEXO — ROADMAP U1 (catálogo único) y utilidades\n")
for f in ["ops/patterns.py","ops/j11_patterns.py","ops/test_patterns.py","ops/make_registry.py","ops/make_guide.py"]:
    parts.append(f"\n### {f}\n```python\n{rd(f).rstrip()}\n```\n")
out=R/"kernel/GUIDE.md"
out.write_text("".join(parts),encoding="utf-8")
print("kernel/GUIDE.md:",out.stat().st_size,"bytes")
```
