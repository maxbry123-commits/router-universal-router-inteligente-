import ast, json, os, shutil, subprocess, time, zipfile
from pathlib import Path

ROOT = Path('.').resolve()
WORK = ROOT / '_work/router-oss'
SRC = WORK / 'src'
PACK = WORK / 'pack'
OUT = ROOT / 'Download code router'
MANIFEST = OUT / 'RESEARCH_DOWNLOAD_MANIFEST.jsonl'
FAILURE_LEDGER = OUT / 'FAILURE_LEDGER.yml'
SPLIT_TARGET = 12000000
MAX_ZIP = 17000000
CHUNK = 8 * 1024 * 1024

REPOS = [('01','asyncpg','https://github.com/MagicStack/asyncpg.git'),('02','aiomysql','https://github.com/aio-libs/aiomysql.git'),('03','autogen','https://github.com/microsoft/autogen.git'),('04','Chart.js','https://github.com/chartjs/Chart.js.git'),('05','chroma','https://github.com/chroma-core/chroma.git'),('06','crewAI','https://github.com/crewAIInc/crewAI.git'),('07','cryptography','https://github.com/pyca/cryptography.git'),('08','dzhng-deep-research','https://github.com/dzhng/deep-research.git'),('09','agents-deep-research','https://github.com/qx-labs/agents-deep-research.git'),('10','docker-py','https://github.com/docker/docker-py.git'),('11','fastapi','https://github.com/fastapi/fastapi.git'),('12','gpt-researcher','https://github.com/assafelovic/gpt-researcher.git'),('13','guardrails','https://github.com/guardrails-ai/guardrails.git'),('14','haystack','https://github.com/deepset-ai/haystack.git'),('15','httpx','https://github.com/encode/httpx.git'),('16','plex','https://github.com/IBM/plex.git'),('17','langgraph','https://github.com/langchain-ai/langgraph.git'),('18','litellm','https://github.com/BerriAI/litellm.git'),('19','llama_index','https://github.com/run-llama/llama_index.git'),('20','lucide','https://github.com/lucide-icons/lucide.git'),('21','python-sdk','https://github.com/modelcontextprotocol/python-sdk.git'),('22','servers','https://github.com/modelcontextprotocol/servers.git'),('23','n8n','https://github.com/n8n-io/n8n.git'),('24','ollama','https://github.com/ollama/ollama.git'),('25','open_deep_research','https://github.com/langchain-ai/open_deep_research.git'),('26','phoenix','https://github.com/Arize-ai/phoenix.git'),('27','pydantic','https://github.com/pydantic/pydantic.git'),('28','pydantic-settings','https://github.com/pydantic/pydantic-settings.git'),('29','pydantic-ai','https://github.com/pydantic/pydantic-ai.git'),('30','pyyaml','https://github.com/yaml/pyyaml.git'),('31','qdrant','https://github.com/qdrant/qdrant.git'),('32','react','https://github.com/facebook/react.git'),('33','redis-py','https://github.com/redis/redis-py.git'),('34','ruflo','https://github.com/ruvnet/ruflo.git'),('35','starlette','https://github.com/encode/starlette.git'),('36','tailwindcss','https://github.com/tailwindlabs/tailwindcss.git'),('37','vllm','https://github.com/vllm-project/vllm.git'),('38','zustand','https://github.com/pmndrs/zustand.git'),('39','uvicorn','https://github.com/encode/uvicorn.git'),('40','gunicorn','https://github.com/benoitc/gunicorn.git'),('41','vite','https://github.com/vitejs/vite.git'),('42','TypeScript','https://github.com/microsoft/TypeScript.git'),('43','PyGithub','https://github.com/PyGithub/PyGithub.git'),('44','huggingface_hub','https://github.com/huggingface/huggingface_hub.git'),('45','python-dotenv','https://github.com/theskumar/python-dotenv.git'),('46','redis','https://github.com/redis/redis.git'),('47','postgres','https://github.com/postgres/postgres.git'),('48','websockets','https://github.com/websockets/websockets.git'),('49','prometheus','https://github.com/prometheus/prometheus.git'),('50','grafana','https://github.com/grafana/grafana.git')]


def run(cmd, cwd=None):
    return subprocess.run(cmd, cwd=cwd, check=True, text=True)


def write_failure(step, error):
    OUT.mkdir(parents=True, exist_ok=True)
    FAILURE_LEDGER.write_text(
        'failure:\n'
        '  target: "<ACTIVE_TARGET>"\n'
        '  workflow: "<ACTIVE_WORKFLOW>"\n'
        f'  failed_step: "{step}"\n'
        f'  root_cause: "{str(error).replace(chr(34), chr(39))}"\n'
        '  status: "OPEN"\n', encoding='utf-8')


def clone_retry(url, root):
    last = None
    for attempt in range(1, 5):
        shutil.rmtree(root, ignore_errors=True)
        try:
            run(['git', 'clone', '--depth=1', '--no-tags', '--filter=blob:none', url, str(root)])
            return
        except subprocess.CalledProcessError as exc:
            last = exc
            print(f'CLONE RETRY {attempt}/4 {url}', flush=True)
            time.sleep(attempt * 3)
    raise last


def chunk_big(root):
    for p in list(root.rglob('*')):
        if not p.is_file() or '.git' in p.parts or p.stat().st_size <= CHUNK:
            continue
        d = p.parent / (p.name + '.chunks')
        d.mkdir(exist_ok=True)
        with p.open('rb') as f:
            i = 0
            while True:
                data = f.read(CHUNK)
                if not data:
                    break
                (d / f'{p.name}.part-{i:04d}').write_bytes(data)
                i += 1
        p.unlink()


def safe_extract(zfile, dest):
    root = dest.resolve()
    for info in zfile.infolist():
        target = (dest / info.filename).resolve()
        if not target.is_relative_to(root):
            raise RuntimeError(f'UNSAFE ZIP PATH: {info.filename}')
    zfile.extractall(dest)


def verify_zip(path):
    if not path.exists() or path.stat().st_size <= 0 or path.stat().st_size > MAX_ZIP:
        raise RuntimeError(f'ZIP SIZE/EXISTENCE FAIL: {path}')
    with zipfile.ZipFile(path) as zf:
        bad = zf.testzip()
        if bad is not None:
            raise RuntimeError(f'CRC FAIL: {path}:{bad}')
        for info in zf.infolist():
            root = (path.parent / '_verify').resolve()
            target = (root / info.filename).resolve()
            if not target.is_relative_to(root):
                raise RuntimeError(f'PATH TRAVERSAL FAIL: {info.filename}')


def commit_and_push(label):
    run(['git', 'add', '-A'])
    if subprocess.run(['git', 'diff', '--cached', '--quiet']).returncode == 0:
        return
    run(['git', 'config', 'user.name', 'github-actions[bot]'])
    run(['git', 'config', 'user.email', '41898282+github-actions[bot]@users.noreply.github.com'])
    run(['git', 'commit', '-m', f'build(router-oss): {label}'])
    for attempt in range(1, 8):
        try:
            run(['git', 'fetch', 'origin', 'main'])
            run(['git', 'rebase', 'origin/main'])
            run(['git', 'push', 'origin', 'HEAD:main'])
            return
        except subprocess.CalledProcessError as exc:
            if attempt == 7:
                raise
            print(f'PUSH RETRY {attempt}/7', flush=True)
            time.sleep(attempt * 3)


def static_preflight():
    workflow = ROOT / '.github/workflows/wordflow-router-oss.yml'
    script = ROOT / 'scripts/research_download_router.py'
    text = workflow.read_text(encoding='utf-8')
    if 'lfs: false' not in text or 'git lfs' in text or 'GIT_LFS_' in text:
        raise RuntimeError('LFS operational policy FAIL')
    compile(script.read_text(encoding='utf-8'), str(script), 'exec')
    tree = ast.parse(script.read_text(encoding='utf-8'))
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == 'clone_retry':
            if any(isinstance(x, ast.Call) and isinstance(x.func, ast.Name) and x.func.id == 'clone_retry' for x in ast.walk(node)):
                raise RuntimeError('clone_retry direct self-recursion detected')


def clean_room():
    shutil.rmtree(OUT, ignore_errors=True)
    shutil.rmtree(WORK, ignore_errors=True)
    for _, slug, _ in REPOS:
        shutil.rmtree(ROOT / slug, ignore_errors=True)
    OUT.mkdir(parents=True, exist_ok=True)
    SRC.mkdir(parents=True, exist_ok=True)
    PACK.mkdir(parents=True, exist_ok=True)


def verify_output():
    rows = [json.loads(x) for x in MANIFEST.read_text(encoding='utf-8').splitlines() if x.strip()]
    ids = [int(x['number']) for x in rows]
    if ids != list(range(1, 51)) or len(rows) != 50:
        raise RuntimeError(f'MANIFEST CARDINALITY FAIL: {len(rows)} rows {ids}')
    if any(x.get('status') != 'COMPLETE' or int(x.get('parts', 0)) < 1 for x in rows):
        raise RuntimeError('MANIFEST STATUS FAIL')
    for number, slug, _ in REPOS:
        root = ROOT / slug
        if not root.exists() or not any(root.iterdir()):
            raise RuntimeError(f'EXTRACTION LOCATION FAIL: {number} {slug}')
        for p in root.rglob('*'):
            if p.is_file():
                try:
                    data = p.read_bytes()[:200]
                except OSError:
                    continue
                if b'git-lfs.github.com/spec/' in data or b'version https://git-lfs.github.com/spec' in data:
                    raise RuntimeError(f'LFS MATERIAL FAIL: {p}')
    (OUT / 'FINAL_FORENSIC_REPORT.json').write_text(json.dumps({'status':'PASS','components':50,'manifest_rows':len(rows),'contiguous_ids':True}, indent=2), encoding='utf-8')


static_preflight()
clean_room()

for number, slug, url in REPOS:
    print(f'===== ROUTER {number}/50: {slug} =====', flush=True)
    root = SRC / slug
    try:
        clone_retry(url, root)
        sha = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
        shutil.rmtree(root / '.git', ignore_errors=True)
        chunk_big(root)
        full = PACK / f'{slug}_full.zip'
        run(['zip', '-q', '-r', '-9', '-y', str(full.resolve()), '.'], cwd=root)
        parts = []
        if full.stat().st_size <= SPLIT_TARGET:
            out = PACK / f'{slug}_0001.zip'
            full.replace(out)
            parts = [out]
        else:
            before = set(PACK.glob('*.zip'))
            run(['zipsplit', '-n', str(SPLIT_TARGET), '-b', str(PACK.resolve()), str(full.resolve())])
            made = [p for p in PACK.glob('*.zip') if p not in before]
            for i, p in enumerate(sorted(made, key=lambda p: (p.stat().st_mtime, p.name)), 1):
                q = PACK / f'{slug}_{i:04d}.zip'
                p.replace(q)
                parts.append(q)
            full.unlink(missing_ok=True)
        for z in parts:
            verify_zip(z)
        dest = ROOT / slug
        shutil.rmtree(dest, ignore_errors=True)
        dest.mkdir(parents=True, exist_ok=True)
        for z in parts:
            shutil.copy2(z, dest / z.name)
            with zipfile.ZipFile(z) as zf:
                safe_extract(zf, dest)
        if not any(dest.iterdir()):
            raise RuntimeError(f'EMPTY EXTRACTION: {slug}')
        with MANIFEST.open('a', encoding='utf-8') as f:
            f.write(json.dumps({'number': int(number), 'slug': slug, 'source': url, 'source_commit': sha, 'parts': len(parts), 'status': 'COMPLETE'}, sort_keys=True) + '\n')
        shutil.rmtree(root, ignore_errors=True)
        shutil.rmtree(PACK, ignore_errors=True)
        PACK.mkdir(parents=True, exist_ok=True)
        commit_and_push(f'{number}-{slug}')
    except Exception as exc:
        write_failure(f'ROUTER {number} {slug}', exc)
        raise

verify_output()
commit_and_push('final-evidence-50-pass')
print('===== ROUTER 50/50 FORENSIC PASS =====', flush=True)
