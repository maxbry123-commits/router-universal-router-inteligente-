"""Publica el Router nuevo (ya arriba y con el codigo nuevo) si NO es peor que el actual: mismas pruebas que el sentinela del kernel (responde cualquiera de dos modelos) + fichas 1-3 con fast_reply. Si pasa: publica LIVE_URL y retira los Routers viejos. Nunca imprime secretos."""
import os, sys, json, gzip, base64, tarfile, time, shutil, pathlib, urllib.parse, urllib.request as ur, urllib.error
from huggingface_hub import HfFileSystem, HfApi
NS = 'COMAND-CENTER-1'; BASE = 'buckets/%s/yaiwes-memoria-storage/router-inteligente-universal' % NS; REPO = 'maxbry123-commits/router-universal-router-inteligente-'; RI = 'router inteligente universal/'
NUEVO = os.environ['RR_JOB']; VIEJOS = [x for x in os.environ.get('RR_VIEJOS', '').split(',') if x]; ACTUAL = VIEJOS[0] if VIEJOS else None
def out(**k): print(json.dumps(k, ensure_ascii=False), flush=True)
fs = HfFileSystem(token=os.environ['HF_TOKEN'], skip_instance_cache=True)
with fs.open(BASE + '/codigo/router-bundle.tar.gz', 'rb', block_size=8 << 20) as r, open('/tmp/b.tgz', 'wb') as w: shutil.copyfileobj(r, w, 8 << 20)
with tarfile.open('/tmp/b.tgz', 'r|gz') as tar:
    for m in tar:
        if m.name.startswith(RI + 'Banco de claves/'): tar.extract(m, '/tmp/kb', filter='data')
sys.path.insert(0, '/tmp/kb/' + RI + 'Banco de claves')
from secret_bank.vault import Vault
pathlib.Path('/tmp/kv.db').write_bytes(gzip.decompress(base64.b64decode(fs.cat_file(BASE + '/banco/vault.db.gz.b64'))))
v = Vault(pathlib.Path('/tmp/kv.db')).unlock(os.environ['RIU_VAULT_PASSPHRASE'])
KEY = v.get_secret('router/runtime-admin-32gb'); GK = v.get_secret('github/director-full')
H = {'X-API-Key': KEY, 'Authorization': 'Bearer ' + KEY, 'Content-Type': 'application/json'}
def http(url, met, path, body=None, t=40):
    try:
        with ur.urlopen(ur.Request(url + path, data=json.dumps(body).encode() if body is not None else None, headers=H, method=met), timeout=t) as rr: return rr.status, json.load(rr)
    except urllib.error.HTTPError as e: return e.code, {}
    except Exception: return 0, {}
def chat(url, base, body, lim=240):
    s, d = http(url, 'POST', base + 'chat_async', body); pid = (d.get('result') or {}).get('proceso_id'); t = time.time()
    while pid and time.time() - t < lim:
        time.sleep(2); s, d = http(url, 'POST', base + 'resultado', {'proceso_id': pid}); r = d.get('result') or {}
        if r.get('estado') != 'procesando': return r
    return {'estado': 'SIN_RESPUESTA'}
P = '/plugins/puente_chat/call/'; F = '/plugins/fichas_qwen/call/'
def por_defecto(url):  # criterio del sentinela del kernel: responde cualquiera de los dos modelos (con un reintento)
    for intento in (1, 2):
        for modelo in ('groq-qwen-3-8', 'nv-nemotron-super'):
            r = chat(url, P, {'model': modelo, 'messages': [{'role': 'user', 'content': 'Responde solamente OK'}], 'max_tokens': 16, 'sesion': 'pub-%s-%d' % (modelo, intento)}, 150)
            c = ((r.get('choices') or [{}])[0].get('message') or {}).get('content')
            if c and str(c).strip(): return True, modelo, str(c)[:20], r.get('estado')
    return False, None, None, r.get('estado')
URL = 'https://%s--8000.hf.jobs' % NUEVO
sano = http(URL, 'GET', '/health', t=20)[0] == 200; out(paso='health router nuevo', ok=sano, job=NUEVO[-8:])
if not sano: sys.exit(4)
s, d = http(URL, 'GET', '/chat/providers'); out(paso='proveedores', configurados=[p.get('id') for p in d.get('providers', []) if p.get('configured')])
ok_n = por_defecto(URL); out(prueba='ruta por defecto (puente_chat) en el router NUEVO', ok=ok_n[0], modelo=ok_n[1], respuesta=ok_n[2], estado=ok_n[3])
ok_a = (None, None, None, None)
if ACTUAL: ok_a = por_defecto('https://%s--8000.hf.jobs' % ACTUAL); out(prueba='ruta por defecto (puente_chat) en el router ACTUAL', ok=ok_a[0], modelo=ok_a[1], respuesta=ok_a[2], estado=ok_a[3])
fichas = []
for nom, fi in [('Team qwen (ficha 1)', '1'), ('Ask consil code (ficha 2)', '2'), ('Ask consil frontend (ficha 3)', '3')]:
    r = chat(URL, F, {'ficha_qwen': fi, 'modelo': 'ficha-qwen38flash', 'messages': [{'role': 'user', 'content': 'Responde solo OK'}], 'sesion': 'pub-' + fi, 'fast_reply': True}, 300)
    good = r.get('execution_path') == 'FAST_QA' and bool(r.get('reply')); fichas.append(good); out(prueba=nom + ' con fast_reply en el router NUEVO', ok=good, execution_path=r.get('execution_path'), ms=r.get('ms'))
regresion = bool(ok_a[0]) and not ok_n[0]  # solo es regresion si el actual SI responde y el nuevo no
if all(fichas) and not regresion:
    value = {'LIVE_URL': URL, 'job_id': NUEVO, 'flavor': 'cpu-basic', 'updated': time.time(), 'auth': 'X-API-Key', 'harnessUrl': URL + '/plugins/puente_chat/call'}
    apiurl = 'https://api.github.com/repos/' + REPO + '/contents/' + urllib.parse.quote(RI + 'LIVE_URL.json'); gh = {'Authorization': 'Bearer ' + GK, 'Content-Type': 'application/json', 'User-Agent': 'yaiwes-pub'}
    old = json.load(ur.urlopen(ur.Request(apiurl + '?ref=main', headers=gh), timeout=30))
    ur.urlopen(ur.Request(apiurl, data=json.dumps({'message': 'Update active HF Router address [skip ci]', 'branch': 'main', 'sha': old['sha'], 'content': base64.b64encode(json.dumps(value, indent=2).encode()).decode()}).encode(), headers=gh, method='PUT'), timeout=30)
    fs.pipe_file(BASE + '/control/router-current.json', json.dumps({'url': URL, 'job_id': NUEVO, 'flavor': 'cpu-basic', 'started': time.time(), 'timeout_s': 172800}).encode()); out(paso='LIVE_URL publicada', url=URL)
    api = HfApi(token=os.environ['HF_TOKEN'])
    for vid in VIEJOS:
        try: api.cancel_job(job_id=vid, namespace=NS); out(paso='router viejo retirado', job=vid[-8:])
        except Exception as e: out(paso='router viejo NO retirado', job=vid[-8:], error=type(e).__name__)
    out(paso='FIN_PUBLICAR', ok=True); sys.exit(0)
out(paso='NO_PUBLICA', motivo='regresion' if regresion else 'fichas no respondieron', fichas=fichas); sys.exit(5)
