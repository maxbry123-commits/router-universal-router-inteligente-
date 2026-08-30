import json, shutil, subprocess, time, zipfile
from pathlib import Path
ROOT=Path('.').resolve()
WORK=ROOT/'_work/router-oss'; SRC=WORK/'src'; PACK=WORK/'pack'
MANIFEST=ROOT/'Download code router'/'RESEARCH_DOWNLOAD_MANIFEST.jsonl'
SPLIT_TARGET=12000000; MAX_ZIP=17000000; BATCH_LIMIT=90*1024*1024; CHUNK=8*1024*1024
REPOS=[('01','asyncpg','https://github.com/MagicStack/asyncpg.git'),('02','aiomysql','https://github.com/aio-libs/aiomysql.git'),('03','autogen','https://github.com/microsoft/autogen.git'),('04','Chart.js','https://github.com/chartjs/Chart.js.git'),('05','chroma','https://github.com/chroma-core/chroma.git'),('06','crewAI','https://github.com/crewAIInc/crewAI.git'),('07','cryptography','https://github.com/pyca/cryptography.git'),('08','dzhng-deep-research','https://github.com/dzhng/deep-research.git'),('09','agents-deep-research','https://github.com/qx-labs/agents-deep-research.git'),('10','docker-py','https://github.com/docker/docker-py.git'),('11','fastapi','https://github.com/fastapi/fastapi.git'),('12','gpt-researcher','https://github.com/assafelovic/gpt-researcher.git'),('13','guardrails','https://github.com/guardrails-ai/guardrails.git'),('14','haystack','https://github.com/deepset-ai/haystack.git'),('15','httpx','https://github.com/encode/httpx.git'),('16','plex','https://github.com/IBM/plex.git'),('17','langgraph','https://github.com/langchain-ai/langgraph.git'),('18','litellm','https://github.com/BerriAI/litellm.git'),('19','llama_index','https://github.com/run-llama/llama_index.git'),('20','lucide','https://github.com/lucide-icons/lucide.git'),('21','python-sdk','https://github.com/modelcontextprotocol/python-sdk.git'),('22','servers','https://github.com/modelcontextprotocol/servers.git'),('23','n8n','https://github.com/n8n-io/n8n.git'),('24','ollama','https://github.com/ollama/ollama.git'),('25','open_deep_research','https://github.com/langchain-ai/open_deep_research.git'),('26','phoenix','https://github.com/Arize-ai/phoenix.git'),('27','pydantic','https://github.com/pydantic/pydantic.git'),('28','pydantic-settings','https://github.com/pydantic/pydantic-settings.git'),('29','pydantic-ai','https://github.com/pydantic/pydantic-ai.git'),('30','pyyaml','https://github.com/yaml/pyyaml.git'),('31','qdrant','https://github.com/qdrant/qdrant.git'),('32','react','https://github.com/facebook/react.git'),('33','redis-py','https://github.com/redis/redis-py.git'),('34','ruflo','https://github.com/ruvnet/ruflo.git'),('35','starlette','https://github.com/encode/starlette.git'),('36','tailwindcss','https://github.com/tailwindlabs/tailwindcss.git'),('37','vllm','https://github.com/vllm-project/vllm.git'),('38','zustand','https://github.com/pmndrs/zustand.git'),('39','uvicorn','https://github.com/encode/uvicorn.git'),('40','gunicorn','https://github.com/benoitc/gunicorn.git'),('41','vite','https://github.com/vitejs/vite.git'),('42','TypeScript','https://github.com/microsoft/TypeScript.git'),('43','PyGithub','https://github.com/PyGithub/PyGithub.git'),('44','huggingface_hub','https://github.com/huggingface/huggingface_hub.git'),('45','python-dotenv','https://github.com/theskumar/python-dotenv.git'),('46','redis','https://github.com/redis/redis.git'),('47','postgres','https://github.com/postgres/postgres.git'),('48','websockets','https://github.com/websockets/websockets.git'),('49','prometheus','https://github.com/prometheus/prometheus.git'),('50','grafana','https://github.com/grafana/grafana.git')]
def run(c,cwd=None): subprocess.run(c,cwd=cwd,check=True)
def clone_retry(url, root):
    last=None
    for attempt in range(1,5):
        shutil.rmtree(root,ignore_errors=True)
        try:
            run(['git','clone','--depth','1','--no-tags',url,str(root)])
            return
        except subprocess.CalledProcessError as e:
            last=e
            print(f'CLONE RETRY {attempt}/4 {url}', flush=True)
            time.sleep(attempt*3)
    raise last
def done(slug):
    if not MANIFEST.exists(): return False
    return any((lambda d:d.get('slug')==slug and d.get('status')=='COMPLETE')(json.loads(x)) for x in MANIFEST.read_text().splitlines() if x.strip())
def chunk_big(root):
    for p in list(root.rglob('*')):
        if not p.is_file(): continue
        if p.stat().st_size<=CHUNK: continue
        d=p.parent/(p.name+'.chunks'); d.mkdir(exist_ok=True)
        with p.open('rb') as f:
            i=0
            while True:
                data=f.read(CHUNK)
                if not data: break
                (d/f'{p.name}.part-{i:04d}').write_bytes(data); i+=1
        p.unlink()
def push(label):
    for attempt in range(1,8):
        try:
            run(['git','fetch','origin','main']); run(['git','rebase','origin/main']); run(['git','push','origin','HEAD:main']); print(f'PUSH PASS {label} attempt {attempt}'); return
        except subprocess.CalledProcessError:
            if attempt==7: raise
            time.sleep(attempt*3)
def commit(n,label):
    if not n:return
    run(['git','add','-A'])
    if subprocess.run(['git','diff','--cached','--quiet']).returncode==0:return
    run(['git','config','user.name','github-actions[bot]']); run(['git','config','user.email','41898282+github-actions[bot]@users.noreply.github.com']); run(['git','commit','-m',f'build(router-oss): {label} ({n} bytes)']); push(label)
def extract_to_root(slug, zips):
    dest=ROOT/slug; shutil.rmtree(dest,ignore_errors=True); dest.mkdir(parents=True, exist_ok=True)
    for z,size in zips:
        shutil.copy2(z, dest/z.name)
        with zipfile.ZipFile(z) as zf: zf.extractall(dest)
MANIFEST.parent.mkdir(parents=True, exist_ok=True); SRC.mkdir(parents=True, exist_ok=True); PACK.mkdir(parents=True, exist_ok=True)
batch=batch_no=0
for number,slug,url in REPOS:
    print(f'===== QUEUE {number}: {slug} =====')
    if done(slug): print(f'{slug}: COMPLETE; skipping'); continue
    root=SRC/slug; shutil.rmtree(root,ignore_errors=True)
    run(['git','clone','--depth','1','--no-tags',url,str(root)])
    sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(); shutil.rmtree(root/'.git',ignore_errors=True)
    chunk_big(root)
    full=PACK/f'{slug}_full.zip'; full.unlink(missing_ok=True)
    run(['zip','-q','-r','-9','-y',str(full.resolve()),'.'],cwd=root)
    parts=[]
    if full.stat().st_size<=SPLIT_TARGET:
        out=PACK/f'{slug}_0001.zip'; full.replace(out); parts=[(out,out.stat().st_size)]
    else:
        before=set(PACK.glob('*.zip')); run(['zipsplit','-n',str(SPLIT_TARGET),'-b',str(PACK.resolve()),str(full.resolve())]); full.unlink(missing_ok=True)
        made=[p for p in PACK.glob('*.zip') if p not in before]
        for i,p in enumerate(sorted(made,key=lambda p:(p.stat().st_mtime,p.name)),1):
            q=PACK/f'{slug}_{i:04d}.zip'; p.replace(q); parts.append((q,q.stat().st_size))
    for z,sz in parts:
        if sz>MAX_ZIP: raise RuntimeError(f'FORENSIC FAIL: ZIP exceeds MAX_ZIP {z} {sz}')
        with zipfile.ZipFile(z) as zf:
            bad=zf.testzip()
            if bad is not None: raise RuntimeError(f'FORENSIC FAIL: CRC {z}:{bad}')
    extract_to_root(slug, parts)
    size=sum(s for _,s in parts)
    if batch and batch+size>BATCH_LIMIT: commit(batch,f'{batch_no:03d}'); batch=0; batch_no+=1
    batch+=size
    with MANIFEST.open('a') as f: f.write(json.dumps({'number':int(number),'slug':slug,'source':url,'source_commit':sha,'parts':len(parts),'status':'COMPLETE'},sort_keys=True)+'\n')
    shutil.rmtree(root,ignore_errors=True); shutil.rmtree(PACK,ignore_errors=True); PACK.mkdir(parents=True, exist_ok=True)
commit(batch,f'{batch_no:03d}-final'); print('===== QUEUE ROUTER 50 COMPLETE =====')
