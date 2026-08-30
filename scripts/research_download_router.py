import json, shutil, subprocess, time, zipfile, stat
from pathlib import Path
ROOT=Path('.').resolve(); WORK=ROOT/'_work/router-oss'; SRC=WORK/'src'; PACK=WORK/'pack'; EXTRACT=WORK/'extract'; OUT=ROOT/'Download code router'
MANIFEST=OUT/'RESEARCH_DOWNLOAD_MANIFEST.jsonl'; LEDGER=OUT/'FAILURE_LEDGER.yml'
SPLIT_TARGET=12_000_000; MAX_ZIP=17_000_000; BATCH_LIMIT=90*1024*1024; CHUNK=8*1024*1024
REPOS=[('01','asyncpg','https://github.com/MagicStack/asyncpg.git'),('02','aiomysql','https://github.com/aio-libs/aiomysql.git'),('03','autogen','https://github.com/microsoft/autogen.git'),('04','Chart.js','https://github.com/chartjs/Chart.js.git'),('05','chroma','https://github.com/chroma-core/chroma.git'),('06','crewAI','https://github.com/crewAIInc/crewAI.git'),('07','cryptography','https://github.com/pyca/cryptography.git'),('08','dzhng-deep-research','https://github.com/dzhng/deep-research.git'),('09','agents-deep-research','https://github.com/qx-labs/agents-deep-research.git'),('10','docker-py','https://github.com/docker/docker-py.git'),('11','fastapi','https://github.com/fastapi/fastapi.git'),('12','gpt-researcher','https://github.com/assafelovic/gpt-researcher.git'),('13','guardrails','https://github.com/guardrails-ai/guardrails.git'),('14','haystack','https://github.com/deepset-ai/haystack.git'),('15','httpx','https://github.com/encode/httpx.git'),('16','plex','https://github.com/IBM/plex.git'),('17','langgraph','https://github.com/langchain-ai/langgraph.git'),('18','litellm','https://github.com/BerriAI/litellm.git'),('19','llama_index','https://github.com/run-llama/llama_index.git'),('20','lucide','https://github.com/lucide-icons/lucide.git'),('21','python-sdk','https://github.com/modelcontextprotocol/python-sdk.git'),('22','servers','https://github.com/modelcontextprotocol/servers.git'),('23','n8n','https://github.com/n8n-io/n8n.git'),('24','ollama','https://github.com/ollama/ollama.git'),('25','open_deep_research','https://github.com/langchain-ai/open_deep_research.git'),('26','phoenix','https://github.com/Arize-ai/phoenix.git'),('27','pydantic','https://github.com/pydantic/pydantic.git'),('28','pydantic-settings','https://github.com/pydantic/pydantic-settings.git'),('29','pydantic-ai','https://github.com/pydantic/pydantic-ai.git'),('30','pyyaml','https://github.com/yaml/pyyaml.git'),('31','qdrant','https://github.com/qdrant/qdrant.git'),('32','react','https://github.com/facebook/react.git'),('33','redis-py','https://github.com/redis/redis-py.git'),('34','ruflo','https://github.com/ruvnet/ruflo.git'),('35','starlette','https://github.com/encode/starlette.git'),('36','tailwindcss','https://github.com/tailwindlabs/tailwindcss.git'),('37','vllm','https://github.com/vllm-project/vllm.git'),('38','zustand','https://github.com/pmndrs/zustand.git'),('39','uvicorn','https://github.com/encode/uvicorn.git'),('40','gunicorn','https://github.com/benoitc/gunicorn.git'),('41','vite','https://github.com/vitejs/vite.git'),('42','TypeScript','https://github.com/microsoft/TypeScript.git'),('43','PyGithub','https://github.com/PyGithub/PyGithub.git'),('44','huggingface_hub','https://github.com/huggingface/huggingface_hub.git'),('45','python-dotenv','https://github.com/theskumar/python-dotenv.git'),('46','redis','https://github.com/redis/redis.git'),('47','postgres','https://github.com/postgres/postgres.git'),('48','websockets','https://github.com/websockets/websockets.git'),('49','prometheus','https://github.com/prometheus/prometheus.git'),('50','grafana','https://github.com/grafana/grafana.git')]
def run(c,cwd=None): subprocess.run(c,cwd=cwd,check=True,text=True)
def clone_retry(url,root):
    last=None
    for attempt in range(1,5):
        shutil.rmtree(root,ignore_errors=True)
        try:
            run(['git','clone','--depth=1','--no-tags',url,str(root)])
            return
        except subprocess.CalledProcessError as e:
            last=e
            if attempt<4: time.sleep(attempt*3)
    raise last
def stage_repo(slug,root):
    stage=PACK/f'{slug}_stage'; shutil.rmtree(stage,ignore_errors=True); stage.mkdir(parents=True)
    for p in root.rglob('*'):
        if not p.is_file(): continue
        rel=p.relative_to(root); target=stage/slug/rel; target.parent.mkdir(parents=True,exist_ok=True); size=p.stat().st_size
        if size<=CHUNK: shutil.copy2(p,target)
        else:
            d=target.parent/(target.name+'.chunks'); d.mkdir(parents=True,exist_ok=True)
            with p.open('rb') as f:
                i=0
                while True:
                    data=f.read(CHUNK)
                    if not data: break
                    (d/f'{target.name}.part-{i:04d}').write_bytes(data); i+=1
    return stage
def package(slug,root):
    stage=stage_repo(slug,root); full=PACK/f'{slug}_full.zip'; full.unlink(missing_ok=True)
    run(['zip','-q','-r','-9','-y',str(full.resolve()),'.'],cwd=stage)
    if full.stat().st_size<=SPLIT_TARGET:
        out=PACK/f'{slug}_0001.zip'; full.replace(out); shutil.rmtree(stage,ignore_errors=True); return [out]
    before=set(PACK.glob('*.zip')); run(['zipsplit','-n',str(SPLIT_TARGET),'-b',str(PACK.resolve()),str(full.resolve())]); full.unlink(missing_ok=True)
    made=[p for p in PACK.glob('*.zip') if p not in before]
    if not made: raise RuntimeError(f'zipsplit produced no parts for {slug}')
    out=[]
    for i,p in enumerate(sorted(made,key=lambda p:(p.stat().st_mtime,p.name)),1):
        q=PACK/f'{slug}_{i:04d}.zip'; p.replace(q); out.append(q)
    shutil.rmtree(stage,ignore_errors=True); return out
def safe_extract(z,dest):
    root=dest.resolve(); dest.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(z) as zf:
        if zf.testzip() is not None: raise RuntimeError(f'CRC FAIL: {z}')
        for info in zf.infolist():
            target=(dest/info.filename).resolve()
            if not target.is_relative_to(root): raise RuntimeError(f'UNSAFE ZIP PATH: {info.filename}')
            mode=info.external_attr >> 16
            if mode and stat.S_ISLNK(mode): raise RuntimeError(f'SYMLINK REJECTED: {info.filename}')
        zf.extractall(dest)
def verify_zip(z):
    if not z.exists() or z.stat().st_size<=0 or z.stat().st_size>MAX_ZIP: raise RuntimeError(f'ZIP SIZE FAIL: {z}')
    subprocess.run(['unzip','-tq',str(z)],check=True)
def append_failure(number,slug,exc):
    OUT.mkdir(parents=True,exist_ok=True)
    with LEDGER.open('a',encoding='utf-8') as f:
        f.write(f'failure:\n  target: "router-50"\n  failed_step: "{number}-{slug}"\n  root_cause: "{str(exc).replace(chr(34),chr(39))}"\n  status: "OPEN"\n\n')
def commit_batch():
    run(['git','add',str(OUT)])
    if subprocess.run(['git','diff','--cached','--quiet']).returncode==0:return
    run(['git','config','user.name','github-actions[bot]']); run(['git','config','user.email','41898282+github-actions[bot]@users.noreply.github.com']); run(['git','commit','-m','build(router-oss): batched forensic download evidence'])
    for attempt in range(1,4):
        try: run(['git','fetch','origin','main']); run(['git','rebase','origin/main']); run(['git','push','origin','HEAD:main']); return
        except subprocess.CalledProcessError:
            if attempt==3: raise
            time.sleep(attempt*2)
def clean_room():
    shutil.rmtree(OUT,ignore_errors=True); shutil.rmtree(WORK,ignore_errors=True); OUT.mkdir(parents=True); SRC.mkdir(parents=True); PACK.mkdir(parents=True); EXTRACT.mkdir(parents=True)
def verify_output():
    rows=[json.loads(x) for x in MANIFEST.read_text().splitlines() if x.strip()]
    if len(rows)!=50 or [int(x['number']) for x in rows]!=list(range(1,51)): raise RuntimeError('MANIFEST 50/50 FAIL')
    if any(x.get('status')!='COMPLETE' for x in rows): raise RuntimeError('MANIFEST COMPLETE FAIL')
    for n,slug,_ in REPOS:
        root=EXTRACT/slug
        if not root.exists() or not any(root.iterdir()): raise RuntimeError(f'EXTRACTION LOCATION FAIL {n} {slug}')
        for p in root.rglob('*'):
            if p.is_file():
                with p.open('rb') as f: head=f.read(300)
                if b'git-lfs.github.com/spec/' in head or b'version https://git-lfs.github.com/spec' in head: raise RuntimeError(f'LFS MATERIAL FAIL {p}')
    (OUT/'FINAL_FORENSIC_REPORT.json').write_text(json.dumps({'status':'PASS','components':50,'manifest_rows':50,'contiguous_ids':True,'crc':'PASS','safe_extraction':'PASS'},indent=2))
clean_room(); batch_bytes=0
for number,slug,url in REPOS:
    try:
        root=SRC/slug; clone_retry(url,root); sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(); shutil.rmtree(root/'.git',ignore_errors=True)
        parts=package(slug,root); extract_root=EXTRACT/slug; shutil.rmtree(extract_root,ignore_errors=True)
        for z in parts:
            verify_zip(z); shutil.copy2(z,OUT/z.name); safe_extract(z,extract_root); batch_bytes+=z.stat().st_size
        if not any(extract_root.iterdir()): raise RuntimeError(f'EMPTY EXTRACTION {slug}')
        with MANIFEST.open('a') as f: f.write(json.dumps({'number':int(number),'slug':slug,'source':url,'source_commit':sha,'parts':len(parts),'status':'COMPLETE'},sort_keys=True)+'\n')
        shutil.rmtree(PACK,ignore_errors=True); PACK.mkdir(parents=True)
        if batch_bytes>=BATCH_LIMIT: commit_batch(); batch_bytes=0
    except Exception as exc:
        append_failure(number,slug,exc)
        raise
verify_output(); commit_batch(); print('ROUTER 50/50 FORENSIC PASS')
