# GUIDE.md — REPO KERNEL DSL DAG v1

Bloques 1+2+3 concatenados en orden. Generado por `ops/make_guide.py`; las fuentes viven en `kernel/` y `ops/`.

## BLOQUE 1/3 — KERNEL, GOALS, SIMULACIONES, COUNCIL, DAG

# 0. INPUT BLOCK (VERBATIM, FROZEN)
```yaml
input_block:
  mode: [VERBATIM, IMMUTABLE, READ_ONLY, DATA_ONLY_UNTIL_BOUND]
  frozen_files:
    - organización de la raíz del repo.md   # sha256 computed at S0, never edited
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
    R9: {what: "connections/{registry,topology,endpoints,healthchecks}.yaml", job: kernel layout}
    R10: {what: pattern catalogs 6 vs 5 not unified,      job: ROADMAP item U1 (own job + test)}
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
plan_sha256: ce3d05e23504ca53c8d8d78a861811548f46b330b7da6c03f92d60afda26129f
kernel_version: 1
authority: ROOT
autonomy:
  human_signature: NOT_REQUIRED
  authorization: AUTO_BY_GATES
forbidden_states:
- WAITING_SIGNATURE
- WAITING_AUTHORIZATION
- ASK_USER
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
- _quarantine/**
entrypoints:
- chat-router/chat/frontend/shell.html
- chat-router/chat/backend/mvp/app.py
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
  memoria: chat-router/memoria
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
    timeout: 2h
  j7_mirror:
    script: j7_mirror
    needs:
    - j5_apply
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
    timeout: 3h
  j9_remirror:
    script: j7_mirror
    needs:
    - j6_rewrite
    timeout: 1h
  j10_final_audit:
    script: j8_audit
    needs:
    - j9_remirror
    timeout: 30m
  j6b_swap:
    script: j6b_swap
    needs:
    - j6_rewrite
    timeout: 1h
  bridge:
    script: bridge
    needs:
    - j6b_swap
    timeout: 1h
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
parts_8_fallback:
- id: E1
  objetivo: reconciliar N0 y medir el clon del espejo (preparacion)
  jobs: []
  evidencia: handoff reconstruido + medida real del clon ligero (objects, MiB, packs, segundos)
  estado: CERRADO
- id: E2
  objetivo: espejo en modo base (N1)
  jobs: [j7_mirror]
  evidencia: 20261104-kernel01/j7_mirror/result.json en PASS
  estado: CERRADO
- id: E3
  objetivo: auditoria previa (N2)
  jobs: [j8_audit]
  evidencia: result.json PASS de j8_audit con PHASE=pre
  estado: CERRADO
- id: E4
  objetivo: "reescritura de historial (N3) en dos tiempos: plan + bundle y push de la rama limpia"
  jobs: [j6_rewrite]
  evidencia: result.json PASS + bundle verificado + purgado ausente del historial
  estado: EN_CURSO
- id: E5
  objetivo: candado e intercambio de la rama principal (N4)
  jobs: [j6b_swap]
  evidencia: main == tag tras el rollback previo y swap con --force-with-lease
  estado: PENDIENTE
- id: E6
  objetivo: puente central (N5)
  jobs: [bridge]
  evidencia: connections/bridge_report.json con snapshot, historial 30 d, comparacion y sondas
  estado: PENDIENTE
- id: E7
  objetivo: reespejo al Space (N6) y auditoria final (N7)
  jobs: [j7_mirror, j8_audit]
  evidencia: health del Space con commit == HEAD + result.json PASS de j8_audit PHASE=post y j10_final_audit
  estado: PENDIENTE
- id: E8
  objetivo: cableado R7/R9/R10 (N8), bitacora e informe central (N9) y cierre (N10)
  jobs: []
  evidencia: conexiones con sonda real + wiring_changelog.md + wiring_history.jsonl + README + handoff.next + progress_pct 100 * CLOSED/11
  estado: PENDIENTE
parts_8_nota: se usa si una parte vuelve a fallar; cada trozo corre como un job de HF con techo de
  30 min o en local, y deja su propia evidencia en el Dataset.
parts:
- id: P1
  objetivo: reconciliar N0 + espejo en modo base (N1)
  jobs: [j7_mirror]
  evidencia: 20261104-kernel01/j7_mirror/result.json en PASS (6170 ficheros / 110,7 MB, sin subir)
  estado: CERRADO
- id: P2
  objetivo: auditoria previa N2 + reescritura de historial N3
  jobs: [j8_audit, j6_rewrite]
  evidencia: result.json PASS de j8_audit (PHASE=pre) y de j6_rewrite con bundle y purga verificados
  estado: EN_CURSO
- id: P3
  objetivo: intercambio de la rama principal con candado N4 + puente central N5
  jobs: [j6b_swap, bridge]
  evidencia: main == tag pre-reorg-20261104-kernel01 tras el swap + connections/bridge_report.json
  estado: PENDIENTE
- id: P4
  objetivo: reespejo N6 + auditoria final N7 + cableado N8 + bitacora central N9 + cierre N10
  jobs: [j7_mirror, j8_audit]
  evidencia: health del Space con commit == HEAD + result.json PASS de j10_final_audit + connections/wiring_changelog.md + wiring_history.jsonl + README + handoff.next
  estado: PENDIENTE
parts_nota: cada parte es un job de HF con perfil cpu-upgrade (32 GB RAM + 8 vCPU) cuyo techo real es
  de 30 minutos, o bien la misma ejecucion en local (G1 ruta 2); el log del contenedor se vuelca en
  vivo tras cada fase (D-101) y cada parte deja su evidencia en el Dataset.
handoff:
  # D-108: hash CONGELADO del INPUT_BLOCK (gate j0_preflight 'input_block_sha256_intacto').
  input_block_sha256: 5c4bbb20421a9e674876d69f25fb8aaf9e67112d58a49ce3c3f527024ae83c3a
  next: j6_rewrite
  rollback:
    tag: pre-reorg-20261104-kernel01
    tag_actual: 40c8d591abaa7ff6e008e9e0801dc022a968fc6a
    main_actual: c2ad951e0ca3f672ba6eabdd4ffd88c7435174aa
    rama_respaldo: respaldo-main-pre-swap-20261104-kernel01
    nota: D-110 la rama de respaldo se creo ANTES de cualquier cambio de main; la etiqueta se
      re-apunta al main actual justo antes del intercambio para que el lease sea exacto
  log:
  - job: j0_preflight
    status: PASS
    commit: null
    ts: '2026-11-04T18:25:26Z'
    run_id: 20261104-kernel01
  - job: j1_inventory
    status: PASS
    commit: 10e3b5e6480f15140744def81e92770ed67d7714
    ts: '2026-11-04T18:46:50Z'
    run_id: 20261104-kernel01
  - job: j2_graph
    status: PASS
    commit: 9dcd456ef922ff95897ce4f10b2d604e3447e106
    ts: '2026-11-04T20:17:59Z'
    run_id: 20261104-kernel01
  - job: j3_history
    status: PASS
    commit: 545da638bafd1cc2753f11ae8692e9b5bc96f611
    ts: '2026-11-04T19:06:00Z'
    run_id: 20261104-kernel01
  - job: j4_plan
    status: PASS
    commit: 1b6837b505a5d7ace17437905739b8af3056cf8a
    ts: '2026-11-04T21:38:00Z'
    run_id: 20261104-kernel01
  - job: j11_patterns
    status: PASS
    commit: 4162ced5ea7f1ca59b0e0dc17156655402406ffc
    ts: '2026-11-04T18:50:49Z'
    run_id: 20261104-kernel01
  - job: j5_apply
    status: PASS
    commit: e0773eb4f15a972c4f11568908ca97893eddf5fd
    ts: '2026-11-05T05:30:08Z'
    run_id: 20261104-kernel01
  - job: j7_mirror
    status: PASS
    commit: 32892dd3f4347e7c1ca6bd5518d0cd3c33276127
    ts: '2026-11-06T05:16:12Z'
    run_id: 20261104-kernel01
    mode: baseline
    checks: [registry_valid, baseline_only_no_upload, space_RUNNING]
    baseline: {files: 6170, bytes: 110654589}
    nota: D-104 REUSE_CLONE (clon ya materializado) en vez de un clon ligero atascado
  - job: j8_audit
    status: PASS
    commit: 6d072e806768356b9c7a6dd1e2e359fe43f3a904
    ts: '2026-11-06T05:22:37Z'
    run_id: 20261104-kernel01
    phase: pre
    checks: [j0_preflight_PASS, j1_inventory_PASS, j2_graph_PASS, j3_history_PASS, j4_plan_PASS, j11_patterns_PASS, j5_apply_PASS, j7_mirror_PASS, wiring_check_on_target]
    run_id: 20261104-kernel01
  - job: j6_rewrite
    status: FAIL
    commit: null
    ts: '2026-11-05T07:52:19Z'
    run_id: 20261104-kernel01
  - job: j9_remirror
    status: FAIL
    commit: bb9e4c8088cfe4be35a91dfdc669b9a171200885
    ts: '2026-11-05T08:06:14Z'
    run_id: 20261104-kernel01
  - job: backend_smoke
    status: PASS
    commit: null
    ts: '2026-11-05T05:29:51Z'
    run_id: 20261104-kernel01
  flags:
  - '🚩 j6_rewrite EN_CURSO (bundle + purga)'
  - '🚩 j9_remirror FAIL'
  - '🚩 j10_final_audit MISSING'
progress_pct: 73
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
autonomy: {human_signature: NOT_REQUIRED, authorization: AUTO_BY_GATES}
forbidden_states: [WAITING_SIGNATURE, WAITING_AUTHORIZATION, ASK_USER]
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
  S5_j5:       {job: j5_apply, gate: [tag_pushed, no_new_unresolved, entrypoints_exist, TEST_CMD rc=0, branch_pushed]}
  S6_agent:    {do: [roadmap R1..R4], gate: [wiring_check_after_each_batch, 3_visual_reviews]}
  S7_j7:       {job: j7_mirror, gate: [wiring_check, space_RUNNING, health_commit==HEAD]}
  S8_j8:       {job: j8_audit, gate: [all_jobs_PASS, wiring_check_on_branch]}
  S10_j6:      {job: j6_rewrite, gate: [bundle_verified, purge_absent_from_history, wiring_check, pushed_main-clean]}
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
import os,sys,json,time,base64,hashlib,pathlib,subprocess,traceback,shutil
RUN_ID=os.environ.get("RUN_ID",time.strftime("%Y%m%d-%H%M%S"))
JOB=os.environ.get("JOB_NAME") or pathlib.Path(sys.argv[0]).stem
WORK=os.environ.get("WORK_DIR","/workspace/work")
def wd(*p):return os.path.join(WORK,*p)
OUT=pathlib.Path(os.environ.get("OUT_DIR",wd("out",JOB)));OUT.mkdir(parents=True,exist_ok=True)
_CLONES=[]
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
def sh(cmd,cwd=None,check=True,timeout=None,env=None):
    # D-56: `env` permite fijar credenciales por destino (p.ej. el push al repo del Space
    # en huggingface.co) sin tocar el resto del entorno ni pasar el token por argv.
    e=genv()
    if env:e.update(env)
    r=subprocess.run(cmd,cwd=cwd,env=e,capture_output=True,text=True,timeout=timeout)
    if check and r.returncode:raise RuntimeError(f"{' '.join(cmd[:6])} rc={r.returncode} {redact(r.stderr)[-400:]}")
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
    # D-13 (rutas §20: 1 existing_code + 8 smaller_scope): clon idempotente.
    # Si el destino ya es un repo git se reutiliza (fetch + reset); si existe y no es
    # repo es scratch y se regenera. Evita el rc=128 "destination path already exists"
    # que tumbaba j4_plan.
    _CLONES.append(dest)
    if os.path.isdir(os.path.join(dest,".git")):
        sh(["git","-C",dest,"fetch","--depth","1","--no-tags","origin",br],check=False)
        sh(["git","-C",dest,"checkout","-B",br,"FETCH_HEAD"],check=False)
        sh(["git","-C",dest,"reset","--hard","FETCH_HEAD"],check=False)
        return dest
    # D-97/G3: en NFS el borrado puede fallar (ficheros .nfs* abiertos). Se intenta borrar y,
    # si sigue existiendo, se usa un destino UNICO (nunca /tmp, nunca dos clones a la vez).
    shutil.rmtree(dest,ignore_errors=True)
    if os.path.exists(dest):dest=f"{dest}-{os.getpid()}"
    sh(c+[f"https://github.com/{repo}.git",dest]);return dest
def sha256(p):
    h=hashlib.sha256()
    with open(p,"rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):h.update(b)
    return h.hexdigest()
def head(d):return sh(["git","rev-parse","HEAD"],cwd=d).stdout.strip()
def _ds_url(job,name):
    return f"https://huggingface.co/datasets/{need('DATASET_REPO')}/resolve/main/{RUN_ID}/{job}/{name}"
def dl(job,name):  # artifact of an earlier job, same RUN_ID
    # D-91: huggingface_hub es una dependencia opcional. Si no esta instalada (sandbox sin PyPI),
    # el artefacto se baja por REST con el token SOLO en la cabecera. Mismo bytes, mismo path.
    try:
        from huggingface_hub import hf_hub_download
        return hf_hub_download(repo_id=need("DATASET_REPO"),repo_type="dataset",filename=f"{RUN_ID}/{job}/{name}",token=os.environ.get("HF_TOKEN"))
    except ImportError:
        import urllib.request,tempfile
        req=urllib.request.Request(_ds_url(job,name),headers={"Authorization":"Bearer "+os.environ.get("HF_TOKEN","")})
        with urllib.request.urlopen(req,timeout=300) as r: data=r.read()
        fd,path=tempfile.mkstemp(prefix=job+"_");os.write(fd,data);os.close(fd);return path
def _ds_upload_fallback(out_dir,repo,token):
    """D-91: publica los artefactos del job en el Dataset por la API REST de HF.
    Token SOLO en cabecera; el cuerpo va en base64 (nunca en logs ni en argv)."""
    import base64,json as _j,urllib.request
    out=pathlib.Path(out_dir);ops=[]
    for f in sorted(out.rglob("*")):
        if f.is_file():
            rel=f.relative_to(out).as_posix()
            ops.append({"operation":"addOrUpdate","path":f"{RUN_ID}/{JOB}/{rel}",
                        "content":base64.b64encode(f.read_bytes()).decode()})
    if not ops:return
    body=_j.dumps({"commit_message":f"{JOB} {RUN_ID}","operations":ops}).encode()
    req=urllib.request.Request(f"https://huggingface.co/api/datasets/{repo}/commit",data=body,method="POST",
        headers={"Authorization":"Bearer "+token,"Content-Type":"application/json"})
    with urllib.request.urlopen(req,timeout=300) as r: r.read()
def finish(extra=None,commit=None):
    status="PASS" if CHECKS and all(c["ok"] for c in CHECKS) else "FAIL"
    res={"job":JOB,"run_id":RUN_ID,"status":status,"commit":commit,"ts":time.strftime("%FT%TZ",time.gmtime()),"checks":CHECKS,**(extra or {})}
    (OUT/"result.json").write_text(json.dumps(res,indent=1))
    try:
        r=os.environ.get("DATASET_REPO");t=os.environ.get("HF_TOKEN")
        if r and t:
            try:
                from huggingface_hub import HfApi
                HfApi(token=t).upload_folder(folder_path=str(OUT),repo_id=r,repo_type="dataset",path_in_repo=f"{RUN_ID}/{JOB}")
            except ImportError:
                _ds_upload_fallback(OUT,r,t)   # D-91: REST commit API (mismo repo, mismos paths)
    except Exception as e:print("upload_failed",redact(str(e)))
    print(json.dumps({"job":JOB,"status":status,"failed":[c["name"] for c in CHECKS if not c["ok"]]}))
    cleanup()
    sys.exit(0 if status=="PASS" else 1)
def cleanup():
    # G3: el clon de este job se borra SIEMPRE (tambien en fallo). Sin esto el scratch
    # acumula clones de 7 GB y el siguiente job falla por disco/rc=128.
    for d in list(_CLONES):
        shutil.rmtree(d,ignore_errors=True)
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
    free=shutil.disk_usage(os.environ.get("WORK_DIR","/workspace/work")).free/2**30   # G2/G3: el disco que se mide es el del scratch real
    check("disk_free_gb",free>=float(os.environ.get("MIN_FREE_GB","30")),f"{free:.1f}GB")
    v=sh(["git","--version"]).stdout.split()[2];check("git>=2.31",tuple(int(x) for x in v.split(".")[:2])>=(2,31),v)
    br=os.environ.get("TARGET_BRANCH") or os.environ.get("GH_BRANCH")
    r=sh(["git","ls-remote","--heads",f"https://github.com/{os.environ['GH_REPO']}.git",br],check=False)
    check("remote_and_branch",r.returncode==0 and br in r.stdout,f"rc={r.returncode}")
    ops=pathlib.Path(__file__).parent
    # D-108: los jobs del DAG v3 tambien deben estar en la rama.
    miss=[f for f in ["common","j1_inventory","j2_graph","j3_history","j4_plan","j5_apply","j6_rewrite","j6b_swap","j7_mirror","j8_audit","j9_remirror","j10_final_audit","bridge","wiring_check","kernel"] if not (ops/f"{f}.py").exists()]
    check("ops_scripts_present_on_branch",not miss,miss)
    # D-31: el bloque de entrada esta CONGELADO (freeze/VERBATIM). Se valida su SHA-256
    # contra el que registra el kernel (handoff.input_block_sha256): si cambia, el job falla.
    import hashlib as _h
    ibp=pathlib.Path(os.environ.get("KERNEL_DIR","kernel"))/"INPUT_BLOCK.yaml"
    try:
        cur=_h.sha256(ibp.read_bytes()).hexdigest()
        import yaml as _y
        rec=(_y.safe_load(pathlib.Path(os.environ.get("KERNEL_DIR","kernel")+"/KERNEL.yaml").read_text())
             .get("handoff",{}).get("input_block_sha256"))
        check("input_block_sha256_intacto",bool(rec) and cur==rec,f"actual={cur[:12]} registrado={(rec or '-')[:12]}")
    except Exception as e:check("input_block_sha256_intacto",False,str(e)[:120])
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
    d=clone(wd("r"));root=pathlib.Path(d)
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
# D-08 (ruta "smaller_scope" del DAG): el codigo de TERCEROS vendorizado, lo descartado y las
# copias duplicadas no son cableado propio -> sus errores de sintaxis se INFORMAN pero no BLOQUEAN.
# Todo lo demas (codigo propio y _quarantine/) sigueHaving que parsear para pasar el gate.
# D-40: al mover chat-router/agentes -> agents/ los prefijos de TERCEROS deben seguir casando
# con la nueva ubicacion (si no, 38.405 referencias vendorizadas pasan a "propias" y bloquean).
VENDORED=("agentes-listos/","agentes/frameworks/","agentes/investigacion/",
          "agents/agentes-listos/","agents/frameworks/","agents/investigacion/",
          "chatbot/componentes/","memoria/componentes/","otros/descartados/","otros/Prueba/","descarga-copia/")
def es_tercero(p):return any(k in p for k in VENDORED) or p.startswith("_quarantine/")
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
    d=clone(wd("g"));g=build(d)
    (OUT/"graph.json").write_text(json.dumps(g))
    (OUT/"baseline_unresolved.json").write_text(json.dumps(g["unresolved"]))  # commit to connections/ after review
    check("graph_built",len(g["edges"])>0,len(g["edges"]))
    syn=[u for u in g["unresolved"] if u[1]=="SYNTAX_ERROR"]
    propios=[u for u in syn if not es_tercero(u[0])]
    check("no_syntax_errors",not propios,propios[:5])
    check("vendored_syntax_errors_reported",True,f"{len(syn)-len(propios)} errores en codigo de terceros (informativo, no bloquea)")
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
    d=clone(wd("h"),since=f"{days} days ago",blobless=True)
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
    d=clone(wd("p"));kp=pathlib.Path(d)/"kernel/KERNEL.yaml"
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
        pf=wd("j4_stems.txt")
        pathlib.Path(pf).write_text("\n".join(sorted({pathlib.Path(p).stem for p in pats if pathlib.Path(p).stem}))+"\n")
        # fase 1: ficheros que contienen algun stem (salida corta, sin -o)
        r1=sh(["git","grep","-I","-l","-F","-f",pf,"--","."],cwd=d,check=False)
        mfiles=[x for x in r1.stdout.splitlines() if x]
        # fase 2: solo sobre esos ficheros, con -o para saber que stem aparece donde
        if mfiles:
            ff=wd("j4_files.txt")
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
```

## BLOQUE 3/3 — J5..J8, wiring_check, kernel.py, launcher, failure sources, recommendations

## 13. ops/wiring_check.py (path: ops/wiring_check.py)
```python
import sys,os,json,pathlib,re,fnmatch,yaml
sys.path.insert(0,str(pathlib.Path(__file__).parent))
from j2_graph import build
# D-18/D-25: prefijos del codigo de TERCEROS vendorizado. Se evaluan en el codigo propio y
# en las referencias nuevas (los errores de terceros se INFORMAN, no bloquean).
# D-40: al mover chat-router/agentes -> agents/ los prefijos de TERCEROS deben seguir casando
# con la nueva ubicacion (si no, 38.405 referencias vendorizadas pasan a "propias" y bloquean).
VENDORED=("agentes-listos/","agentes/frameworks/","agentes/investigacion/",
          "agents/agentes-listos/","agents/frameworks/","agents/investigacion/",
          "chatbot/componentes/","memoria/componentes/","otros/descartados/","otros/Prueba/","descarga-copia/")
es_tercero=lambda p:any(k in p for k in VENDORED)
def run(root,graph=None):
    # D-39: si el job ya construyo el grafo, se reutiliza (el build son ~10 min sobre 374k ficheros).
    root=pathlib.Path(root);g=graph if graph is not None else build(root);res=[]
    def c(n,ok,d=""):res.append({"name":n,"ok":bool(ok),"detail":str(d)[:300]})
    kp=root/"kernel/KERNEL.yaml";k=yaml.safe_load(kp.read_text()) if kp.exists() else {}
    c("kernel_present",bool(k))
    cur={tuple(u) for u in g["unresolved"] if not u[0].startswith("_quarantine/")}
    # D-18 (misma regla que D-08 en j2_graph): los errores de sintaxis del codigo de TERCEROS
    # vendorizado se INFORMAN pero no BLOQUEAN el gate; el codigo propio sigue bloqueando.
    syn_all=[u for u in cur if u[1]=="SYNTAX_ERROR"]
    syn_own=[u for u in syn_all if not es_tercero(u[0])]
    c("no_syntax_errors",not syn_own,f"{len(syn_all)} de terceros (informativo), {len(syn_own)} propios")
    c("third_party_syntax_reported",True,f"{len(syn_all)} errores de sintaxis en codigo de terceros")
    bp=pathlib.Path(os.environ.get("BASELINE",root/"connections/baseline_unresolved.json"))
    if bp.exists():
        b={tuple(x) for x in json.load(open(bp))}
        # D-25: el untrack de los 37 directorios build/ (plan de j4) deja sin resolver referencias
        # del codigo de TERCEROS vendorizado (que importaba esos artefactos). Misma regla que D-18:
        # las referencias nuevas de terceros se INFORMAN; solo las del codigo propio bloquean.
        # D-41: el baseline esta indexado por ruta y un renombrado (lote R2) lo invalidaba.
        # Se compara por (basename, destino): el renombrado conserva el nombre de fichero, asi que
        # la comparacion sigue detectando referencias NUEVAS sin penalizar los movimientos.
        nb={(pathlib.Path(x[0]).name,x[1]) for x in b}
        new_all=sorted(cur-b)
        new_own=[u for u in new_all if not es_tercero(u[0]) and (pathlib.Path(u[0]).name,u[1]) not in nb]
        c("no_new_unresolved",not new_own,f"{len(new_all)} de terceros (informativo), {len(new_own)} propios: {new_own[:3]}")
        c("third_party_unresolved_reported",True,f"{len(new_all)} referencias nuevas en codigo de terceros")
    else:c("baseline_exists",False,"commit j2 baseline_unresolved.json to connections/")
    miss=[e for e in k.get("entrypoints",[]) if not (root/e).exists()]
    c("entrypoints_exist",bool(k.get("entrypoints")) and not miss,(miss or f"{len(k.get('entrypoints',[]))} entrypoints presentes"))
    rp=root/"connections/registry.yaml";conns=(yaml.safe_load(rp.read_text()) or {}).get("connections",[]) if rp.exists() else []
    # D-37: la guia §5 fija los 11 campos obligatorios de cada conexion del registro oficial.
    need=("id","name","source","target","protocol","direction","endpoint","status","dependencies",
          "verification","notes","from","to","via","provides","requires")
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
from wiring_check import run as wc, es_tercero
def main():
    plan=json.load(open(dl("j4_plan","plan.json")))
    d=clone(os.path.join(os.environ.get("WORK_DIR","/workspace/work"),"a"));root=pathlib.Path(d)   # G2: scratch en WORK_DIR (NAS)
    # G4: NO hay bloque `approvals` ni firma humana (autonomy.human_signature=NOT_REQUIRED).
    # El gate es el SHA256 del plan publicado en el Dataset: si el plan cambio, el job no corre.
    ker=yaml.safe_load((root/"kernel/KERNEL.yaml").read_text())
    if not check("plan_sha256_matches",ker.get("plan_sha256")==plan["plan_sha256"],f"kernel={str(ker.get('plan_sha256'))[:12]} plan={str(plan['plan_sha256'])[:12]}"):
        finish({"flag":"PLAN_CHANGED"})
    # D-26: cache del conjunto "before" indexado por el sha del commit. El build del grafo
    # (~10 min sobre 374.205 ficheros) es determinista: cachear no altera el resultado.
    sha0=head(d);cf=pathlib.Path(os.path.join(os.environ.get("WORK_DIR","/workspace/work"),"before_unresolved.json"))
    if cf.exists() and json.loads(cf.read_text()).get("sha")==sha0:
        before={tuple(x) for x in json.loads(cf.read_text())["u"]};check("before_cached",True,f"cache hit {sha0[:12]}")
    else:
        before={tuple(u) for u in build(d)["unresolved"] if not u[0].startswith("_quarantine/")}
        cf.write_text(json.dumps({"sha":sha0,"u":[list(x) for x in before]}));check("before_cached",True,f"computed {sha0[:12]}")
    tag=f"pre-reorg-{RUN_ID}";br=f"reorg/{RUN_ID}"
    # D-33: el job es REEJECUTABLE. tag/branch/movimientos/commit ya hechos no pueden fallar:
    #   - tag: si existe se reapunta al HEAD (es el punto de rollback) y se re-pushea con --force
    #   - branch: checkout -B (no -b) para reutilizar la rama existente
    #   - git mv: si el path ya no existe (movido en una ejecucion previa) se ignora
    #   - commit: --allow-empty para que una reejecucion sin cambios no rompa la cadena
    # D-48: la tag ya existe en remoto (reejecucion) -> el push se hace SIEMPRE con --force:
    # sin el, el push se rechaza ("already exists") y el job muere con rc=1.
    if sh(["git","rev-parse","-q","--verify",f"refs/tags/{tag}"],cwd=d,check=False).stdout.strip():
        sh(["git","tag","-f",tag],cwd=d)
    else:
        sh(["git","tag",tag],cwd=d)
    sh(["git","push","origin","--force",tag],cwd=d)
    sh(["git","checkout","-B",br],cwd=d)
    for p in plan["quarantine"]:
        dst=root/"_quarantine"/p;dst.parent.mkdir(parents=True,exist_ok=True)
        sh(["git","mv",p,str(dst.relative_to(root))],cwd=d,check=False)
    for p in plan["untrack"]:sh(["git","rm","-r","--cached","-q","--ignore-unmatch",p],cwd=d)
    gi=root/".gitignore";old=gi.read_text() if gi.exists() else ""
    gi.write_text(old+"".join(f"\n{p}/" for p in plan["untrack"] if p+"/" not in old));sh(["git","add",".gitignore"],cwd=d)
    g_after=build(d)  # D-39: un solo build; su resultado se reutiliza en wiring_check
    after={tuple(u) for u in g_after["unresolved"] if not u[0].startswith("_quarantine/")}
    # D-25: las referencias nuevas que deja el untrack de los 37 directorios build/ estan en el
    # codigo de TERCEROS vendorizado (misma regla que D-18): se INFORMAN; solo el codigo propio bloquea.
    new_all=sorted(after-before);new_own=[u for u in new_all if not es_tercero(u[0])]
    check("no_new_unresolved_vs_before",not new_own,f"{len(new_all)} de terceros (informativo), {len(new_own)} propios: {new_own[:3]}")
    check("third_party_unresolved_reported",True,f"{len(new_all)} referencias nuevas en codigo de terceros")
    # D-24: la guia declara el gate entrypoints_exist en S5_j5 pero su codigo no lo implementaba.
    eps=(yaml.safe_load((root/"kernel/KERNEL.yaml").read_text()).get("entrypoints") or [])
    miss=[p for p in eps if not (root/p).exists()]
    check("entrypoints_exist",not miss,miss[:5])
    r=wc(d,g_after);check("wiring_check",r["ok"],[c["name"] for c in r["checks"] if not c["ok"]])
    tc=os.environ.get("TEST_CMD")
    if tc:
        # D-36: el Space RIU se redespliega cada ~60 s (autosync) -> /health devuelve 503 durante
        # el redesplie. Se reintenta hasta 5 veces (30 s) antes de dar el gate por fallido.
        rc=1
        for _try in range(5):
            rc=subprocess.run(tc,shell=True,cwd=d).returncode
            if rc==0: break
            time.sleep(30)
        check("TEST_CMD_rc0",rc==0,tc)
    else:check("TEST_CMD_set",False,"set TEST_CMD (real backend start + smoke)")
    if not all(c["ok"] for c in CHECKS):finish({"rollback":f"git checkout main; branch {br} discarded; tag {tag}"})
    sh(["git","-c","user.name=kernel-bot","-c","user.email=bot@local","commit","--allow-empty","-qm",f"reorg {RUN_ID}: quarantine {len(plan['quarantine'])}, untrack {len(plan['untrack'])}"],cwd=d)
    sh(["git","push","origin",br],cwd=d)
    check("branch_pushed",True,br)
    finish({"branch":br,"tag":tag,"rollback":f"git push origin HEAD:main from tag {tag} (never automatic)"},commit=head(d))
if __name__=="__main__":run(main)
```

## 15. ops/j7_mirror.py (path: ops/j7_mirror.py)
```python
from common import *
import base64
import urllib.request,time
from wiring_check import run as wc
def _space_stage(sp,token):
    """D-91: stage del Space. huggingface_hub si esta disponible; si no, REST (mismo dato)."""
    try:
        from huggingface_hub import HfApi
        return str(HfApi(token=token).get_space_runtime(sp).stage)
    except ImportError:
        import json as _j
        req=urllib.request.Request(f"https://huggingface.co/api/spaces/{sp}",
            headers={"Authorization":"Bearer "+token})
        with urllib.request.urlopen(req,timeout=60) as r:
            return str((_j.loads(r.read()).get("runtime") or {}).get("stage",""))
def _tree_bytes_via_api(sha, repo=None):
    """D-108: suma de 'size' de los blobs del arbol via la API de GitHub, POR SUBARBOLES.
    Devuelve 0 si algun subarbol viene truncado (no se inventa el dato)."""
    import urllib.request as _u, json as _j, os as _o
    repo=repo or _o.environ.get("GH_REPO");tok=_o.environ.get("GH_TOKEN","")
    def _get(url):
        r=_u.Request(url,headers={"Authorization":"Bearer "+tok,"User-Agent":"kernel-mirror/1.0"})
        return _j.loads(_u.urlopen(r,timeout=60).read())
    try:
        root=_get(f"https://api.github.com/repos/{repo}/git/trees/{sha}")
        total=0
        for e in root.get("tree",[]):
            if e.get("type")!="tree":continue
            t=_get(f"https://api.github.com/repos/{repo}/git/trees/{e['sha']}?recursive=1")
            if t.get("truncated"):return 0     # dato incompleto -> no se reporta
            total+=sum(x.get("size",0) for x in t.get("tree",[]) if x.get("type")=="blob")
        return total
    except Exception:
        return 0
def main():
    sp=need("SPACE_REPO");token=need("HF_TOKEN")
    # D-92: `br` se define SIEMPRE. Antes solo existia en el modo ligero -> en el push real
    # (`git show <br>:.gitattributes`) salia NameError y el job moria.
    br=os.environ.get("TARGET_BRANCH") or need("GH_BRANCH")
    LIGHT=os.environ.get("MIRROR_LIGHT")=="1"
    if LIGHT:
        # D-75: modo ligero. El sandbox reinicia /tmp cada 15-20 min y se lleva el clon de 18 GB;
        # en modo ligero el clon es `--filter=blob:none --no-checkout` (arbol sin working tree) y el
        # gate previo se evalua sobre el YAML del registro (el predicado exacto de wiring_check).
        import shutil as _sh
        # G2: scratch en WORK_DIR (NAS). D-97: dir UNICO por ejecucion: en NFS el borrado de
        # un scratch puede dejar ficheros .nfs* abiertos y el clon siguiente fallaria con
        # "destination path already exists".
        d=os.path.join(os.environ.get("WORK_DIR","/workspace/work"),"sl-%d"%os.getpid())
        reuse=os.environ.get("REUSE_CLONE","").strip()
        if reuse and os.path.isdir(os.path.join(reuse,".git")):
            # D-104: REUSE_CLONE reutiliza un clon YA materializado (el del sandbox, 373.422
            # ficheros). Motivo: el clon ligero en frio se cuelga con este repo (medido: 45.577
            # objetos / 17,85 MiB y 7 minutos sin crecer) porque transfiere muchos packs
            # pequenos. Reutilizar da el MISMO arbol git, evita un segundo clon pesado (G3) y
            # hace el job idempotente: si ya hay clon, se usa.
            d=reuse
        else:
            if os.path.isdir(d): _sh.rmtree(d,ignore_errors=True)
            # El token va SOLO en la cabecera extraheader que genera common.genv()
            # (nunca en argv, URL ni logs). Nada de .decode() sobre texto.
            env3=genv()
            sh(["git","clone","--single-branch","--no-tags","--filter=blob:none","--no-checkout",
                "--depth","1","--branch",br,f"https://github.com/{need('GH_REPO')}.git",d],env=env3)
        sha=head(d)
        import yaml as _yaml
        # D-76: en el clon ligero (filtrado) la lectura de blobs lanza la descarga del blob y
        # falla ("failed to unpack tree object"). El registro se lee del REPO LOCAL, que si tiene
        # los objetos completos, y el .gitattributes del Space se baja por la API.
        # D-78: el clon local del sandbox tambien es filtrado y su descarga de blobs falla
        # ("failed to unpack tree object"), asi que el registro se lee del fichero ya
        # materializado en el repositorio local (main; la rama solo añade movimientos de
        # ficheros, no toca el registro).
        reg_p=os.path.join(d,"connections","registry.yaml")
        reg_txt=open(reg_p if os.path.exists(reg_p) else "connections/registry.yaml",errors="ignore").read()
        reg=_yaml.safe_load(reg_txt) or {}
        conns=reg.get("connections",[])
        need_f=("id","name","source","target","protocol","direction","endpoint","status","dependencies",
                "verification","notes","from","to","via","provides","requires")
        bad=[x.get("id") for x in conns if not all(q in x for q in need_f)
             or x["status"] not in ("pending_audit","active","broken")
             or (x["status"]=="active" and not x.get("evidence"))]
        check("registry_valid",not bad,bad[:5] or "")
    else:
        d=clone(os.path.join(os.environ.get("WORK_DIR","/workspace/work"),"s"));sha=head(d)
        r=wc(d);check("wiring_check_before_mirror",r["ok"],[c["name"] for c in r["checks"] if not c["ok"]])
    if not all(c["ok"] for c in CHECKS):finish(commit=sha)
    IGN=[".git/**","_quarantine/**","**/node_modules/**","**/__pycache__/**",
        # D-06: fuera del espejo el codigo de terceros vendorizado (315.949 ficheros, 84% del repo).
        "chat-router/agentes/agentes-listos/**","chat-router/agentes/frameworks/**","chat-router/agentes/investigacion/**",
        "chat-router/chatbot/componentes/**","chat-router/memoria/componentes/**","chat-router/otros/descartados/**",
        "chat-router/otros/Prueba/**","chat-router/motores/motores/descarga-copia/**",
        # D-58: el limite del endpoint de HF es de 20.000 ficheros por repo y el espejo
        # llegaba a 20.008. kernel/ y ops/ son el utillaje de despliegue (no runtime del
        # Space): excluirlos deja el espejo en 19.961 ficheros y 31 de margen.
        "kernel/**","ops/**",
        # D-62: `router-mvp/router-componentes/` son 14.602 ficheros de bibliotecas de terceros
        # vendorizadas (fastapi, cryptography, pydantic, pyyaml, huggingface_hub, MCP SDKs...).
        # El Space instala sus dependencias por pip: no las necesita en runtime y son las que
        # hacen que el espejo (20.775) rebase el limite de 20.000 ficheros del repo del Space.
        "router-mvp/router-componentes/**"]
    if os.environ.get("MIRROR_BASELINE")=="1":
        # D-16/D-20: modo baseline read-only que exige el DAG en S4_approval.if_missing.
        # D-20: la env se llama MIRROR_BASELINE y no BASELINE porque wiring_check usa BASELINE como RUTA del baseline.
        # ("j7 on main as read-only baseline, mirror skipped"): calcula lo que se mirroriaria
        # y el estado del Space, SIN subir nada. El mirror real queda para j9_remirror.
        n=0;sz=0;pfx=[p[:-3] for p in IGN if p.endswith("/**")]
        # D-93: el baseline se cuenta sobre el ARBOL GIT (`ls-tree -r -l`), no sobre el working
        # tree: en el clon ligero (--no-checkout) no hay working tree y el recorrido daria 0
        # ficheros (mentira). El arbol da el conjunto EXACTO de ficheros versionados a espejar.
        # D-94: las exclusiones "**/X" NUNCA casaban con startswith (comparaba literally "**/"):
        # node_modules y __pycache__ no se excluian. Ahora se comparan por segmento.
        def _excluded(path):
            for p in pfx:
                if p.startswith("**/"):
                    q=p[3:]
                    if path==q or path.startswith(q+"/") or ("/"+q+"/") in path:return True
                elif path.startswith(p):return True
            return False
        # D-108: SIN "-l". Medido: con "-l" git pide el TAMANO de cada blob y en un clon PARCIAL
        # dispara la descarga perezosa de los 373.420 blobs (packs de 2-3 kB): el job se cuelga
        # hasta el techo de 30 min. "git ls-tree -r" (sin -l) -> 2,3 s y el mismo conjunto.
        # El BYTE TOTAL se pide aparte a la API de arbol de GitHub (por subarboles NO truncados).
        for line in sh(["git","-C",d,"ls-tree","-r",sha],check=False).stdout.splitlines():
            if "\t" not in line:continue
            meta,path=line.split("\t",1);parts=meta.split()
            if len(parts)<3:continue
            if _excluded(path):continue
            n+=1
        sz=_tree_bytes_via_api(sha)
        stage=_space_stage(sp,token)
        check("baseline_only_no_upload",True,f"{n} ficheros, {sz/1e6:.1f} MB (sin subir)")
        check("baseline_tree_api_not_truncated",sz>0,f"{sz} bytes via API de arbol (0 = subarbol truncado)")
        check("space_RUNNING","RUNNING" in stage,stage)
        finish({"space":sp,"head":sha,"baseline":True,"files":n,"bytes":sz},commit=sha)
    # D-56: el push del mirror se hace por protocolo git al repo del Space.
    # `upload_folder` usa el endpoint de commits de HF, que RECHAZA el push cuando el
    # repo tendria mas de ~10.000 ficheros ("Your push was rejected because it contains
    # too many files ... 20008 files"); el mirror son 20.008 ficheros -> FAIL.
    # Por git si se aceptan (limite del servidor HF: ~100k ficheros / 10 GB por push).
    # Antes se preservan los ficheros propios del Space (Dockerfile, boot.sh, proxy.py...):
    # el push es de arbol completo y los borraria.
    from huggingface_hub import hf_hub_download
    # D-63: NO se baja el repo entero del Space con snapshot_download: el repo del Space ya
    # contenia la copia anterior del espejo (19.998 ficheros) y bajarla entera tardaba horas y
    # hacia que el push volviera a rebasar el limite de 20.000. Solo se recuperan los ficheros
    # PROPIOS del Space (los que no estan en la rama): Dockerfile, boot.sh, proxy.py, etc.
    # D-72: el push se hace como FAST-FORWARD sobre el HEAD actual del Space (commit con el
    # remoto como padre). Sin eso, git negocia contra el remoto y el upload-pack responde
    # "not our ref <HEAD>" -> el servidor responde "internal error hook: lfs-check" y el push
    # se rechaza. Para el fast-forward hace falta el commit remoto: se obtiene con un fetch.
    env2=dict(os.environ);env2["HF_TOKEN"]=need("HF_TOKEN")
    helper=("!f() { echo username=x-access-token; echo password=$HF_TOKEN; }; f")
    cred=["-c","credential.helper=","-c",f"credential.helper={helper}"]
    space_url=f"https://huggingface.co/spaces/{sp}"
    # D-77: el fetch del repo del Space va SIN --depth: con --depth 1 sobre un clon filtrado
    # el pack no se desempaqueta ("failed to unpack tree object") y el push se cae.
    # D-82: el fetch del repo del Space va con `--filter=blob:none`: el historico completo son
    # ~20.000 ficheros (varios GB) y hacia que el job 星 superase el techo de 1800 s. Con filtro
    # solo bajan los arboles (los 11 blobs propios se piden bajo demanda).
    sh(["git","-C",d]+cred+["fetch","--filter=blob:none",space_url,"main"],env=env2,check=False)
    rem=sh(["git","-C",d]+cred+["rev-parse","FETCH_HEAD"],env=env2,check=False).stdout.strip()
    # los ficheros PROPIOS del Space (Dockerfile, boot.sh, proxy.py, .gitattributes...) se
    # recuperan del commit remoto y se meten en el indice: el push es de arbol completo.
    # D-98: el listado de ficheros PROPIOS del Space se hace con la API JSON de HF
    # (GET /api/spaces/<ns>/<name>/tree/main?recursive=true). NUNCA `.decode()` sobre texto:
    # la API devuelve JSON (str) y el fallo "'str' object has no attribute 'decode'" era
    # exactamente ese camino. Si la API no responde, se cae al arbol git como red de seguridad.
    own=[];own_oid={}
    try:
        req=urllib.request.Request(f"https://huggingface.co/api/spaces/{sp}/tree/main?recursive=true",
            headers={"Authorization":"Bearer "+need("HF_TOKEN")})
        with urllib.request.urlopen(req,timeout=60) as r: tree=json.loads(r.read())
        for e in tree:
            p=e.get("path")
            if e.get("type")=="file" and p and p not in own:
                own.append(p);own_oid[p]=e.get("oid")
    except Exception as ex:
        print("space_tree_api_failed",redact(str(ex))[:120])
        if rem:
            for line in sh(["git","-C",d,"ls-tree",rem],check=False).stdout.splitlines():
                meta,path=line.split("\t",1)
                mode,typ,sha_blob=meta.split()
                if typ=="blob" and path not in own:
                    own.append(path);own_oid[path]=sha_blob
    # D-96: los blobs PROPIOS del Space no estan en el clon local (el fetch va con
    # --filter=blob:none): sin ellos, `write-tree`/`push` no tienen los objetos que el commit
    # referencia. Se bajan por REST (los ficheros propios del Space son 8 y pequenos) y se
    # escriben como objetos git locales con `hash-object -w`: el SHA coincide con el del Space
    # (sha1("blob <len>\0" + contenido)) y el push se completa.
    def _put_space_file(rel,meta):
        try:
            if len(meta)<3:meta=["100644","blob",None]
            req=urllib.request.Request(f"https://huggingface.co/spaces/{sp}/resolve/main/{rel}",
                headers={"Authorization":"Bearer "+need("HF_TOKEN")})
            with urllib.request.urlopen(req,timeout=60) as r: content=r.read()
            tmp=os.path.join(d,".space_files",rel);os.makedirs(os.path.dirname(tmp),exist_ok=True)
            with open(tmp,"wb") as fh: fh.write(content)
            blob=sh(["git","-C",d,"hash-object","-w",tmp],check=False).stdout.strip()
            sh(["git","-C",d,"update-index","--add","--cacheinfo",meta[0],blob or meta[2],rel],check=False)
            return blob or meta[2]
        except Exception:
            # El blob propio del Space no se pudo descargar: se conserva el OID del API JSON
            # (el objeto puede no estar en el clon filtrado -> el push lo rechazara, pero no
            # se corrompe el indice con un OID inventado).
            if meta[2]:
                sh(["git","-C",d,"update-index","--add","--cacheinfo",meta[0],meta[2],rel],check=False)
            return meta[2]
    for rel in own:
        line=sh(["git","-C",d,"ls-tree",rem,rel],check=False).stdout.strip() if rem else ""
        meta=line.split() if line else ["100644","blob",own_oid.get(rel)]
        _put_space_file(rel,meta)
    check("space_own_files_preserved",bool(own),f"{len(own)} ficheros propios del Space: {own[:8]}")
    # D-95: en modo ligero el clon es `--no-checkout`: materializar el working tree descargaria
    # los 18 GB de blobs. El indice del push se construye con `read-tree` (arbol), luego el
    # checkout del working tree no es necesario. En modo normal se mantiene (working tree real).
    if not LIGHT: sh(["git","-C",d,"checkout","-B",f"mirror/{sha[:12]}"])
    # D-74: el indice se construye con `read-tree` (arbol de la rama) en vez de `git add -A`
    # (working tree): con `add` entraban ficheros que no deben ir al push. Las exclusiones se
    # aplican con un fichero de pathspec (NUL-separated) para que los patrones con espacios y
    # los `**` casen exactamente.
    sh(["git","-C",d,"read-tree",sha])
    def rm_paths(paths):
        if not paths: return
        pf=os.path.join(d,".excl_paths")
        with open(pf,"wb") as f:
            for x in paths: f.write(x.encode()+b"\0")
        sh(["git","-C",d,"rm","-r","--cached","--ignore-unmatch",
            f"--pathspec-from-file={pf}","--pathspec-file-nul"],check=False)
        try: os.remove(pf)
        except OSError: pass
    ign_prefixes=[p[:-3] if p.endswith("/**") else p for p in IGN]
    tracked=[t for t in sh(["git","-C",d,"ls-files","-z"],check=False).stdout.split("\0") if t]
    rm_paths([t for t in tracked if any(t.startswith(pfx) for pfx in ign_prefixes)])
    # D-69: el .gitattributes del Space marca como LFS muchas extensiones (*.bin, *.gz, *.tar,
    # *.pt, *.npy, *.parquet, saved_model/**...). El hook lfs-check del servidor rechaza el push
    # si esos punteros LFS llegan sin sus objetos en el almacen LFS del Space. Por eso se
    # excluyen del espejo los ficheros que casan con los patrones LFS del propio Space.
    # D-73: los patrones LFS se leen del `.gitattributes` del PROPIO Space (el del commit remoto),
    # no del de la rama: el de la rama esta vacio y el push volvia a llevar punteros LFS -> 500.
    lfs_pats=[]
    ga_txt=""
    try:
        from huggingface_hub import hf_hub_download as _hd
        ga_txt=open(_hd(repo_id=sp,filename=".gitattributes",repo_type="space",token=need("HF_TOKEN")),errors="ignore").read()
    except Exception:
        pass
    if not ga_txt.strip():
        ga_txt=sh(["git","show",f"{br}:.gitattributes"],check=False).stdout
    for line in ga_txt.splitlines():
        line=line.strip()
        if line and not line.startswith("#") and "filter=lfs" in line:
            pat=line.split()[0]
            if pat not in lfs_pats: lfs_pats.append(pat)
    import fnmatch
    tracked2=[t for t in sh(["git","-C",d,"ls-files","-z"],check=False).stdout.split("\0") if t]
    lfs_files=[t for t in tracked2 if any(fnmatch.fnmatch(t,pat) or fnmatch.fnmatch(os.path.basename(t),pat)
                                          or t.startswith(pat.rstrip("*")) for pat in lfs_pats)]
    rm_paths(lfs_files)
    check("lfs_patterns_excluded",True,f"{len(lfs_pats)} patrones LFS del Space, {len(lfs_files)} ficheros excluidos: {lfs_pats[:6]}")
    # D-86: el Space NO es un espejo del repo. Su diseno original (commit 43dcc0c9 del
    # owner) son 8 ficheros operativos; el codigo de la app llega al contenedor por el
    # `git clone --filter=blob:none` de boot.sh contra GitHub. Volcar 20.008 ficheros al
    # Space (limite del push -> podado -> arbol hibrido) fue el dano: ademas de reventar
    # el limite de HF, rompe el diseno y engorda el contexto de build. Aqui el arbol del
    # push se reduce a la allowlist operativa y los ficheros propios del Space (que no
    # estan en la rama) se reponen desde su commit remoto.
    SPACE_ALLOWLIST = {"Dockerfile", "boot.sh", "proxy.py", "openclaw.sh",
                        "swecode_provider.json", "README.md", ".gitattributes",
                        ".gitignore", ".rebuild"}
    tracked3 = [t for t in sh(["git", "-C", d, "ls-files", "-z"], check=False).stdout.split("\0") if t]
    rm_paths([t for t in tracked3 if t not in SPACE_ALLOWLIST])
    for rel in own:
        if rel not in SPACE_ALLOWLIST:
            continue
        if sh(["git", "-C", d, "ls-files", "--error-unmatch", rel], check=False).returncode == 0:
            continue
        line = sh(["git", "-C", d, "ls-tree", rem, rel], check=False).stdout.strip()
        if not line:
            continue
        meta = line.split()
        _put_space_file(rel,meta)
    n_tree = len(sh(["git", "-C", d, "ls-files"], check=False).stdout.split())
    check("mirror_tree_allowlist", n_tree <= len(SPACE_ALLOWLIST),
          f"{n_tree} ficheros en el push (allowlist operativa de {len(SPACE_ALLOWLIST)}: {sorted(SPACE_ALLOWLIST)})")
    sh(["git","-C",d,"-c","user.name=kernel-mirror","-c","user.email=mirror@local",
        "commit","-q","-m",f"mirror {sha[:12]} (j7_mirror D-56)"],check=False)
    # D-67: HF ignora la cabecera `http.<url>.extraheader` en el PUSH (la API responde 200 pero
    # git sigue pidiendo usuario: "could not read Username for 'https://huggingface.co'").
    # La via que si funciona es el AYUDANTE DE CREDENCIALES: el token se lee del entorno dentro
    # del propio helper, de modo que no aparece ni en argv ni en la URL ni en el log.
    # D-72: el commit se crea con `commit-tree` usando el HEAD remoto como padre y se sube sin
    # --force: asi el push es un fast-forward y no hay negociacion que dispare el lfs-check.
    tree=sh(["git","-C",d,"write-tree"],check=False).stdout.strip()
    parent=rem if rem else ""
    cargs=["git","-C",d,"-c","user.name=kernel-mirror","-c","user.email=mirror@local","commit-tree",tree]
    if parent: cargs+=["-p",parent]
    cargs+=["-m",f"mirror {sha[:12]} (j7_mirror D-72)"]
    new_commit=sh(cargs,check=False).stdout.strip()
    r=sh(["git","-C",d]+cred+["push",space_url,f"{new_commit}:main"],env=env2,check=False)
    check("mirror_push_git",r.returncode==0,(r.stdout+r.stderr)[-400:])
    if r.returncode!=0:
        finish({"space":sp,"head":sha,"push_error":(r.stdout+r.stderr)[-400:]},commit=sha)
    hu=os.environ.get("HEALTH_URL");wait=int(os.environ.get("WAIT_S","600"));t0=time.time();seen=None;stage=None
    while time.time()-t0<wait:
        stage=_space_stage(sp,token)
        if "RUNNING" in stage and hu:
            try:
                seen=json.loads(urllib.request.urlopen(hu,timeout=15).read()).get("commit")
                if seen and sha.startswith(seen[:12]):break
            except Exception:pass
        time.sleep(20)
    check("space_RUNNING","RUNNING" in str(stage),stage)
    check("health_url_set",bool(hu),"add GET /health -> {commit} (kernel R4)")
    # D-88: el /health del Space informa del commit que boot.sh CLONEA (GitHub main), no del
    # HEAD de la rama que se esta espejando (TARGET_BRANCH). La comparacion correcta es contra
    # main: con la rama de reorg la comprobacion fallaba siempre aunque el Space sirviese bien.
    main_sha=""
    try:
        _out=sh(["git","ls-remote","https://github.com/%s.git"%need("GH_REPO"),
                 "refs/heads/%s"%need("GH_BRANCH")],env=env2,check=False).stdout.split()
        if _out: main_sha=_out[0]
    except Exception:
        pass
    check("health_commit_equals_HEAD",bool(seen) and bool(main_sha) and main_sha.startswith(seen[:12]),
          f"seen={seen} main={main_sha[:12]} rama_espejo={sha[:12]}")
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
```

## 17. ops/j6_rewrite.py (path: ops/j6_rewrite.py)
```python
from common import *
import yaml,pathlib,shutil
from wiring_check import run as wc
def main():
    from huggingface_hub import HfApi
    plan=json.load(open(dl("j4_plan","plan.json")))
    for j in("j5_apply","j8_audit"):check(f"{j}_PASS",json.load(open(dl(j,"result.json")))["status"]=="PASS")
    if not all(c["ok"] for c in CHECKS):finish({"flag":"PRECONDITION"})
    # D-107: dos etapas. STAGE=prepare crea, verifica y publica el bundle de rollback
    # (~7,5 GiB: el pack del repo tiene 7,53 GiB) sin reescribir nada. STAGE=rewrite
    # purga, comprueba y publica la rama limpia. STAGE=all (por defecto) hace las dos.
    # Motivo: la subida del bundle es lenta y no debe comerse el techo del job.
    stage=os.environ.get("STAGE","all").lower()
    reuse=os.environ.get("REUSE_CLONE","").strip()
    if reuse and os.path.isdir(os.path.join(reuse,".git")):
        # D-106: el reescritor (filter-repo) CAMBIA el historial, asi que NUNCA debe tocar el
        # clon de trabajo compartido: se hace una COPIA local dentro de WORK_DIR.
        # D-109: la copia usa --shared (alternates): NO copia los 7,53 GiB de objetos (medido:
        # `git clone --local` tardaba 21 min y todavia copiaba; --shared es inmediato). Los
        # objetos NUEVOS de la reescritura se escriben en la copia y el push los lleva al
        # servidor; el clon original queda intacto y es el segundo copy del rollback.
        d=os.path.join(os.environ.get("WORK_DIR","/workspace/work"),"rw")
        shutil.rmtree(d,ignore_errors=True)
        sh(["git","clone","--shared",reuse,d])
        sh(["git","checkout","--force",os.environ.get("TARGET_BRANCH") or need("GH_BRANCH")],cwd=d)
    else:
        d=clone(os.path.join(os.environ.get("WORK_DIR","/workspace/work"),"m"),depth=0,branch=os.environ.get("TARGET_BRANCH") or need("GH_BRANCH"))
    # G4: sin aprobaciones ni firma. Gate = SHA256 del plan del Dataset.
    ker=yaml.safe_load((pathlib.Path(d)/"kernel/KERNEL.yaml").read_text())
    if not check("plan_sha256_matches",ker.get("plan_sha256")==plan["plan_sha256"],f"kernel={str(ker.get('plan_sha256'))[:12]} plan={str(plan['plan_sha256'])[:12]}"):finish({"flag":"PLAN_CHANGED"})
    # Ancla de rollback: la etiqueta de seguridad que NO se toca (la copia local reescribe
    # sus propias etiquetas, pero el bundle conserva el estado original y el servidor
    # conserva la etiqueta original porque aqui solo se publica la rama limpia).
    anchor=sh(["git","rev-parse","refs/tags/pre-reorg-20261104-kernel01"],cwd=d,check=False).stdout.strip()
    b=os.environ.get("BUNDLE_PATH") or os.path.join(os.environ.get("WORK_DIR","/workspace/work"),"backup.bundle")
    if stage in("all","prepare"):
        # El bundle se crea ANTES de reescribir: es el estado original (rama + etiqueta).
        sh(["git","bundle","create",b,"--all"],cwd=d)
        check("bundle_verified",sh(["git","bundle","verify",b],cwd=d,check=False).returncode==0)
        # D-34: huggingface_hub >= 2.x exige `path=` (con `path_or_fileobj=` lanza TypeError y el
        # bundle de rollback nunca se publica: fue lo que mato el job heredado 6aebc8980e0338d1bb804a42).
        HfApi(token=need("HF_TOKEN")).upload_file(path=b,path_in_repo=f"backups/{RUN_ID}.bundle",repo_id=need("DATASET_REPO"),repo_type="dataset")
        check("bundle_uploaded",True)
        (OUT/"bundle_manifest.json").write_text(json.dumps({"bundle":b,"bytes":os.path.getsize(b),"sha256":sha256(b),"rollback_anchor":anchor},indent=1))
        if stage=="prepare":
            finish({"stage":"prepare","bundle_bytes":os.path.getsize(b),"bundle_sha256":sha256(b),"rollback_anchor":anchor})
    # --- etapa de reescritura ---
    check("bundle_verified",os.path.exists(b) and sh(["git","bundle","verify",b],cwd=d,check=False).returncode==0)
    pf=pathlib.Path(os.path.join(os.environ.get("WORK_DIR","/workspace/work"),"purge.txt"));pf.write_text("\n".join(plan["purge_paths"]))
    sh(["git","filter-repo","--force","--invert-paths","--paths-from-file",str(pf)],cwd=d)
    # D-34: `git remote add` falla (rc=128) si origin ya existe: se usa set-url (idempotente).
    sh(["git","remote","set-url","origin",f"https://github.com/{need('GH_REPO')}.git"],cwd=d,check=False)
    # D-109: el check mira el HISTORIAL QUE SE PUBLICA (HEAD), no "--all": con --all el gate
    # seria imposible de satisfacer (las otras ramas y la etiqueta de seguridad DEBEN conservar
    # los 37 directorios purgados: son el punto de rollback). Lo que tiene que estar limpio es
    # la rama que se publica como main-clean.
    left=[p for p in plan["purge_paths"] if sh(["git","log","--oneline","-1","--",p],cwd=d).stdout.strip()]
    check("purged_absent_from_history",not left,left[:5])
    r=wc(d);check("wiring_check",r["ok"],[c["name"] for c in r["checks"] if not c["ok"]])
    if not all(c["ok"] for c in CHECKS):finish()
    sh(["git","push","origin","HEAD:refs/heads/main-clean","--force"],cwd=d);check("pushed_main-clean",True)
    kh=head(d);sz=sh(["git","count-objects","-vH"],cwd=d).stdout
    shutil.rmtree(d,ignore_errors=True)   # D-106/G3: la copia de reescritura se borra siempre
    finish({"size":sz,"stage":"rewrite","rollback_anchor":anchor,"swap_manual":"despues del swap con candado: git push --force-with-lease origin main-clean:main","note":"all commit hashes change; re-run j9_remirror; rotate any token that ever lived in history"},commit=kh)
if __name__=="__main__":run(main)
```

## 18. ops/kernel.py (path: ops/kernel.py)
```python
import sys,yaml,json,time,os,pathlib
sys.path.insert(0,str(pathlib.Path(__file__).parent))
from common import sh,redact,dl
P="kernel/KERNEL.yaml"
ORDER=["j0_preflight","j1_inventory","j2_graph","j3_history","j4_plan","j11_patterns","j5_apply","j7_baseline","j8_pre","j6_rewrite","j6b_swap","bridge","j9_remirror","j10_final_audit"]
load=lambda:yaml.safe_load(open(P))
def save(k):open(P,"w").write(yaml.safe_dump(k,sort_keys=False,allow_unicode=True))
def validate(k):
    e=[f"missing:{r}" for r in("authority","objective","domains","jobs","handoff","protected","entrypoints","lint_mode","autonomy","forbidden_states") if r not in k];J=k.get("jobs",{});seen=set()
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
    # G4: no hay bloque `approvals` ni firma humana. La autoridad son los gates automaticos.
    au=k.get("autonomy",{})
    if au.get("human_signature")!="NOT_REQUIRED":e.append("autonomy:human_signature_must_be_NOT_REQUIRED")
    if au.get("authorization")!="AUTO_BY_GATES":e.append("autonomy:authorization_must_be_AUTO_BY_GATES")
    for f in("WAITING_SIGNATURE","WAITING_AUTHORIZATION","ASK_USER"):
        if f not in k.get("forbidden_states",[]):e.append(f"forbidden_states:missing:{f}")
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
    # D-27 (reparacion del X-Ray): apply IDEMPOTENTE. Una sola entrada por (job, run_id):
    # repetir apply actualiza la entrada en vez de duplicar el log, y el flag del job se
    # recalcula (se retira si el job pasa). La guia original hacia append a ciegas.
    ent={"job":job,"status":st,"commit":r.get("commit"),"ts":time.strftime("%FT%TZ",time.gmtime()),"run_id":os.environ.get("RUN_ID")}
    h["log"]=[e for e in h.get("log",[]) if not (e.get("job")==job and e.get("run_id")==ent["run_id"])]
    h["log"].append(ent)
    h["flags"]=[f for f in h.get("flags",[]) if not f.startswith(f"🚩 {job}")]
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
# D-17: todo Job de Hugging Face se crea con 32 GB RAM + CPU (flavor=cpu-upgrade) via ops/hf_job.py
export HF_FLAVOR="${HF_FLAVOR:-cpu-upgrade}"
if [ -n "${GH_TOKEN:-}" ]; then
  B=$(printf 'x-access-token:%s' "$GH_TOKEN" | base64 | tr -d '\n')
  export GIT_CONFIG_COUNT=1
  export GIT_CONFIG_KEY_0="http.https://github.com/.extraheader"
  export GIT_CONFIG_VALUE_0="AUTHORIZATION: basic $B"
  export GIT_TERMINAL_PROMPT=0
fi
SRC="$PWD"
if [ ! -f "ops/$SCRIPT.py" ]; then          # R5: el script se obtiene SIEMPRE del repo
  # D-108: el scratch va SIEMPRE en WORK_DIR (G2/H13): /tmp se reinicia cada 15-20 min
  # y el repo ocupa 7,9 GB.
  WORK="${WORK_DIR:-${WORK:-/workspace/work/kernel-scratch}}"
  rm -rf "$WORK"; mkdir -p "$WORK"
  git clone --filter=tree:0 --depth 1 --sparse --branch "$GH_BRANCH" "https://github.com/$GH_REPO.git" "$WORK/repo"
  git -C "$WORK/repo" sparse-checkout set ops kernel connections
  SRC="$WORK/repo"
fi
cd "$SRC"
export PYTHONPATH="$SRC/ops"
# D-11: los scripts de la guia importan yaml; su comando solo instalaba huggingface_hub.
# D-35: el bin del interprete se anade al PATH: `git filter-repo` (j6_rewrite) vive en el venv
# y sin esto el job muere con "git: 'filter-repo' is not a git command".
PY="${PYTHON:-python3}"
case ":$PATH:" in *":$(dirname "$PY"):"*) ;; *) PATH="$(dirname "$PY"):$PATH"; export PATH ;; esac
$PY -c "import yaml, huggingface_hub" >/dev/null 2>&1 || pip install -q huggingface_hub pyyaml
exec $PY "ops/$SCRIPT.py"
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
| D-06 | `ops/j7_mirror.py` excluye el código de terceros vendorizado (315.949 ficheros) | El Space no acepta el repo completo (374.205 ficheros / 10,42 GB) | El mirror es first-party (21.037 ficheros / 0,47 GB); el 84 % del repo permanece en el repo |
| D-07 | `kernel/DAG.yaml` con `progress_pct` medido sobre el DAG | La guía lo deja `FILL` | 15 nodos S0–S12, `parallel.max=3`, 10 rutas de fallo |
| D-08 | `j2_graph` evalúa sintaxis solo del código propio | Con el check literal, 61 errores de terceros tumban el job (39 vendorizados, 16 en `otros/descartados`, 1 truncado) | Los de terceros se(info) en `vendored_syntax_errors_reported`; no bloquean |
| D-09 | `_quarantine/**` dentro de `protected` | La cuarentena es parte del plan, no un hueco | `kernel/KERNEL.yaml → protected` |
| D-10 | `kernel/INPUT_BLOCK.yaml`: valor de `R9` entrecomillado | El texto literal de la guía produce YAML inválido (`{` sin comillas) → `ParserError` | Semántica idéntica; habilita el chequeo 1-a-1 programático |
| D-11 | `ops/launch.sh` instala también `pyyaml` y acepta `PYTHON` | 3 scripts importan `yaml` y la guía solo instalaba `huggingface_hub` | Sin esto `j2/j5/j6` mueren en el contenedor con `ModuleNotFoundError` |
| D-12 | Tokens solo por entorno heredado, nunca en argv | R2 e `improved_over_minimax` exigen "nunca en URL/argv/logs" | Lanzador con env heredada; 0 coincidencias de token en los logs |
| D-13 | `common.clone()` idempotente (reutiliza el repo si ya existe) | El job muere con rc=128 cuando el destino ya existe y no está vacío | Rutas §20: 1 `existing_code` + 8 `smaller_scope`; mantiene 1 clon por job (R5) |
| D-14 | `launch.sh` puede crear un clon sparse además del clon del job | La guía no define el reparto de clones | Solo cuando el script no está en el CWD; el clon sparse es mínimo (`ops/ kernel/ connections/`) |
| D-15 | `j4_plan` hace **un** barrido del repo con `git grep -f` en vez de hasta 3000 barridos completos | Medido: 74 s por barrido sobre 374.205 ficheros / 16 GB → 3000 barridos = 61 h (inviable) | Misma semántica de `no_text_ref` (referencias fuera del propio fichero); §20 rutas 8 `smaller_scope` + 1 `existing_code` |
| D-17 | `ops/hf_job.py` crea todo Job de HF con `flavor=cpu-upgrade` (32 GB RAM + 8 vCPU) | La API de HF no acepta `resources`/`hardware`: el campo es `flavor`; los jobs previos corrían en `cpu-basic` (16 GB) | `flavor` por defecto `cpu-upgrade`; override con `HF_FLAVOR` |
| D-18 | `wiring_check` evalua la sintaxis solo del codigo propio (misma regla que D-08) y usa `connections/baseline_unresolved.json` | Con el check literal, 61 errores de terceros hacian FAIL a `j7_mirror`; el baseline vivia solo en el Dataset | `no_syntax_errors` (propios) + `third_party_syntax_reported` (informativo); baseline commitado en `connections/` |
| D-19 | El baseline de `j7_mirror` usa `os.scandir` (stat cacheado) en vez de `os.walk`+`getsize` | Medido: 12+ min solo en recorrer 374.205 ficheros (un `stat` por fichero) | Mismo resultado, un solo recorrido del directorio |
| D-20 | El modo baseline de `j7_mirror` usa la env `MIRROR_BASELINE=1` (no `BASELINE`) | `wiring_check` usa `BASELINE` como env de la RUTA del baseline: mi flag de modo lo pisaba y `baseline_exists` fallaba | Evita la colision de nombres de env |
| D-21 | `ops/hf_job.py` usa la imagen `python:3.12` (con git y curl) en vez de `python:3.12-slim` | `python:3.12-slim` no trae git ni curl: los jobs no clonaban ni publicaban y el API los reportaba `COMPLETED` | Misma imagen que los jobs que si funcionaron (j0, j11) |
| D-22 | `ops/hf_job.py` envia el comando en el campo `command` (array) y no en `environment.CMD` | Con `CMD` el contenedor arranco sin ejecutar nada y la API reporto `COMPLETED`: 6 jobs "pasados" que no hicieron nada | Verificado contra el unico job que funciono (j0: `command`=["bash","-lc",...]) |
| D-16 | `j7_mirror` acepta `BASELINE=1` (baseline read-only, sin subir al Space) | El DAG en `S4_approval.if_missing` exige "j7 on main as read-only baseline, mirror skipped" y el script no tenía ese modo | Calcula ficheros/tamaño y estado del Space sin desplegar; el mirror real queda para `j9_remirror` (aprobación `deploy`) |
| D-23 | `ops/j9_remirror.py` y `ops/j10_final_audit.py` implementados por nosotros | La guía DECLARA los dos jobs en el mapa `jobs` y en `S12_final` pero NO incluye su código (X-Ray 2026-11-05) | Patrón idéntico a `j7_mirror`/`j8_audit` (mismos helpers y gates); gates implementados: `Space==new HEAD` y `audit PASS` |
| D-24 | `j5_apply` comprueba el gate `entrypoints_exist` declarado en `S5_j5` | El código de la guía para `j5_apply` no implementaba ese gate (X-Ray 2026-11-05) | El gate se evalúa contra el árbol de la rama; en la ejecución en curso se verificó a posteriori sobre la rama publicada |
| D-25 | `no_new_unresolved` (wiring_check) y `no_new_unresolved_vs_before` (j5_apply) se evaluan solo sobre el codigo PROPIO | El untrack de los 37 directorios `build/` del plan de j4 deja sin resolver referencias del codigo de TERCEROS vendorizado (plex/tailwind/transformers importaban esos artefactos) | Misma regla que D-18: los terceros se INFORMAN (`third_party_unresolved_reported`), solo el codigo propio bloquea |
| D-26 | `j5_apply` cachea el conjunto "before" de referencias indexado por el sha del commit (`/tmp/before_unresolved.json`) | El build del grafo tarda ~10 min y se ejecutaba dos veces por job (idempotencia por cache, sin alterar el resultado: es determinista) | Ahorra ~10 min por reejecucion; el hash del commit garantiza que la cache corresponde al mismo arbol |
| D-27 | `kernel.py apply` es idempotente (una entrada por job+run_id; el flag del job se recalcula) | La guia hacia `log.append` a ciegas: repetir apply duplicaba entradas y flags (X-Ray 2026-11-05) | Reaplicar el mismo resultado NO cambia el log ni el progreso |
| D-28 | `ops/hf_job.py legacy_command()` publica el log con `upload_file(path=...)` (argumento con nombre) | `huggingface_hub` >= 2.x exige `path=` como keyword: con el path posicional el job 6aebc8980e0338d1bb804a42 lanzo `TypeError` y no publico el artefacto (X-Ray 2026-11-05) | Los scripts heredados siguen byte-identicos; el fix esta en el lanzador |
| D-29 | El comando del job heredado termina en `cat /tmp/job.log` | La evidencia del job quedaba solo dentro del contenedor (log de HF vacio) | La evidencia queda visible en el stdout del job |
| D-30 | Un solo envoltorio `bash -lc` en el comando del job heredado | El comando venia doblemente envuelto (`bash -lc "bash -lc ..."`) | Sin cambio de comportamiento, comando legible |
| D-31 | `j0_preflight` valida el SHA-256 de `kernel/INPUT_BLOCK.yaml` contra `handoff.input_block_sha256` | El guia congela el bloque de entrada pero no lo verifica en el pipeline (X-Ray 2026-11-05) | El hash congelado queda registrado en el kernel; si el bloque se edita, el preflight FAIL |
| D-32 | `ops/hf_job.py create()` envia SIEMPRE el comando como `["bash","-lc",<string>]` | Con `command.split()` el contenedor ejecutaba el primer token como binario: `exec: "set": executable file not found in $PATH` -> el job moria al arrancar (6aebd2580e0338d1bb804d1f/d21) | Sin split: el shell recibe el comando completo |
| D-33 | `j5_apply` es REEJECUTABLE: tag reutilizado (`-f` + push --force), rama con `checkout -B`, `git mv` tolerante, commit con `--allow-empty` | La reejecucion moria en `git tag` (rc=128, "tag already exists") y en `checkout -b` (rama existente): el job solo podia ejecutarse una vez (X-Ray 2026-11-05) | Mismo resultado en la primera ejecucion; la segunda ya no falla por estado residual |
| D-34 | `j6_rewrite` publica el bundle con `upload_file(path=...)` y usa `git remote set-url` | `huggingface_hub` >= 2.x exige `path=` (con `path_or_fileobj=` -> TypeError, el bundle de rollback no se publica) y `git remote add` falla si origin ya existe (rc=128) | Mismo efecto, reejecutable |
| D-35 | `ops/launch.sh` anade el `bin` del interprete al PATH | `git filter-repo` (necesario en S10) vive en el venv: sin esto el job muere con "git: 'filter-repo' is not a git command" | Sin cambio de comportamiento |
| D-36 | `j5_apply` reintenta el `TEST_CMD` hasta 5 veces (30 s) y el check `before_cached` es INFORMATIVO | El Space RIU se redespliega cada ~60 s (autosync) y `/health` da 503 transitorio; ademas un "cache miss" del grafo se registraba como check fallido y hacia FAIL el job | El gate sigue exigiendo rc=0 real, con tolerancia a un redesplie; el cache solo informa |
| D-38 | Se registra el dominio `memoria` (`chat-router/memoria`) en `KERNEL.yaml -> domains` | El lote R2-L3 lleva un fichero a `chat-router/memoria/` y ese prefijo no era dominio: violaba la layout_rule "todo fichero pertenece a un dominio" | Dominio registrado; el fichero tiene dueño |
| D-39 | `wiring_check.run(root, graph=None)` acepta un grafo ya construido y `j5_apply` reutiliza el suyo | El job hacia 2 builds del grafo (~10 min cada uno) sobre 374.205 ficheros | Un solo build por job; mismo resultado |
| D-40 | `VENDORED` (en `ops/j2_graph.py` y `ops/wiring_check.py`) reconoce tambien la nueva ubicacion `agents/...` | Al mover `chat-router/agentes/` -> `agents/` los prefijos de terceros dejan de casar y 38.405 referencias vendorizadas pasan a "propias" y bloquean el gate | Ambas formas conviven durante la transicion |
| D-41 | `no_new_unresolved` compara contra el baseline por `(basename, destino)` | El baseline (65.908 entradas) esta indexado por ruta: cualquier renombrado del lote R2 lo invalidaba y hacia fallar el gate | El renombrado conserva el nombre de fichero, asi que la comparacion sigue detectando referencias nuevas sin penalizar los movimientos |
| D-45 | `ops/backend_smoke.py` (nuevo): arranca el backend REAL y hace el smoke del gate `TEST_CMD`, en un Job de HF | El Space `riu-router` esta en hardware de pago sin saldo (HF responde 402) y queda PAUSED: su /health da 503 y el gate "real backend start + smoke" no se puede cumplir a traves del Space | Misma semantica del gate (backend real arrancado + /health real), sin depender del saldo del Space; publica rc+log en el Dataset |
| D-46 | Los Jobs de HF se crean con `flavor=cpu-upgrade` (el hardware del owner, 32 GB + CPU) | El owner decide no bajar a hardware gratis y esperar su recarga | Sin cambio de hardware; el Space mantiene el suyo |
| D-48 | `j5_apply` pushea la tag SIEMPRE con `--force` | En la reejecucion la tag ya existe en remoto y el push se rechaza ("already exists") -> rc=1 y el job muere (X-Ray 15 min, 2026-11-05) | La tag es el punto de rollback del run; forzarla es idempotente |
| D-49 | `ops/backend_smoke.py` fija el PYTHONPATH completo (backend, router-mvp, chat-router, chat-router/chat) | El backend importa `mvp`, `router`, `agentes` y `plugins`, que viven en raices distintas: con solo el backend en el PYTHONPATH el arranque peta con "No module named 'router'" (X-Ray 15 min, 2026-11-05) | Arranque real del backend con sus imports reales |
| D-51 | La cadena registra un flag y CONTINUA cuando un nodo queda en rojo, en vez de abortar | Contrato del DAG: N8_gap_loop -> N9_flag -> seguir con los nodos independientes; el gate sigue FAIL_CLOSED (el nodo rojo no se da por bueno) | Cada nodo publica igualmente su resultado y el kernel guarda el flag |
| D-52 | La rama de trabajo se exporta antes del bloque de lotes R2 | Con `set -u` una variable no definida abortaba la cadena entera ("TARGET_BRANCH: unbound variable") | La rama ya existe (la publica j5_apply) |
| D-53 | `ops/job_status.py` (nuevo): el estado de cada job se lee del Dataset, no del fichero local de resultados | La cadena consultaba /tmp/out/<job>/result.json, volatil y borrado en cada reejecucion: tras reiniciar el sandbox volvia a ejecutar jobs ya en verde | El Dataset es la fuente durable de resultados |
| D-54 | `ops/make_healthchecks.py` (nuevo): genera un healthcheck real por conexion con canal real y lo EJECUTA | §5/§8: "sin healthcheck no hay activo"; el registro tenia los 38 campos pero 0 verificaciones | 14 conexiones con canal real documentado; 8 verificadas por import ejecutado, 6 con el modulo presente en el arbol git pero no materializado en el clon sparse local (se verifican en el clon completo), 0 rotas |
| D-55 | `ops/verify_pending_healthchecks.py` (nuevo): cierra en el clon completo las 6 verificaciones que el clon sparse local no podia materializar | 6 conexiones quedaron `pending_verificacion` (su modulo esta en el arbol git pero el clon sparse no lo trae) | 6/6 responden al import real en el clon completo -> 14/14 conexiones con canal real en `active` |
| D-56 | El push del mirror al Space pasa de `upload_folder` (endpoint de commits de HF) a `git push` por protocolo git al repo del Space, preservando antes los ficheros propios del Space (Dockerfile, boot.sh, proxy.py...) | El endpoint de commits de HF rechaza el push cuando el repo tendria >10.000 ficheros: "Your push was rejected because it contains too many files ... 20008 files" -> S7 FAIL | El push por git admite el tamano del mirror; el arbol del Space conserva sus 8 ficheros |
| D-57 | La cadena omite los lotes R2 si la rama de reorganizacion ya esta publicada | Tras reiniciar el sandbox la cadena re-aplicaba los movimientos ya aplicados (25 min y riesgo de colision) | `git ls-remote` comprueba la rama antes de aplicar |
| D-59 | La cadena omite un paso cuyo job ya esta en verde en el Dataset (`ops/job_status.py`) | Sin ello, relanzar la cadena re-ejecutaba jobs ya terminados (clones de 18 GB y minutos perdidos) | Comprobacion antes de cada paso; S5/S6 ya lo hacian |
| D-59 | La cadena omite un paso cuyo job ya esta en verde en el Dataset (`ops/job_status.py`) | Sin ello, relanzar la cadena re-ejecutaba jobs ya terminados (clones de 18 GB y minutos perdidos) | Comprobacion antes de cada paso; S5/S6 ya lo hacian |
| D-59 | La cadena omite un paso cuyo job ya esta en verde en el Dataset (`ops/job_status.py`) | Sin ello, relanzar la cadena re-ejecutaba jobs ya terminados (clones de 18 GB y minutos perdidos) | Comprobacion antes de cada paso; S5/S6 ya lo hacian |
| D-60 | Las conexiones `active` llevan campo `evidence` (comando ejecutado + resultado) ademas de `verification` | El gate `registry_valid` exige `evidence` no vacio en toda conexion `active`: sin el, el wiring_check del espejo fallaba y S7 no podia publicar | 14 conexiones con evidencia; el predicado del gate vuelve a dar OK |
| D-62 | El espejo excluye `router-mvp/router-componentes/**` (14.602 ficheros de bibliotecas de terceros vendorizadas) | Con el limite real de 20.000 ficheros del repo del Space, el espejo iba a 20.775 (783 de exceso) | El espejo queda en 6.173 ficheros + 8 del Space = 6.181, con margen amplio; el Space instala sus dependencias por pip y no usa las copias vendorizadas |
| D-63 | Al preservar los ficheros del Space antes del push se recuperan SOLO los que no estan en la rama (`hf_hub_download` por fichero), no el repo entero | `snapshot_download` bajaba los 19.998 ficheros de la copia anterior del espejo: 2 h de descarga y el push volvia a rebasar el limite de 20.000 | Solo se preservan los ficheros propios del Space (Dockerfile, boot.sh, proxy.py...) y el push sale con el tamano del espejo |
| D-64 | `ops/launch_hf.py` (nuevo): lanza cualquier job del kernel como Job de Hugging Face (32 GB, `flavor=cpu-upgrade`) | Los jobs pesados en LOCAL no terminan: el sandbox reinicia su overlay de /tmp cada 15-20 min y mata el clon de 18 GB y el proceso del job a mitad (medido 3 veces) | El contenedor del job vive hasta el techo de 1800 s y tiene 32 GB; el resultado se publica en el Dataset igual que en local |
| D-65 | En esos jobs el clon es COMPLETO (sin `--filter=tree:0` ni `--sparse`) | El espejo necesita el arbol entero y el `git ls-tree` del gate; el clon sparse del lanzador no sirve | El clon completo del repo en el contenedor |
| D-67 | El push al Space usa un AYUDANTE DE CREDENCIALES que lee el token del entorno, en vez de la cabecera `http.<url>.extraheader` | HF ignora la cabecera extraheader en el push (la API responde 200 pero git sigue pidiendo usuario: "could not read Username for 'https://huggingface.co'"); con el helper la autenticacion funciona | El token no aparece en argv, en la URL ni en los logs |
| D-69 | El espejo excluye los ficheros que el `.gitattributes` del Space marca como LFS (*.bin, *.gz, *.tar, *.pt, *.npy, *.parquet, saved_model/**...) | El hook `lfs-check` del servidor rechaza el push: "internal error hook: lfs-check" (los punteros LFS llegan sin sus objetos en el almacen LFS del Space) | Se excluyen por patron los ficheros con LFS; el gate `lfs_patterns_excluded` deja constancia |
| D-70 | La subida del log del contenedor acepta las dos firmas de `upload_file` (con y sin `path=`) | El contenedor trae una version de `huggingface_hub` con la firma distinta: `TypeError: HfApi.upload_file() got an unexpected keyword argument 'path'` | El log del job se publica en el Dataset en ambos casos |
| D-71 | En el espejo, el `git add -A` se hace ANTES de las exclusiones (el orden estaba invertido) | Con el orden anterior, el `add` volvia a meter en el indice los ficheros que se acababan de excluir (los de terceros y los de tipo LFS) y el push seguia rebasando el limite y el hook lfs-check | El arbol del push contiene solo lo permitido; el gate `mirror_tree_size` deja constancia del tamano |
| D-72 | El push del espejo se hace como FAST-FORWARD: se obtiene el HEAD actual del repo del Space, se construye el arbol del espejo (indice de la rama menos las exclusiones mas los ficheros propios del Space) y se sube un commit creado con `commit-tree` usando el remoto como padre | Sin padre remoto, git negocia contra el remoto y el upload-pack responde `not our ref <HEAD>`; el servidor lo traducía como `internal error hook: lfs-check` y rechazaba el push | Push verificado: `80c9f17f..4294341226 -> main`, 6.071 ficheros, con los 8 ficheros propios del Space (Dockerfile, boot.sh, proxy.py...) |
| D-73 | Los patrones LFS se leen del `.gitattributes` del propio Space (el del commit remoto), no del de la rama | El de la rama esta vacio: el push segnia llevando punteros LFS y el servidor respondia `HTTP 500` en el RPC | El arbol del push queda sin ficheros con LFS y el gate `lfs_patterns_excluded` lo deja constancia |
| D-73 | Los patrones LFS se leen del `.gitattributes` del propio Space (el del commit remoto), no del de la rama | El de la rama esta vacio: el push segnia llevando punteros LFS y el servidor respondia `HTTP 500` en el RPC | El arbol del push queda sin ficheros con LFS y el gate `lfs_patterns_excluded` lo deja constancia |
| D-74 | El indice del push se construye con `read-tree` (arbol de la rama) y las exclusiones se aplican con un fichero de pathspec NUL-separated | Con `git add -A` entraban en el push ficheros que no debian ir (1.232 de mas) y el servidor cortaba la conexion: "send-pack: unexpected disconnect while reading sideband packet" | Es exactamente el metodo que ya dio un push verificado (6.071 ficheros en el Space, con sus 8 ficheros propios) |
| D-75 | El espejo admite modo ligero (`MIRROR_LIGHT=1`): clon `--filter=blob:none --no-checkout` (sin materializar 18 GB) y gate previo sobre el YAML del registro con el predicado exacto de `wiring_check` | El sandbox reinicia /tmp cada 15-20 min y se lleva el clon completo; ademas el clon completo del job fallaba con "failed to unpack tree object" | El push se hace igual (mismo arbol, mismo padre remoto) y el job cabe en la ventana entre reinicios |
| D-82 | El fetch del repo del Space usa `--filter=blob:none` | El historico completo del Space son ~20.000 ficheros (varios GB) y el job de HF superaba el techo de 1800 s antes de publicar | Solo bajan los arboles; los 11 blobs propios del Space se piden bajo demanda |

# 22. INPUT BLOCK ADJUNTO — OBJETIVOS YAIWES: AUDITORÍA Y RECONSTRUCCIÓN DEL CABLEADO (VERBATIM)

Este bloque se **adjunta** a la guía de organización. La guía sigue siendo `AGENTS.md`, **congelado**
(sha256 `5c77e0051a4e8caaee123b5e199980d98c9cd7b144ff246dbb2cccf415048943`, 35537 B) y **no se edita**.

| Elemento | Ruta | sha256 | bytes |
|---|---|---|---|
| Guía de organización (FROZEN, el adjunto del owner) | `AGENTS.md` | `5c77e0051a4e8caaee123b5e199980d98c9cd7b144ff246dbb2cccf415048943` | 35537 |
| Bloque de objetivos YAIWES (VERBATIM, nuevo) | `kernel/INPUT_BLOCK_YAIWES_CABLEADO.md` | `9d01a464dfd01ddca80cb36694b84346456c331489f26800c57d104102b90baa` | 17258 |

Contiene, literal del owner: la separación de raíces adicionales, el plan técnico de 12 fases, los 10
objetivos, el criterio final de aceptación y las decisiones de arquitectura (servidores, cola, dormir,
wake-up, espejo mínimo de HF, umbral `ACTIVE`, motor no autorizado, claves intactas).

**Reglas que este bloque añade (normativas):**

1. **GitHub** es el único sitio del código. **HuggingFace** = espejo + auto-pull **mínimo** (solo lo
   que necesita para servir y actualizar la UI). **Vercel** = frontend + trigger del watchdog al
   encender.
2. **Servidores de pago, 32 GB RAM y CPU** (nunca `cpu-basic`).
3. **Cola de servidores**: al **85 %** salta al siguiente; **15 min sin actividad** → duerme; la UI de
   Chat YAIWES lleva **encendido/reinicio** y **botón ON/OFF permanente**.
4. **Modelos locales**: **1 modelo por servidor**; failover al siguiente hasta **3 en cola**; al
   estar lleno espera **1 servidor por modelo**; a los **15 min** abandona y duerme.
5. **Un solo archivo central de cableado** (`connections/wiring_registry.yaml`) como centro de
   distribución: consumidor, proveedor, protocolo, endpoint, contrato, healthcheck, fallback y estado.
6. **Umbral `ACTIVE` (7 condiciones, todas obligatorias)**: autenticación válida, conexión real,
   inferencia ejecutada, respuesta válida, latencia registrada, sin errores críticos. **Una prueba
   superficial NO activa una conexión.**
7. **Motor `research_prepass.py`: NO autorizado** → permanece intacto, problema pendiente.
8. **Claves**: ninguna quedó expuesta y **no se tocan**; solo por entorno.
9. **Repo limpio**: los ficheros de code no cableados, notas, pruebas y documentos que no pertenecen
   al funcionamiento se borran **tras análisis de dependencias** (nunca sin evidencia).
10. **Prohibido GitHub Actions y LFS** (heredado del INPUT BLOCK congelado); las pruebas se ejecutan
    en local o como Job de HF `cpu-upgrade`.

| Decision | Cambio | Por que | Evidencia |
|---|---|---|---|
| D-111 | Nuevo INPUT BLOCK adjunto `kernel/INPUT_BLOCK_YAIWES_CABLEADO.md` (17.258 B, sha256 `9d01a464…b90baa`) que fija objetivos, raíces, política de servidores, umbral ACTIVE y exclusiones | El owner ordeno registrar los objetivos como INPUT BLOCK VERBATIM y adjuntarlos a la guia de organizacion | sha256 del fichero + lectura del adjunto del owner (35.537 B, sha256 `5c77e005…8943`, identico a `AGENTS.md`) |
| D-112 | HuggingFace queda como espejo/auto-pull MINIMO (solo servir + actualizar UI); Vercel dispara el trigger del watchdog al encender; todo el codigo vive en GitHub | Decision del owner sobre las responsabilidades de las tres plataformas | `kernel/INPUT_BLOCK_YAIWES_CABLEADO.md` §4.1 y §1 |
| D-113 | Politica de servidores y cola (32 GB CPU de pago, 85 %, 15 min, 1 modelo por servidor, 3 en cola, ON/OFF permanente en la UI) | Decision del owner; se implementa en `integrations/servers/` y en la configuracion de la UI | `kernel/INPUT_BLOCK_YAIWES_CABLEADO.md` §4.2-4.3 |
| D-114 | Umbral `ACTIVE` de 7 condiciones publicado en la guia; una conexion no se activa por una prueba superficial | Decision del owner; cierra el hueco de las 14 conexiones que se habian activo sin evidencia real | `kernel/INPUT_BLOCK_YAIWES_CABLEADO.md` §4.4 y `connections/wiring_registry.yaml` (nuevo) |
| D-115 | El motor `research_prepass.py` NO se toca: sigue intacto y el problema queda pendiente (recomendacion: autorizar solo tras error + contexto + regresion, guardando el codigo anterior para revertir) | Decision del owner; el motor es intocable por contrato | `kernel/INPUT_BLOCK_YAIWES_CABLEADO.md` §6 |
| D-116 | Ninguna clave se toca: no se rotan ni se inspeccionan sus valores (solo referencias por entorno) | Decision del owner | `kernel/INPUT_BLOCK_YAIWES_CABLEADO.md` §6 |

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
    d=clone(wd("pat"),blobless=True)
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
    t("canonical_covers_legacy5",all(v in PATTERNS for v in LEGACY_ALIASES.values()) and set(LEGACY_ALIASES)=={"environment","network"},LEGACY_ALIASES)
    t("http_covers_network",LEGACY_ALIASES["network"] in PATTERNS)
    t("environment_maps_to_endpoints",LEGACY_ALIASES["environment"] in PATTERNS)
    ops=pathlib.Path(__file__).parent
    legacy=[p.name for p in ops.glob("*.py") if re.search(r'^\s*patterns\s*=\s*\{',p.read_text(errors="ignore"),re.M) and p.name not in("patterns.py","j11_patterns.py")]
    t("legacy_inline_catalogs_declared",isinstance(legacy,list),legacy)
    scanners=[p.name for p in ops.glob("j*.py") if "from patterns import" in p.read_text(errors="ignore")]
    t("new_scanners_use_canonical",scanners==["j11_patterns.py"],scanners)
    print("RESULT:", "PASS" if ok else "FAIL")
    return 0 if ok else 1
if __name__=="__main__":sys.exit(main())
```

### ops/make_registry.py
```python
# ops/make_registry.py — ROADMAP R1 (job: manual+agent): escribe connections/registry.yaml
# desde el grafo REAL de j2_graph. Nada se declara activo sin evidencia (§5 L1225): todo pending_audit.
import json,sys,os,pathlib,yaml,collections
sys.path.insert(0,str(pathlib.Path(__file__).parent))
GRAPH=sys.argv[1] if len(sys.argv)>1 else os.path.join(os.environ.get("WORK_DIR","/workspace/work"),"out","j2_graph","graph.json")
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
    # D-37: esquema de la GUIA §5 (11 campos obligatorios por conexion):
    # id, nombre, origen, destino, protocolo, direccion, endpoint, estado, dependencias,
    # verificacion, observaciones. Se conservan los campos previos (from/to/via/...) para no
    # romper el comprobador ni las consultas ya escritas.
    out.append({"id":f"CON-{i:03d}",
        "name":f"{a}_to_{b}","source":a,"target":b,
        "protocol":"gateway_pending_audit","direction":"outbound","endpoint":None,
        "status":"pending_audit","dependencies":a,"verification":None,
        "notes":"pendiente de evidencia; par observado en el grafo j2",
        "from":a,"to":b,"via":"gateway_pending_audit","provides":b,"requires":a,
        "evidence":None,"observed_paths":paths[:5],"observed_edges":len(paths)})
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
