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
           'Cuando te pidan leer, buscar, crear o cambiar archivos, repositorios, jobs o modelos, usa las herramientas en lugar de decir que no puedes. '
           'Nunca muestres claves ni tokens. Responde en espanol.')
S = {'type': 'string'}
O = {'type': 'object'}


def _fn(nombre, desc, props, req):
    return {'type': 'function', 'function': {'name': nombre, 'description': desc, 'parameters': {'type': 'object', 'properties': props, 'required': req}}}


TOOLS = [
    _fn('github_leer', 'Lee un archivo, o lista una carpeta, de un repositorio de GitHub de maxbry123-commits.', {'repo': S, 'ruta': S, 'rama': S}, ['repo']),
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


def _token_gh():
    c = _cache.get('gh')
    if c and time.time() - c[1] < 600:
        return c[0]
    for k in _llaves('github', ['GITHUB_PERSONAL_ACCESS_TOKEN']):
        s, _ = _peticion('GET', 'https://api.github.com/user', k, espera=20, extra={'Accept': 'application/vnd.github+json'})
        if s == 200:
            _cache['gh'] = (k, time.time())
            return k
    return ''


def _token_hf():
    c = _cache.get('hf')
    if c and time.time() - c[1] < 600:
        return c[0]
    for k in _llaves('huggingface', ['HF_TOKEN']):
        s, _ = _peticion('GET', 'https://huggingface.co/api/whoami-v2', k, espera=20)
        if s == 200:
            _cache['hf'] = (k, time.time())
            return k
    return ''


GH_RUTA = re.compile('^/(repos/maxbry123-commits/[A-Za-z0-9._-]+(/[^?#]*)?|user|user/repos|search/(code|repositories|issues|commits))([?][^#]*)?$')
GH_REPO = re.compile('^/repos/[^/]+/[^/?]+/?([?].*)?$')
HF_BLOQUEO = [re.compile('^/api/repos/(delete|move)'),
              re.compile('^/api/(models|datasets|spaces)/[^/]+/[^/]+/(pause|restart|hardware|sleeptime|settings|secrets|variables)'),
              re.compile('^/api/jobs/[^/]+/[^/]+/cancel'), re.compile('^/api/buckets')]


def _gh(metodo, ruta, cuerpo=None):
    metodo = str(metodo or 'GET').upper()
    if not str(ruta or '').startswith('/') or str(ruta).startswith('//') or '..' in ruta:
        return 0, 'ERROR: ruta de GitHub no permitida (solo repos de maxbry123-commits, /user y busquedas)'
    t = _token_gh()
    if not t:
        return 0, 'ERROR: no hay token de GitHub valido en el banco'
    return _peticion(metodo, 'https://api.github.com' + ruta, t, cuerpo, 40, {'Accept': 'application/vnd.github+json'})


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
    repo = a.get('repo', '')
    ruta = urllib.parse.quote(a.get('ruta', '') or '', safe='/')
    rama = urllib.parse.quote(a.get('rama') or 'main', safe='')
    s, d = _gh('GET', '/repos/%s/%s/contents/%s?ref=%s' % (OWNER, repo, ruta, rama))
    if isinstance(d, list):
        return json.dumps([x.get('name', '') + ('/' if x.get('type') == 'dir' else '') for x in d])[:12000]
    if s != 200 or not isinstance(d, dict):
        return 'ERROR %s %s' % (s, str(d)[:300])
    if d.get('encoding') == 'base64':
        return base64.b64decode(d.get('content', '')).decode('utf-8', 'replace')[:15000]
    return str(d)[:3000]


def github_escribir(a):
    repo = a.get('repo', '')
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
