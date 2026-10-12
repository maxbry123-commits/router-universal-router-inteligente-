"""Reinicio del Router con el codigo nuevo (misma via que usa el kernel). RR_MODE=CHECK: solo lee y compara. RR_MODE=APPLY: respalda y actualiza el paquete del bucket, relanza, valida y retira los Routers viejos. Nunca imprime secretos."""
import os, sys, io, json, gzip, base64, tarfile, hashlib, time, shutil, pathlib, urllib.parse, urllib.request as ur, urllib.error
from huggingface_hub import HfFileSystem, HfApi
MODE = os.environ.get('RR_MODE', 'CHECK'); NS = 'COMAND-CENTER-1'
BASE = 'buckets/%s/yaiwes-memoria-storage/router-inteligente-universal' % NS
REPO = 'maxbry123-commits/router-universal-router-inteligente-'; BASE_SHA = '254e5b1a1b61a6fa3bddbe2d403c06ae7cc4edcf'
RI = 'router inteligente universal/'
ARCHIVOS = [RI + 'plugins/fichas_qwen/plugin.py'] + [RI + 'plugins/fichas_qwen/fichas/%s.json' % n for n in ('ficha1-modelos', 'ficha2-dag-codigo', 'ficha3-frontend', 'ficha4-workflow-yaiwes')]
VIEJOS = ['6acc8a9d095c57808932967a', '6acca1dcfee2c900701a4256']
def out(**k): print(json.dumps(k, ensure_ascii=False), flush=True)
def gh(ref, path): return ur.urlopen('https://raw.githubusercontent.com/%s/%s/%s' % (REPO, ref, urllib.parse.quote(path)), timeout=60).read()
sha = lambda b: hashlib.sha256(b).hexdigest()[:12]
fs = HfFileSystem(token=os.environ['HF_TOKEN'], skip_instance_cache=True)
t0 = time.time()
with fs.open(BASE + '/codigo/router-bundle.tar.gz', 'rb', block_size=8 << 20) as r, open('/tmp/b.tgz', 'wb') as w: shutil.copyfileobj(r, w, 8 << 20)
out(paso='bundle descargado', MB=round(os.path.getsize('/tmp/b.tgz') / 1e6), seg=round(time.time() - t0))
try: out(paso='router-bundle.json', contenido=json.loads(fs.cat_file(BASE + '/codigo/router-bundle.json')))
except Exception as e: out(paso='router-bundle.json', error=str(e)[:100])
enb = {}; nombres = []
with tarfile.open('/tmp/b.tgz', 'r|gz') as tar:
    for m in tar:
        if m.isreg() and m.name in ARCHIVOS: enb[m.name] = tar.extractfile(m).read()
        elif m.name.startswith(RI + 'Banco de claves/'): tar.extract(m, '/tmp/kb', filter='data')
        if m.isreg() and m.name.endswith('fichas_qwen/plugin.py') and m.name not in ARCHIVOS: nombres.append(m.name)
for a in ARCHIVOS:
    base = sha(gh(BASE_SHA, a)); main = sha(gh('main', a)); bun = sha(enb[a]) if a in enb else None
    out(archivo=a.replace(RI, ''), en_bundle=bun, base_254e5b1a=base, main_nuevo=main, bundle_igual_a_base=(bun == base), ya_actualizado=(bun == main))
out(otros_plugin_py=nombres[:3])
sys.path.insert(0, '/tmp/kb/' + RI + 'Banco de claves')
from secret_bank.vault import Vault
pathlib.Path('/tmp/kv.db').write_bytes(gzip.decompress(base64.b64decode(fs.cat_file(BASE + '/banco/vault.db.gz.b64'))))
def hidratar():
    v = Vault(pathlib.Path('/tmp/kv.db')).unlock(os.environ['RIU_VAULT_PASSPHRASE'])
    os.environ['HF_TOKEN'] = v.get_secret('huggingface/token-1-new'); os.environ['HF_CONTROL_JOBS_TOKEN'] = os.environ['HF_TOKEN']
    os.environ['GITHUB_PERSONAL_ACCESS_TOKEN'] = v.get_secret('github/director-full'); os.environ['RIU_ROUTER_API_KEY'] = v.get_secret('router/runtime-admin-32gb')
    os.environ['RIU_DIRECTOR_KEY_HASH'] = v.get_secret('router/runtime-director-hash'); keys = {}
    for x in v.list():
        if x['enabled'] and x['provider'] == 'router' and 'hash' not in x['account']:
            try: keys[v.get_secret(x['credential_ref'])] = 'chat-ui' if 'chat-ui' in x['account'] else x['account']
            except Exception: pass
    os.environ['RIU_AGENT_API_KEYS'] = json.dumps(keys); os.environ['RIU_AGENT_API_KEYS_2'] = '{}'; os.environ['RIU_PUBLIC_CHAT_KEY'] = v.get_secret('router/chat-ui-director')
    return v
try:
    v = hidratar(); out(paso='banco abierto', ok=True, secretos_del_router=len([1 for x in v.list() if x['provider'] == 'router']), claves_agente=len(json.loads(os.environ['RIU_AGENT_API_KEYS'])), tiene_ficha_clave=bool(os.environ.get('FICHA_CLAVE_BANCO')))
except Exception as e: out(paso='banco abierto', ok=False, error=type(e).__name__ + ': ' + str(e)[:120]); sys.exit(2)
if MODE != 'APPLY': out(paso='FIN_CHECK'); sys.exit(0)
if any(a not in enb or sha(enb[a]) != sha(gh(BASE_SHA, a)) for a in ARCHIVOS) and not os.environ.get('RR_FORCE'): out(paso='ABORTA', motivo='el paquete tiene cambios que no estan en GitHub: no se pisa sin RR_FORCE'); sys.exit(3)
nuevo = {a: gh('main', a) for a in ARCHIVOS}
fs.put_file('/tmp/b.tgz', BASE + '/codigo/router-bundle.tar.gz.bak-20261012-pre-fastreply2'); out(paso='respaldo subido', ruta='router-bundle.tar.gz.bak-20261012-pre-fastreply2')
vistos = set()
with tarfile.open('/tmp/b.tgz', 'r|gz') as src, tarfile.open('/tmp/n.tgz', 'w|gz', compresslevel=6) as dst:
    for m in src:
        if m.isreg() and m.name in nuevo:
            ti = tarfile.TarInfo(m.name); ti.size = len(nuevo[m.name]); ti.mtime = int(time.time()); ti.mode = m.mode; ti.uid, ti.gid, ti.uname, ti.gname = m.uid, m.gid, m.uname, m.gname
            dst.addfile(ti, io.BytesIO(nuevo[m.name])); vistos.add(m.name)
        elif m.isreg(): dst.addfile(m, src.extractfile(m))
        else: dst.addfile(m)
assert vistos == set(ARCHIVOS), vistos
fs.put_file('/tmp/n.tgz', BASE + '/codigo/router-bundle.tar.gz'); out(paso='paquete nuevo subido', MB=round(os.path.getsize('/tmp/n.tgz') / 1e6), reemplazados=len(vistos))
hh = hashlib.sha256()
with open('/tmp/n.tgz', 'rb') as ff:
    for blk in iter(lambda: ff.read(8 << 20), b''): hh.update(blk)
try: oldj = json.loads(fs.cat_file(BASE + '/codigo/router-bundle.json'))
except Exception: oldj = {}
fs.pipe_file(BASE + '/codigo/router-bundle.json.bak-20261012-pre-fastreply2', json.dumps(oldj, ensure_ascii=False).encode())
oldj.update({'sha256': hh.hexdigest(), 'bytes': os.path.getsize('/tmp/n.tgz'), 'commit': 'main 7107f947ae: respuesta rapida fichas 1-4', 'ts': time.time(), 'agregado': str(oldj.get('agregado', '')) + ' + respuesta rapida (fast_reply) fichas 1-4'})
fs.pipe_file(BASE + '/codigo/router-bundle.json', json.dumps(oldj, ensure_ascii=False).encode()); out(paso='router-bundle.json actualizado', respaldo='router-bundle.json.bak-20261012-pre-fastreply2')
# relanzar como lo hace el kernel (+ FICHA_CLAVE_BANCO, que el kernel no incluye)
CMD = ['bash', '-lc', "set -e\npip install -q huggingface_hub cryptography httpx 'uvicorn[standard]' fastapi pydantic psutil mcp beautifulsoup4\npython - <<'PY'\nimport os,io,tarfile\nfrom huggingface_hub import HfFileSystem\nf=HfFileSystem(token=os.environ['HF_TOKEN'])\nb='buckets/COMAND-CENTER-1/yaiwes-memoria-storage/router-inteligente-universal'\ntarfile.open(fileobj=io.BytesIO(f.cat_file(b+'/codigo/router-bundle.tar.gz')),mode='r:gz').extractall('/app',filter='data')\nimport base64,gzip\nvp,vs=os.environ.get('RIU_VAULT_PATH'),os.environ.get('RIU_VAULT_SOURCE')\nif vp and vs:\n    os.makedirs(os.path.dirname(vp),exist_ok=True)\n    open(vp,'wb').write(gzip.decompress(base64.b64decode(f.cat_file(vs))))\nPY\ncd '/app/router inteligente universal'\npython riu_kernel.py --watch &\nexec uvicorn public_chat_app:app --host 0.0.0.0 --port 8000 --timeout-keep-alive 120"]
ENV = {'HF_BUCKET_ID': NS + '/yaiwes-memoria-storage', 'RIU_DATA_DIR': '/tmp/riu-data', 'RIU_VAULT_PATH': '/tmp/riu-data/riu_vault.db', 'RIU_VAULT_SOURCE': BASE + '/banco/vault.db.gz.b64', 'RIU_VAULT_PROVIDERS_SOURCE': BASE + '/banco/providers.json', 'RIU_AUTOSYNC_SECONDS': '60', 'RIU_CHAT_ALLOW_PROVIDER_LIVE': '1', 'RIU_G2_GROQ_MODEL': 'qwen/qwen3.8-27b', 'RIU_CODE_BUNDLE': BASE + '/codigo/router-bundle.tar.gz', 'RIU_ROOT': 'router-inteligente-universal', 'RIU_FLAVOR': 'cpu-basic', 'RIU_JOB_ROLE': 'main', 'HF_AUTOSCALE_MAX_WORKERS': '1', 'HF_HUB_DISABLE_PROGRESS_BARS': '1', 'RIU_CORS_ORIGINS': '*'}
NOMBRES = ['HF_TOKEN', 'HF_CONTROL_JOBS_TOKEN', 'GITHUB_PERSONAL_ACCESS_TOKEN', 'RIU_VAULT_PASSPHRASE', 'RIU_ROUTER_API_KEY', 'RIU_AGENT_API_KEYS', 'RIU_AGENT_API_KEYS_2', 'RIU_DIRECTOR_KEY_HASH', 'RIU_PUBLIC_CHAT_KEY', 'FICHA_CLAVE_BANCO']
j = HfApi(token=os.environ['HF_TOKEN']).run_job(image='python:3.12', command=CMD, flavor='cpu-basic', timeout='48h', expose=[8000], expose_public=[8000], env=ENV, secrets={k: os.environ[k] for k in NOMBRES if os.environ.get(k)}, namespace=NS, labels={'name': 'yaiwes-router-16gb'})
URL = 'https://' + j.id + '--8000.hf.jobs'; out(paso='router nuevo lanzado', job_id=j.id, url=URL)
KEY = os.environ['RIU_ROUTER_API_KEY']; H = {'X-API-Key': KEY, 'Authorization': 'Bearer ' + KEY, 'Content-Type': 'application/json'}
def http(met, path, body=None, t=40):
    try:
        with ur.urlopen(ur.Request(URL + path, data=json.dumps(body).encode() if body is not None else None, headers=H, method=met), timeout=t) as rr: return rr.status, json.load(rr)
    except urllib.error.HTTPError as e: return e.code, {}
    except Exception: return 0, {}
sano = False
for _ in range(90):
    if http('GET', '/health', t=10)[0] == 200: sano = True; break
    time.sleep(8)
out(paso='health', ok=sano, seg=round(time.time() - t0))
if not sano: out(paso='ABORTA', motivo='el router nuevo no responde; los viejos siguen vivos'); sys.exit(4)
s, d = http('GET', '/chat/providers'); out(paso='banco/proveedores', status=s, configurados=[p.get('id') for p in d.get('providers', []) if p.get('configured')])
if not any(p.get('configured') for p in d.get('providers', [])): s2, _ = http('POST', '/vault/unlock', {'passphrase': os.environ['RIU_VAULT_PASSPHRASE']}); out(paso='abrir banco', status=s2)
def chat(base, body, lim=400):
    s, d = http('POST', base + 'chat_async', body); pid = (d.get('result') or {}).get('proceso_id'); t = time.time()
    while pid and time.time() - t < lim:
        time.sleep(2); s, d = http('POST', base + 'resultado', {'proceso_id': pid}); r = d.get('result') or {}
        if r.get('estado') != 'procesando': return r
    return {'estado': 'SIN_RESPUESTA'}
F = '/plugins/fichas_qwen/call/'; P = '/plugins/puente_chat/call/'; ok = []
r = chat(P, {'model': 'nv-nemotron-super', 'messages': [{'role': 'user', 'content': 'Responde solamente OK'}], 'max_tokens': 16, 'sesion': 'rr-default'}); c = ((r.get('choices') or [{}])[0].get('message') or {}).get('content'); ok.append(bool(c)); out(prueba='selector ninguno / Nvidia groq team (harness puente_chat)', ok=bool(c), respuesta=str(c)[:40])
for nom, fi, mod in [('Team qwen (ficha 1) Qwen 3.8 Flash', '1', 'Qwen 3.8 Flash'), ('Ask consil code (ficha 2)', '2', ''), ('Ask consil frontend (ficha 3)', '3', '')]:
    r = chat(F, {'ficha_qwen': fi, 'modelo': mod or 'ficha-qwen38flash', 'messages': [{'role': 'user', 'content': 'Responde solo OK'}], 'sesion': 'rr-' + fi, 'fast_reply': True}); good = r.get('execution_path') == 'FAST_QA' and bool(r.get('reply')); ok.append(good)
    out(prueba=nom + ' con fast_reply', ok=good, execution_path=r.get('execution_path'), modelo=next((z.get('modelo') for z in (r.get('traza') or []) if z.get('modelo') not in (None, 'goals')), None), ms=r.get('ms'))
if all(ok):
    api = HfApi(token=os.environ['HF_TOKEN'])
    value = {'LIVE_URL': URL, 'job_id': j.id, 'flavor': 'cpu-basic', 'updated': time.time(), 'auth': 'X-API-Key', 'harnessUrl': URL + '/plugins/puente_chat/call'}
    apiurl = 'https://api.github.com/repos/' + REPO + '/contents/' + urllib.parse.quote(RI + 'LIVE_URL.json')
    gk = os.environ['GITHUB_PERSONAL_ACCESS_TOKEN']; gh_h = {'Authorization': 'Bearer ' + gk, 'Content-Type': 'application/json', 'User-Agent': 'yaiwes-rr'}
    old = json.load(ur.urlopen(ur.Request(apiurl + '?ref=main', headers=gh_h), timeout=30))
    ur.urlopen(ur.Request(apiurl, data=json.dumps({'message': 'Update active HF Router address [skip ci]', 'branch': 'main', 'sha': old['sha'], 'content': base64.b64encode(json.dumps(value, indent=2).encode()).decode()}).encode(), headers=gh_h, method='PUT'), timeout=30)
    fs.pipe_file(BASE + '/control/router-current.json', json.dumps({'url': URL, 'job_id': j.id, 'flavor': 'cpu-basic', 'started': time.time(), 'timeout_s': 172800}).encode()); out(paso='LIVE_URL publicada', url=URL)
    for vid in VIEJOS:
        try: api.cancel_job(job_id=vid, namespace=NS); out(paso='router viejo retirado', job=vid[-8:])
        except Exception as e: out(paso='router viejo NO retirado', job=vid[-8:], error=type(e).__name__)
    out(paso='FIN_APPLY', ok=True)
else: out(paso='VALIDACION_FALLIDA', detalle='no se publica LIVE_URL ni se retiran los routers viejos; el nuevo queda vivo para revisar', router_nuevo=j.id); sys.exit(5)
