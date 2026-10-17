# Herramientas de GitHub y Hugging Face para los modelos de las fichas (Director 2026-10-04).
# Las claves salen del banco del Router y nunca se devuelven al modelo.
import base64
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request

OWNER = 'maxbry123-commits'
NS = 'COMAND-CENTER-1'
BUCKET = NS + '/yaiwes-memoria-storage'
_cache = {}
SISTEMA = ('Tienes herramientas reales: GitHub (cuenta maxbry123-commits) y Hugging Face (cuenta COMAND-CENTER-1). '
           'El repo principal es router-universal-router-inteligente- (lleva guion al final) en la rama main. '
           'Cuando te pidan leer, buscar, crear o cambiar archivos, repositorios, jobs o modelos, usa las herramientas en lugar de decir que no puedes. '
           'Nunca muestres claves ni tokens. Responde en espanol.')
S = {'type': 'string'}
O = {'type': 'object'}


def _fn(nombre, desc, props, req):
    return {'type': 'function', 'function': {'name': nombre, 'description': desc, 'parameters': {'type': 'object', 'properties': props, 'required': req}}}


TOOLS = [
    _fn('github_leer', 'Lee un archivo, o lista una carpeta, de un repositorio de GitHub de maxbry123-commits. En archivos largos usa lineas (ej "200-400") para leer un rango.', {'repo': S, 'ruta': S, 'rama': S, 'lineas': S}, ['repo']),
    _fn('github_escribir', 'Crea o cambia un archivo en un repositorio de GitHub de maxbry123-commits (hace un commit).', {'repo': S, 'ruta': S, 'contenido': S, 'mensaje': S, 'rama': S}, ['repo', 'ruta', 'contenido']),
    _fn('github_api', 'Llama a la API de GitHub con los permisos de la cuenta del Director. metodo: GET, POST, PUT, PATCH o DELETE.', {'metodo': S, 'ruta': S, 'cuerpo': O}, ['metodo', 'ruta']),
    _fn('hf_leer', 'Lee un archivo de un repo de Hugging Face. tipo: model, dataset o space.', {'repo': S, 'ruta': S, 'tipo': S, 'rama': S}, ['repo', 'ruta']),
    _fn('hf_escribir', 'Crea o cambia un archivo en un repo de Hugging Face de la cuenta COMAND-CENTER-1.', {'repo': S, 'ruta': S, 'contenido': S, 'mensaje': S, 'tipo': S}, ['repo', 'ruta', 'contenido']),
    _fn('hf_api', 'Llama a la API de Hugging Face (la ruta empieza con /api/). Escribir solo en la cuenta COMAND-CENTER-1.', {'metodo': S, 'ruta': S, 'cuerpo': O}, ['metodo', 'ruta']),
    _fn('hf_almacenamiento', 'Almacenamiento permanente de Hugging Face. accion: listar, leer o escribir.', {'accion': S, 'ruta': S, 'contenido': S}, ['accion']),
]


def _peticion(metodo, url, token, cuerpo=None, espera=40, extra=None):
    cab = {'User-Agent': 'riu-puente', 'Accept': 'application/json'}
    if token:
        cab['Authorization'] = 'Bearer ' + token
    if cuerpo is not None:
        cab['Content-Type'] = 'application/json'
    if extra:
        cab.update(extra)
    req = urllib.request.Request(url, data=json.dumps(cuerpo).encode() if cuerpo is not None else None, headers=cab, method=metodo)
    try:
        with urllib.request.urlopen(req, timeout=espera) as r:
            t = r.read().decode('utf-8', 'replace')
            code = r.status
    except urllib.error.HTTPError as e:
        t = e.read().decode('utf-8', 'replace')
        code = e.code
    except Exception as e:
        return 0, 'ERROR de red: ' + type(e).__name__
    try:
        return code, json.loads(t)
    except ValueError:
        return code, t


def _llaves(proveedor, env):
    try:
        from integration.chat_mvp import vault_hook
        base = list(vault_hook.provider_keys(proveedor))
    except Exception:
        base = []
    if proveedor == 'github':
        try:
            for var in json.loads(os.environ.get('RIU_GITHUB_ACCOUNTS') or '{}').values():
                if os.environ.get(str(var)):
                    base.append(os.environ[str(var)])
        except ValueError:
            pass
    for nombre in env:
        if os.environ.get(nombre):
            base.append(os.environ[nombre])
    vistos = []
    for k in base:
        if k and k not in vistos:
            vistos.append(k)
    return vistos


def _token_gh(repo='', escritura=False):
    # Elige una clave del banco que de verdad vea el repo (y pueda escribir si hace falta):
    # varias claves del banco son validas en /user pero no tienen acceso al repo de YAIWES.
    clave_cache = 'gh:' + (repo or '-') + (':w' if escritura else '')
    c = _cache.get(clave_cache)
    if c and time.time() - c[1] < 600:
        return c[0]
    reserva = ''
    for k in _llaves('github', ['GITHUB_PERSONAL_ACCESS_TOKEN']):
        if repo:
            s, d = _peticion('GET', 'https://api.github.com/repos/%s/%s' % (OWNER, repo), k, espera=20,
                             extra={'Accept': 'application/vnd.github+json'})
            if s in (0, 500, 502, 503, 504):
                # fallo transitorio de GitHub: la clave puede valer; queda de reserva
                s2, _ = _peticion('GET', 'https://api.github.com/user', k, espera=20,
                                  extra={'Accept': 'application/vnd.github+json'})
                if s2 == 200 and not reserva:
                    reserva = k
                continue
            if s != 200 or not isinstance(d, dict):
                continue
            if escritura and not (d.get('permissions') or {}).get('push'):
                continue
        else:
            s, _ = _peticion('GET', 'https://api.github.com/user', k, espera=20,
                             extra={'Accept': 'application/vnd.github+json'})
            if s != 200:
                continue
        _cache[clave_cache] = (k, time.time())
        return k
    if reserva:
        _cache[clave_cache] = (reserva, time.time())
    return reserva


def _token_hf():
    c = _cache.get('hf')
    if c and time.time() - c[1] < 600:
        return c[0]
    reserva = ''
    for k in _llaves('hf', ['HF_TOKEN']):  # nombre logico del chat: provider_map hf -> vault_provider huggingface; 'huggingface' devolvia [] y caia a HF_TOKEN suelto
        s, _ = _peticion('GET', 'https://huggingface.co/api/whoami-v2', k, espera=20)
        if s == 200:
            _cache['hf'] = (k, time.time())
            return k
        if s in (0, 500, 502, 503, 504) and not reserva:
            reserva = k
    if reserva:
        _cache['hf'] = (reserva, time.time())
    return reserva


GH_RUTA = re.compile('^/(repos/maxbry123-commits/[A-Za-z0-9._-]+(/[^?#]*)?|user|user/repos|search/(code|repositories|issues|commits))([?][^#]*)?$')
GH_REPO = re.compile('^/repos/[^/]+/[^/?]+/?([?].*)?$')
HF_BLOQUEO = [re.compile('^/api/repos/(delete|move)'),
              re.compile('^/api/(models|datasets|spaces)/[^/]+/[^/]+/(pause|restart|hardware|sleeptime|settings|secrets|variables)'),
              re.compile('^/api/jobs/[^/]+/[^/]+/cancel'), re.compile('^/api/buckets')]


def _gh(metodo, ruta, cuerpo=None):
    metodo = str(metodo or 'GET').upper()
    if not str(ruta or '').startswith('/') or str(ruta).startswith('//') or '..' in ruta:
        return 0, 'ERROR: ruta de GitHub no permitida (solo repos de maxbry123-commits, /user y busquedas)'
    if metodo == 'DELETE' and re.match('^/repos/maxbry123-commits/[^/?]+/?([?].*)?$', str(ruta)):
        return 0, 'ERROR: no se puede borrar un repositorio'
    m = re.match('^/repos/maxbry123-commits/([^/?]+)(/.*)?$', str(ruta))
    if m:
        real = _resolver_repo(urllib.parse.unquote(m.group(1)))
        if real != m.group(1):
            ruta = '/repos/%s/%s%s' % (OWNER, urllib.parse.quote(real, safe=''), m.group(2) or '')
            m = re.match('^/repos/maxbry123-commits/([^/?]+)(/.*)?$', ruta)
    escritura = metodo not in ('GET', 'HEAD') and str(ruta).startswith('/repos/maxbry123-commits/')
    if not escritura:
        t = _token_gh(m.group(1) if m else '')
        if not t:
            return 0, 'ERROR: no hay token de GitHub valido en el banco'
        s, d = _peticion(metodo, 'https://api.github.com' + ruta, t, cuerpo, 40,
                         {'Accept': 'application/vnd.github+json'})
        if s in (0, 500, 502, 503, 504):
            time.sleep(1)
            s, d = _peticion(metodo, 'https://api.github.com' + ruta, t, cuerpo, 40,
                             {'Accept': 'application/vnd.github+json'})
        return s, d
    # Escritura: probar las claves del banco hasta que una tenga permiso real de commit.
    # Las PAT finas de solo lectura devuelven 403/404 aunque el repo exista y el usuario tenga push.
    ultimo = (0, 'ERROR: no hay token de GitHub valido en el banco')
    for k in _llaves('github', ['GITHUB_PERSONAL_ACCESS_TOKEN']):
        s, d = _peticion(metodo, 'https://api.github.com' + ruta, k, cuerpo, 40,
                         {'Accept': 'application/vnd.github+json'})
        if s in (401, 403, 404, 0, 500, 502, 503, 504):
            ultimo = (s, d)
            continue  # sin permiso o fallo transitorio: siguiente clave
        return s, d
    return ultimo


def _canon(nom):
    return re.sub('[^a-z0-9]', '', str(nom or '').lower())


def _resolver_repo(nombre):
    # Devuelve el nombre real del repo aunque el modelo lo escriba mal
    # (sin guion final, espacios, mayusculas). Si no hay coincidencia, devuelve el original.
    nom = str(nombre or '').strip().strip('/')
    if not nom:
        return nom
    ck = 'ghrepo:' + nom.lower()
    c = _cache.get(ck)
    if c and time.time() - c[1] < 600:
        return c[0]
    claves = _llaves('github', ['GITHUB_PERSONAL_ACCESS_TOKEN'])
    for k in claves:
        s, _ = _peticion('GET', 'https://api.github.com/repos/%s/%s' % (OWNER, urllib.parse.quote(nom, safe='')),
                         k, espera=15, extra={'Accept': 'application/vnd.github+json'})
        if s == 200:
            _cache[ck] = (nom, time.time())
            return nom
        if s == 401:
            continue
    objetivo = _canon(nom)
    for k in claves:
        pagina = 1
        encontrado = ''
        while pagina <= 5 and not encontrado:
            s, d = _peticion('GET', 'https://api.github.com/users/%s/repos?per_page=100&page=%d&type=owner' % (OWNER, pagina),
                             k, espera=20, extra={'Accept': 'application/vnd.github+json'})
            if s != 200 or not isinstance(d, list) or not d:
                break
            for r in d:
                n = r.get('name') or ''
                cn = _canon(n)
                if cn == objetivo or (len(objetivo) >= 8 and objetivo in cn) or (len(cn) >= 8 and cn in objetivo):
                    encontrado = n
                    break
            pagina += 1
        if encontrado:
            _cache[ck] = (encontrado, time.time())
            return encontrado
        break
    return nom


def _hf(metodo, ruta, cuerpo=None):
    metodo = str(metodo or 'GET').upper()
    if not str(ruta or '').startswith('/api/') or '..' in ruta:
        return 0, 'ERROR: ruta de HF no permitida (debe empezar con /api/)'
    t = _token_hf()
    if not t:
        return 0, 'ERROR: no hay token de Hugging Face valido en el banco'
    return _peticion(metodo, 'https://huggingface.co' + ruta, t, cuerpo, 40)


def _texto(s, d, limite=12000):
    cuerpo = d if isinstance(d, str) else json.dumps(d, ensure_ascii=False)
    return ('HTTP %s ' % s) + cuerpo[:limite]


def github_leer(a):
    repo = a.get('repo') or 'router-universal-router-inteligente-'
    ruta = urllib.parse.quote(a.get('ruta', '') or '', safe='/')
    rama = urllib.parse.quote(a.get('rama') or 'main', safe='')
    s, d = _gh('GET', '/repos/%s/%s/contents/%s?ref=%s' % (OWNER, repo, ruta, rama))
    if isinstance(d, list):
        return json.dumps([x.get('name', '') + ('/' if x.get('type') == 'dir' else '') for x in d])[:12000]
    if s != 200 or not isinstance(d, dict):
        return 'ERROR %s %s' % (s, str(d)[:300])
    if d.get('encoding') == 'base64':
        texto = base64.b64decode(d.get('content', '')).decode('utf-8', 'replace')
        lineas = str(a.get('lineas') or '').strip()
        total = len(texto.splitlines())
        if lineas:
            m = re.match(r'^(\d*)\s*-\s*(\d*)$', lineas)
            if m:
                ini = int(m.group(1)) - 1 if m.group(1) else 0
                fin = int(m.group(2)) if m.group(2) else total
                trozo = '\n'.join(texto.splitlines()[max(0, ini):fin])
                return ('(lineas %s de %d totales)\n' % (lineas, total)) + trozo[:12000]
            return 'ERROR: lineas debe ser "desde-hasta", ej "1-200" o "300-"'
        if total > 300:
            return ('(archivo de %d lineas; mostrando las primeras; pide un rango con "lineas", ej "200-400")\n' % total) + texto[:12000]
        return texto[:12000]
    return str(d)[:3000]


def github_escribir(a):
    repo = a.get('repo') or 'router-universal-router-inteligente-'
    rama = a.get('rama') or 'main'
    base = '/repos/%s/%s/contents/%s' % (OWNER, repo, urllib.parse.quote(a.get('ruta', ''), safe='/'))
    s0, d0 = _gh('GET', base + '?ref=' + urllib.parse.quote(rama, safe=''))
    cuerpo = {'message': a.get('mensaje') or 'cambio desde el chat', 'content': base64.b64encode((a.get('contenido') or '').encode()).decode(), 'branch': rama}
    if s0 == 200 and isinstance(d0, dict) and d0.get('sha'):
        cuerpo['sha'] = d0['sha']
    s, d = _gh('PUT', base, cuerpo)
    if s in (200, 201) and isinstance(d, dict):
        return 'OK commit ' + str((d.get('commit') or {}).get('sha', ''))[:10]
    return 'ERROR %s %s' % (s, str(d)[:300])


def github_api(a):
    s, d = _gh(a.get('metodo'), a.get('ruta'), a.get('cuerpo'))
    return _texto(s, d)


def hf_leer(a):
    tipo = {'dataset': 'datasets/', 'space': 'spaces/'}.get(a.get('tipo') or 'model', '')
    t = _token_hf()
    if not t:
        return 'ERROR: no hay token de Hugging Face valido en el banco'
    url = 'https://huggingface.co/%s%s/resolve/%s/%s' % (tipo, a.get('repo', ''), urllib.parse.quote(a.get('rama') or 'main', safe=''), urllib.parse.quote(a.get('ruta', ''), safe='/'))
    s, d = _peticion('GET', url, t, None, 40, {'Range': 'bytes=0-60000', 'Accept': '*/*'})
    return _texto(s, d, 15000)


def hf_escribir(a):
    repo = a.get('repo', '')
    if not repo.startswith(NS + '/'):
        return 'ERROR: solo se puede escribir en la cuenta ' + NS
    t = _token_hf()
    if not t:
        return 'ERROR: no hay token de Hugging Face valido en el banco'
    try:
        from huggingface_hub import HfApi
        r = HfApi(token=t).upload_file(path_or_fileobj=(a.get('contenido') or '').encode(), path_in_repo=a.get('ruta', ''), repo_id=repo,
                                       repo_type=a.get('tipo') or 'model', commit_message=a.get('mensaje') or 'cambio desde el chat')
        return 'OK ' + str(r)[:200]
    except Exception as e:
        return 'ERROR ' + str(e)[:300]


def hf_api(a):
    s, d = _hf(a.get('metodo'), a.get('ruta'), a.get('cuerpo'))
    return _texto(s, d)


def hf_almacenamiento(a):
    accion = a.get('accion')
    ruta = a.get('ruta') or ''
    if re.search('banco|vault|secret|clave', ruta, re.I) or (accion == 'escribir' and re.search('codigo|control', ruta, re.I)):
        return 'ERROR: carpeta protegida'
    t = _token_hf()
    if not t:
        return 'ERROR: no hay token de Hugging Face valido en el banco'
    try:
        from huggingface_hub import HfApi
        api = HfApi(token=t)
        if accion == 'listar':
            return json.dumps([(e.path, getattr(e, 'size', None)) for e in api.list_bucket_tree(BUCKET, prefix=ruta)][:200])[:12000]
        if accion == 'leer':
            api.download_bucket_files(BUCKET, files=[(ruta, '/tmp/lectura-bucket.tmp')])
            return open('/tmp/lectura-bucket.tmp', encoding='utf-8', errors='replace').read()[:15000]
        if accion == 'escribir':
            api.batch_bucket_files(BUCKET, add=[((a.get('contenido') or '').encode(), ruta)])
            return 'OK escrito ' + ruta
        return 'ERROR: accion debe ser listar, leer o escribir'
    except Exception as e:
        return 'ERROR ' + str(e)[:300]


FUNCS = {'github_leer': github_leer, 'github_escribir': github_escribir, 'github_api': github_api, 'hf_leer': hf_leer,
         'hf_escribir': hf_escribir, 'hf_api': hf_api, 'hf_almacenamiento': hf_almacenamiento}


def ejecutar(nombre, args):
    f = FUNCS.get(nombre)
    if not f:
        return 'ERROR: herramienta desconocida'
    try:
        return str(f(args if isinstance(args, dict) else {}))
    except Exception as e:
        return 'ERROR: ' + type(e).__name__ + ' ' + str(e)[:200]

# Public Internet tools: credentials are never attached to web requests.
def internet_leer(a):
    import socket, ipaddress
    from bs4 import BeautifulSoup
    url = str(a.get('url') or '')
    def validate(u):
        q = urllib.parse.urlparse(u)
        if q.scheme not in ('http', 'https') or not q.hostname or q.username or q.password:
            raise ValueError('URL_PUBLICA_REQUERIDA')
        addresses = socket.getaddrinfo(q.hostname, q.port or (443 if q.scheme == 'https' else 80))
        if (q.hostname.lower() not in {'huggingface.co', 'api.github.com', 'github.com', 'raw.githubusercontent.com'}
            and (not addresses or any(not ipaddress.ip_address(x[4][0]).is_global for x in addresses))):
            raise ValueError('SOLO_INTERNET_PUBLICO')
    class Redirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            validate(newurl)
            return super().redirect_request(req, fp, code, msg, headers, newurl)
    validate(url)
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 YAIWES', 'Accept': 'text/html,application/json,text/plain'})
    with urllib.request.build_opener(Redirect()).open(req, timeout=20) as r:
        content = r.read(512000).decode('utf-8', 'replace')
        ct = r.headers.get('content-type', '')
    if 'html' in ct:
        soup = BeautifulSoup(content, 'html.parser')
        for el in soup(['script','style','noscript']): el.decompose()
        content = soup.get_text(' ', strip=True)
    return json.dumps({'url': url, 'contenido': content[:15000]}, ensure_ascii=False)
def internet_buscar(a):
    import xml.etree.ElementTree as ET
    query = str(a.get('consulta') or '').strip()
    if not query: return 'ERROR: consulta vacia'
    url = 'https://www.bing.com/search?format=rss&q=' + urllib.parse.quote(query)
    req = urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 YAIWES'})
    with urllib.request.urlopen(req,timeout=20) as r: raw=r.read(256000)
    tree=ET.fromstring(raw)
    return json.dumps([{'titulo':i.findtext('title'),'url':i.findtext('link'),'resumen':i.findtext('description')} for i in tree.findall('.//item')][:8],ensure_ascii=False)
TOOLS.extend([
    _fn('internet_leer','Lee una pagina publica de Internet por HTTP; devuelve texto y URL. Nunca se envian claves.',{'url': S},['url']),
    _fn('internet_buscar','Busca informacion publica en Internet y devuelve enlaces y resumenes.',{'consulta': S},['consulta']),
])
FUNCS.update({'internet_leer':internet_leer,'internet_buscar':internet_buscar})
SISTEMA += ' Tambien tienes internet_buscar e internet_leer para consultar la web publica.'

SISTEMA += ' Si una herramienta falla, explica el error; no inventes su resultado.'

# --- Groq: una sola ficha como tool para enrutar a agentes (pool de hasta 20) ---
GROQ_MAX = 20
GROQ_RUTA = os.environ.get('RIU_AGENTES_RUTA') or 'agentes/groq-pool.json'  # pruebas locales: ruta aparte, sin tocar el pool real
GROQ_MODELOS = ('openai/gpt-oss-20b', 'openai/gpt-oss-120b', 'qwen/qwen3.8-27b')
_GROQ_DEF = [
    {'nombre': 'investigador', 'modelo': 'openai/gpt-oss-20b', 'sistema': 'Eres un investigador. Responde con datos concretos y breves, en espanol.'},
    {'nombre': 'programador', 'modelo': 'openai/gpt-oss-120b', 'sistema': 'Eres un programador senior. Responde con codigo corto y correcto, en espanol.'},
    {'nombre': 'redactor', 'modelo': 'openai/gpt-oss-20b', 'sistema': 'Eres un redactor. Escribe textos claros y breves en espanol.'},
]
_GROQ = {'pool': None, 'i': 0}
GROQ_ENV = ['GROQ_API_KEY'] + ['GROQ_API_KEY_%d' % i for i in range(2, 11)]  # GROQ_API_KEY_1 fuera: HTTP 401 medido el 16-oct


def groq_pool():
    if _GROQ['pool'] is None:
        txt = hf_almacenamiento({'accion': 'leer', 'ruta': GROQ_RUTA})
        try:
            p = json.loads(txt)
            _GROQ['pool'] = [a for a in p if isinstance(a, dict) and a.get('nombre')][:GROQ_MAX] if isinstance(p, list) else list(_GROQ_DEF)
        except ValueError:
            _GROQ['pool'] = list(_GROQ_DEF)
    return _GROQ['pool']


def groq_guardar(pool):
    limpio, vistos = [], set()
    for a in pool or []:
        n = re.sub(r'[^a-z0-9_-]', '', str((a or {}).get('nombre') or '').lower())[:40]
        if not n or n in vistos:
            continue
        vistos.add(n)
        m = str(a.get('modelo') or GROQ_MODELOS[0])
        ag = {'nombre': n, 'modelo': m if m in GROQ_MODELOS else GROQ_MODELOS[0], 'sistema': str(a.get('sistema') or '')[:600]}
        rec = str(a.get('recurso') or '')
        if rec and rec in recursos_ids():
            ag['recurso'] = rec  # recurso LLM enlazado (Ficha 4 / NVIDIA codigo / Groq); sin recurso = su modelo Groq
        limpio.append(ag)
    if len(limpio) > GROQ_MAX:
        return {'error': 'MAXIMO_%d_AGENTES' % GROQ_MAX}
    _GROQ['pool'] = limpio
    r = hf_almacenamiento({'accion': 'escribir', 'ruta': GROQ_RUTA, 'contenido': json.dumps(limpio, ensure_ascii=False)})
    return {'ok': True, 'agentes': limpio, 'guardado': r.startswith('OK')}


def groq_agente(a):
    nombre = str(a.get('nombre') or '').lower().strip()
    ag = next((x for x in groq_pool() if x['nombre'] == nombre), None)
    if not ag:
        return 'ERROR: agente desconocido. Agentes: ' + ', '.join(x['nombre'] for x in groq_pool())
    if ag.get('recurso') and not str(ag['recurso']).startswith('groq:'):
        return '[' + ag['nombre'] + ' · ' + ag['recurso'] + '] ' + llamar_recurso(ag['recurso'], ag.get('sistema') or '', str(a.get('mensaje') or ''))
    claves = _llaves('groq', GROQ_ENV)
    if not claves:
        return 'ERROR: no hay claves de Groq'
    cuerpo = {'model': (str(ag.get('recurso') or '')[5:] or ag['modelo']) if str(ag.get('recurso') or '').startswith('groq:') else ag['modelo'], 'max_tokens': 1500, 'messages': [{'role': 'system', 'content': ag['sistema'] or 'Responde en espanol.'}, {'role': 'user', 'content': str(a.get('mensaje') or '')[:8000]}]}
    ultimo = ''
    for _ in range(len(claves)):
        k = claves[_GROQ['i'] % len(claves)]
        _GROQ['i'] += 1
        s, d = _peticion('POST', 'https://api.groq.com/openai/v1/chat/completions', k, cuerpo, 45)
        if s == 200 and isinstance(d, dict) and d.get('choices'):
            return '[' + ag['nombre'] + ' · ' + ag['modelo'] + '] ' + str(d['choices'][0]['message'].get('content') or '')
        ultimo = 'HTTP %s' % s
        if s not in (0, 401, 403, 429) and s < 500:
            break
    return 'ERROR Groq: ' + ultimo


TOOLS.append(_fn('groq_agente', 'Enruta un mensaje a uno de los agentes Groq conectados (pool de hasta 20) y devuelve su respuesta. nombre: nombre del agente (ej. investigador, programador, redactor).', {'nombre': S, 'mensaje': S}, ['nombre', 'mensaje']))
FUNCS['groq_agente'] = groq_agente
SISTEMA += ' Tienes groq_agente(nombre, mensaje) para delegar en un agente Groq del pool.'


# --- Staff de tools: recursos LLM enlazables (Ficha 4 por Harness/HTTP, tool NVIDIA de codigo, Groq) ---
# El Harness (plugin.py) inyecta LLM_CALL (llm_call -> HTTP -> Ficha 4) y LLM_NV (_llamar_api nvidia, claves 2-5).
LLM_CALL = None
LLM_NV = None
NV_CODIGO = [('z-ai/glm-5.3', 'GLM-5.3', 'Codigo: 1o de la comunidad (SWE-bench, LMArena WebDev)'),
             ('stepfun-ai/step-5-preview', 'Step 5 Preview', 'Codigo rapido: 2o en uso real OpenRouter')]
# deepseek-ai/deepseek-v4.1-flash (1o en uso OpenRouter) queda fuera: timeout >90 s en NVIDIA el 16-oct (3 de 3)


def _ficha4_texto():
    ruta = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'fichas_qwen', 'fichas', 'ficha4-workflow-yaiwes.json')
    try:
        with open(ruta, encoding='utf-8') as f:
            sel = json.load(f).get('selector') or []
    except Exception:  # noqa: BLE001
        sel = []
    return [x for x in sel if isinstance(x, dict) and x.get('tipo') == 'texto' and x.get('id')]


def recursos_llm():
    r = [{'id': 'ficha4:' + x['id'], 'nombre': x.get('nombre') or x['id'], 'rol': x.get('rol') or '', 'grupo': 'Ficha 4', 'via': 'Harness -> HTTP -> Ficha 4'} for x in _ficha4_texto()]
    r += [{'id': 'nvcode:' + m, 'nombre': n + ' (NVIDIA)', 'rol': rol, 'grupo': 'NVIDIA codigo', 'via': 'Harness -> HTTP -> NVIDIA (claves 2-5)'} for m, n, rol in NV_CODIGO]
    r += [{'id': 'groq:' + m, 'nombre': m, 'rol': 'Groq', 'grupo': 'Groq', 'via': 'Harness -> HTTP -> Groq'} for m in GROQ_MODELOS]
    return r


def recursos_ids():
    return {x['id'] for x in recursos_llm()}


def llamar_recurso(recurso, sistema, mensaje):
    recurso = str(recurso or '')
    msgs = ([{'role': 'system', 'content': str(sistema)[:2000]}] if sistema else []) + [{'role': 'user', 'content': str(mensaje or '')[:12000]}]
    if recurso not in recursos_ids():
        return 'ERROR: recurso desconocido. Validos: ' + ', '.join(sorted(recursos_ids()))
    if recurso.startswith('ficha4:'):
        if not LLM_CALL:
            return 'ERROR: GAP_FICHA4_HTTP (harness sin llm_call)'
        d = LLM_CALL({'caller_id': 'tools-staff', 'plugin_id': 'tools', 'workflow_id': 'tools-staff', 'task_type': 'code', 'modelo': recurso[7:], 'messages': msgs, 'max_tokens': 1500})
        return str(d.get('reply') or '') if d.get('reply') else 'ERROR Ficha 4: ' + str(d.get('error') or 'sin respuesta') + ' ' + str(d.get('detalle') or '')
    if recurso.startswith('nvcode:'):
        if not LLM_NV:
            return 'ERROR: harness sin NVIDIA'
        s_, d = LLM_NV(recurso[7:], msgs)
        if isinstance(d, dict) and d.get('choices'):
            return str((d['choices'][0].get('message') or {}).get('content') or '')
        return 'ERROR NVIDIA: HTTP %s %s' % (s_, json.dumps(d, ensure_ascii=False)[:200] if isinstance(d, dict) else str(d)[:200])
    claves = _llaves('groq', GROQ_ENV)
    for k in claves:
        s_, d = _peticion('POST', 'https://api.groq.com/openai/v1/chat/completions', k, {'model': recurso[5:], 'max_tokens': 1500, 'messages': msgs}, 45)
        if s_ == 200 and isinstance(d, dict) and d.get('choices'):
            return str(d['choices'][0]['message'].get('content') or '')
    return 'ERROR Groq: sin respuesta'


def agente_enlazar(a):
    nombre = re.sub(r'[^a-z0-9_-]', '', str(a.get('nombre') or '').lower())[:40]
    rec = str(a.get('recurso') or '')
    if not nombre:
        return {'error': 'FALTA_NOMBRE'}
    if rec not in recursos_ids():
        return {'error': 'RECURSO_DESCONOCIDO', 'validos': sorted(recursos_ids())}
    pool = [dict(x) for x in groq_pool()]
    ag = next((x for x in pool if x['nombre'] == nombre), None)
    if ag is None:
        ag = {'nombre': nombre, 'modelo': GROQ_MODELOS[0], 'sistema': str(a.get('sistema') or '')}
        pool.append(ag)
    ag['recurso'] = rec
    if a.get('sistema'):
        ag['sistema'] = str(a['sistema'])
    return groq_guardar(pool)


def _t_recurso(a):
    return llamar_recurso(a.get('recurso'), '', a.get('mensaje'))


def _t_nvcodigo(a):
    m = str(a.get('modelo') or NV_CODIGO[0][0])
    return llamar_recurso('nvcode:' + (m if m in [x[0] for x in NV_CODIGO] else NV_CODIGO[0][0]), 'Eres un programador senior. Responde con codigo correcto y breve, en espanol.', a.get('mensaje'))


def _t_enlazar(a):
    r = agente_enlazar(a)
    return json.dumps(r, ensure_ascii=False)[:1500]


TOOLS.extend([
    _fn('nvidia_codigo', 'Tool NVIDIA de codigo (GLM-5.3 por defecto, o deepseek-ai/deepseek-v4.1-flash): escribe o revisa codigo y devuelve la respuesta.', {'mensaje': S, 'modelo': S}, ['mensaje']),
    _fn('recurso_llm', 'Consulta un recurso LLM del staff de tools (ej. ficha4:ficha-qwen38max, nvcode:z-ai/glm-5.3, groq:openai/gpt-oss-120b) y devuelve su respuesta.', {'recurso': S, 'mensaje': S}, ['recurso', 'mensaje']),
    _fn('agente_enlazar', 'Enlaza un recurso LLM (modelo de la Ficha 4, NVIDIA codigo o Groq) a un agente del staff; si el agente no existe lo crea. Luego usa groq_agente(nombre, mensaje).', {'nombre': S, 'recurso': S, 'sistema': S}, ['nombre', 'recurso']),
])
FUNCS.update({'nvidia_codigo': _t_nvcodigo, 'recurso_llm': _t_recurso, 'agente_enlazar': _t_enlazar})
SISTEMA += (' Staff de tools: nvidia_codigo(mensaje) para codigo; recurso_llm(recurso, mensaje) para consultar un modelo de la Ficha 4 '
            '(ficha4:<id>), NVIDIA codigo (nvcode:<modelo>) o Groq; agente_enlazar(nombre, recurso) para elegir que modelo usa un agente.')
