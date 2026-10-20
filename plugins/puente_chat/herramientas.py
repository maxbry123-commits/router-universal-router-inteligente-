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
    _fn('github_escribir', 'Crea o cambia un archivo en un repositorio de GitHub de maxbry123-commits (hace un commit). Archivos grandes (hasta 500000 caracteres): escribe por partes con anexar=true y offset=<caracteres que el archivo tiene ahora (0 la primera vez)>; el resultado informa total=<caracteres>.', {'repo': S, 'ruta': S, 'contenido': S, 'mensaje': S, 'rama': S, 'anexar': {'type': 'boolean'}, 'offset': {'type': 'integer'}}, ['repo', 'ruta', 'contenido']),  # >>> PARCHE_500K <<<

    _fn('github_api', 'Llama a la API de GitHub con los permisos de la cuenta del Director. metodo: GET, POST, PUT, PATCH o DELETE. ruta: empieza con / (ej. /repos/<owner>/<repo>/commits?per_page=3); admite ?query params.', {'metodo': S, 'ruta': S, 'cuerpo': O}, ['metodo', 'ruta']),
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
        from plugins import router_api_cliente as vault_hook
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


def _ruta_gh_codificada(ruta):  # PARCHE_GH_URL_ENC
    """Codifica espacios, acentos y emoji de la ruta (idempotente: conserva los %XX previos)."""
    return urllib.parse.quote(str(ruta), safe="/?&=%:@,;+$!*'()~#-._")


def _gh(metodo, ruta, cuerpo=None):
    metodo = str(metodo or 'GET').upper()
    if not str(ruta or '').startswith('/') or str(ruta).startswith('//') or '..' in ruta:
        return 0, 'ERROR: ruta de GitHub no permitida (solo repos de maxbry123-commits, /user y busquedas)'
    if '..' in urllib.parse.unquote(str(ruta)):  # PARCHE_GH_URL_ENC
        return 0, 'ERROR: ruta de GitHub no permitida (solo repos de maxbry123-commits, /user y busquedas)'
    ruta = _ruta_gh_codificada(ruta)  # PARCHE_GH_URL_ENC
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
    if metodo in ('PUT', 'POST', 'PATCH') and ultimo[0] in (401, 403, 404):  # >>> PARCHE_VERIF <<< mensaje explicito: no confundir con "capacidad no disponible"
        return ultimo[0], 'ERROR SIN_PAT_CON_PUSH: ninguna clave del banco puede escribir en ese repo (HTTP %s): %s' % (ultimo[0], str(ultimo[1])[:150])
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


MAX_ARCHIVO_CHARS = 500000  # >>> PARCHE_500K <<<


def github_escribir(a):
    repo = a.get('repo') or 'router-universal-router-inteligente-'
    rama = a.get('rama') or 'main'
    base = '/repos/%s/%s/contents/%s' % (OWNER, repo, urllib.parse.quote(a.get('ruta', ''), safe='/'))
    s0, d0 = _gh('GET', base + '?ref=' + urllib.parse.quote(rama, safe=''))
    contenido = a.get('contenido') or ''  # >>> PARCHE_500K <<<
    if a.get('anexar') in (True, 'true', 'True', 1, '1'):
        prev = ''
        if s0 == 200 and isinstance(d0, dict) and d0.get('content') and d0.get('encoding', 'base64') == 'base64':
            prev = base64.b64decode(d0['content']).decode('utf-8', 'replace')
        elif s0 not in (200, 404):
            return 'ERROR %s no se pudo leer el archivo para anexar: %s' % (s0, str(d0)[:200])
        try:
            off = a.get('offset')
            if off is not None and str(off) != '' and int(off) != len(prev):
                return 'ERROR OFFSET_DISTINTO tamano_actual=%d (no se anexo nada; usa offset=%d)' % (len(prev), len(prev))
        except (TypeError, ValueError):
            return 'ERROR OFFSET_INVALIDO: debe ser un entero'
        contenido = prev + contenido
    if len(contenido) > MAX_ARCHIVO_CHARS:
        return 'ERROR ARCHIVO_EXCEDE_%d_CARACTERES (total pedido %d); divide en archivos' % (MAX_ARCHIVO_CHARS, len(contenido))
    cuerpo = {'message': a.get('mensaje') or 'cambio desde el chat', 'content': base64.b64encode(contenido.encode()).decode(), 'branch': rama}
    if s0 == 200 and isinstance(d0, dict) and d0.get('sha'):
        cuerpo['sha'] = d0['sha']
    s, d = _gh('PUT', base, cuerpo)
    if s in (200, 201) and isinstance(d, dict):
        csha = str((d.get('commit') or {}).get('sha', ''))
        if not csha:
            return 'ERROR SIN_SHA_DE_COMMIT repo=%s rama=%s ruta=%s (GitHub no devolvio commit; no se da por escrito)' % (repo, rama, a.get('ruta', ''))  # >>> PARCHE_VERIF <<<
        # >>> PARCHE_VERIF <<< relectura: el archivo debe estar en esa rama con ese contenido; si no, no hay exito
        s2, d2 = _gh('GET', base + '?ref=' + urllib.parse.quote(rama, safe=''))
        try:
            if s2 != 200 or not isinstance(d2, dict):
                raise ValueError('HTTP %s' % s2)
            if d2.get('content') and d2.get('encoding', 'base64') == 'base64':
                ok = base64.b64decode(d2['content']).decode('utf-8', 'replace') == contenido.encode().decode('utf-8', 'replace')
            else:  # archivos grandes: la API no devuelve el contenido; se compara el blob sha de git
                import hashlib as _hl
                _b = contenido.encode()
                ok = d2.get('sha') == _hl.sha1(b'blob %d\0' % len(_b) + _b).hexdigest()
            if not ok:
                raise ValueError('contenido distinto')
        except Exception as e:  # noqa: BLE001
            return 'ERROR READBACK_NO_COINCIDE repo=%s rama=%s ruta=%s commit=%s (%s)' % (repo, rama, a.get('ruta', ''), csha[:10], str(e)[:80])
        return 'OK commit ' + csha[:10] + ' total=%d repo=%s rama=%s ruta=%s verificado=relectura' % (len(contenido), repo, rama, a.get('ruta', ''))  # >>> PARCHE_500K <<<
    return 'ERROR %s %s' % (s, str(d)[:300])


def github_api(a):
    ruta = str(a.get('ruta') or a.get('endpoint') or a.get('path') or '').strip()  # alias: los modelos mandan endpoint/path
    if ruta.startswith('https://api.github.com'):
        ruta = ruta[len('https://api.github.com'):]  # el modelo manda a veces la URL completa
    elif ruta.startswith('api.github.com'):
        ruta = ruta[len('api.github.com'):]
    if ruta and not ruta.startswith('/'):
        ruta = '/' + ruta  # aceptar "repos/..." sin barra inicial; los ?query params ya los admite GH_RUTA
    s, d = _gh(a.get('metodo') or a.get('method'), ruta, a.get('cuerpo') or a.get('body'))
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


def _motor_json():  # >>> PARCHE_E2E <<< modulo del motor JSON/Python (yaiwes_motor) para es_mutante y ejecutar_plan_json
    import importlib.util as _iu
    import sys as _sy
    from pathlib import Path as _P
    if 'yaiwes_motor' in _sy.modules:
        return _sy.modules['yaiwes_motor']
    p = _P(__file__).resolve().parent.parent.parent / 'fichas' / 'fichas_qwen' / 'motor_json' / 'yaiwes_motor.py'
    sp = _iu.spec_from_file_location('yaiwes_motor', str(p))
    m = _iu.module_from_spec(sp)
    _sy.modules['yaiwes_motor'] = m
    sp.loader.exec_module(m)
    return m


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
             ('stepfun-ai/step-5-preview', 'Step 5 Preview', 'Codigo rapido: 2o en uso real OpenRouter'),
             ('deepseek-ai/deepseek-v4.1-flash', 'DeepSeek V4.1 Flash', 'Codigo: 3a opcion, solo si responde en <30 s')]
NV_TOPE = {'deepseek-ai/deepseek-v4.1-flash': 30}  # DeepSeek V4.1 Flash dio timeout >90 s el 16-oct: tope 30 s y se salta


def _ficha4_texto():
    ruta = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'fichas', 'fichas_qwen', 'fichas', 'ficha4-workflow-yaiwes.json')
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


def llamar_recurso(recurso, sistema, mensaje, limite_tokens=None, restante_s=None):
    recurso = str(recurso or '')
    msgs = ([{'role': 'system', 'content': str(sistema)[:2000]}] if sistema else []) + [{'role': 'user', 'content': str(mensaje or '')[:12000]}]
    if recurso not in recursos_ids():
        return 'ERROR: recurso desconocido. Validos: ' + ', '.join(sorted(recursos_ids()))
    if recurso.startswith('ficha4:'):
        if not LLM_CALL:
            return 'ERROR: GAP_FICHA4_HTTP (harness sin llm_call)'
        # DSL A06: ContextVar no cruza HTTP — la profundidad/capa/presupuesto viaja DENTRO del payload LLM_CALL
        d = LLM_CALL({'caller_id': 'tools-staff', 'plugin_id': 'tools', 'workflow_id': 'tools-staff', 'task_type': 'code', 'modelo': recurso[7:], 'messages': msgs,
                      'max_tokens': min(int(limite_tokens or 1500), 1500), 'delegacion_depth': 1, 'cap_tools': 'read',
                      'solo_lectura': True, 'presupuesto_s': min(120.0, float(restante_s or 120.0))})
        return str(d.get('reply') or '') if d.get('reply') else 'ERROR Ficha 4: ' + str(d.get('error') or 'sin respuesta') + ' ' + str(d.get('detalle') or '')
    if recurso.startswith('nvcode:'):
        if not LLM_NV:
            return 'ERROR: harness sin NVIDIA'
        s_, d = LLM_NV(recurso[7:], msgs, NV_TOPE.get(recurso[7:], 90))
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
    # cadena: GLM-5.3 -> Step 5 Preview -> DeepSeek V4.1 Flash (<30 s); el modelo pedido va primero
    ids = [x[0] for x in NV_CODIGO]
    m = str(a.get('modelo') or '')
    orden = ([m] if m in ids else []) + [x for x in ids if x != m]
    r = ''
    for mod_ in orden:
        r = llamar_recurso('nvcode:' + mod_, 'Eres un programador senior. Responde con codigo correcto y breve, en espanol.', a.get('mensaje'))
        if not str(r).startswith('ERROR') and str(r).strip():
            return r
    return r


def _t_enlazar(a):
    r = agente_enlazar(a)
    return json.dumps(r, ensure_ascii=False)[:1500]


TOOLS.extend([
    _fn('nvidia_codigo', 'Tool NVIDIA de codigo (GLM-5.3 por defecto; si falla Step 5 Preview y luego DeepSeek V4.1 Flash): escribe o revisa codigo y devuelve la respuesta. modelo opcional: z-ai/glm-5.3, stepfun-ai/step-5-preview o deepseek-ai/deepseek-v4.1-flash.', {'mensaje': S, 'modelo': S}, ['mensaje']),
    _fn('recurso_llm', 'Consulta un recurso LLM del staff de tools (ej. ficha4:ficha-qwen38max, nvcode:z-ai/glm-5.3, groq:openai/gpt-oss-120b) y devuelve su respuesta.', {'recurso': S, 'mensaje': S}, ['recurso', 'mensaje']),
    _fn('agente_enlazar', 'Enlaza un recurso LLM (modelo de la Ficha 4, NVIDIA codigo o Groq) a un agente del staff; si el agente no existe lo crea. Luego usa groq_agente(nombre, mensaje).', {'nombre': S, 'recurso': S, 'sistema': S}, ['nombre', 'recurso']),
])
FUNCS.update({'nvidia_codigo': _t_nvcodigo, 'recurso_llm': _t_recurso, 'agente_enlazar': _t_enlazar})
SISTEMA += (' Staff de tools: nvidia_codigo(mensaje) para codigo; recurso_llm(recurso, mensaje) para consultar un modelo de la Ficha 4 '
            '(ficha4:<id>), NVIDIA codigo (nvcode:<modelo>) o Groq; agente_enlazar(nombre, recurso) para elegir que modelo usa un agente.')


# --- t172u-t177u: Chat BOTS, ROOM, notas (bloc) y panel de pendientes (DSL DAG) como tools de CUALQUIER modelo del chat ---
# Mismo conector del chat MVP: LLM_CALL (plugin.py llm_call -> HTTP -> Ficha 4 -> modelo) y la misma memoria memoria_yaiwes.
# Los input blocks se guardan verbatim 1:1 (nunca se reescriben); la vista organizada es aparte.
import hashlib as _hl
import threading as _th
NOTAS_SCOPE = 'chat-ui:agenda:notas'
ESTADOS_DAG = ('🔴 pendiente', '🟡 en curso', '🟢 cerrado', '⚫ cancelado', '⚪ falta instrucciones o autorizacion')
_TRABAJOS = {}
_COMP_RAIZ = 'componentes/chat-bot'


def _mem_ag():
    from plugins.router_api_cliente import memory as _memory
    return _memory()


def _dato(clave):
    try:
        r = _mem_ag().sqlite.load(NOTAS_SCOPE, clave)  # clave exacta, el mas reciente primero (igual que plugins/orquestador)
        dd = (r[0].get('data') if r and isinstance(r[0], dict) else None) or {}
        return dd if isinstance(dd, dict) else {}
    except Exception:  # noqa: BLE001
        return {}


def _poner(clave, data):
    _mem_ag().save(NOTAS_SCOPE, clave, dict(data, clave=clave))


def notas_inputs(_a=None):
    return list(_dato('indice').get('inputs') or [])


def notas_guardar(a):
    texto = str(a.get('texto') or '')
    if not texto.strip():
        return {'error': 'TEXTO_VACIO'}
    sha = _hl.sha256(texto.encode('utf-8')).hexdigest()
    idx = notas_inputs()
    if any(x.get('sha256') == sha for x in idx):
        return {'ok': True, 'repetido': True, 'sha256': sha}
    iid = 'in-%04d' % (len(idx) + 1)
    _poner('input:' + iid, {'id': iid, 'texto': texto, 'sha256': sha, 'fecha': time.strftime('%Y-%m-%dT%H:%M:%S%z')})
    idx.append({'id': iid, 'sha256': sha, 'fecha': time.strftime('%Y-%m-%dT%H:%M:%S%z'), 'chars': len(texto)})
    _poner('indice', {'inputs': idx})
    return {'ok': True, 'id': iid, 'sha256': sha}


def notas_leer(a):
    iid = str(a.get('id') or '')
    d = _dato('input:' + iid)
    if not d:
        return {'error': 'INPUT_NO_EXISTE'}
    ok = _hl.sha256(str(d.get('texto') or '').encode('utf-8')).hexdigest() == d.get('sha256')
    return {'id': iid, 'texto': d.get('texto'), 'sha256': d.get('sha256'), 'intacto': ok, 'fecha': d.get('fecha')}


def notas_prompt(a=None):
    a = a or {}
    if a.get('prompt') not in (None, ''):
        p = a['prompt']
        if isinstance(p, str):
            try:
                p = json.loads(p)
            except ValueError:
                p = {'rol': p}
        if not isinstance(p, dict):
            return {'error': 'PROMPT_DEBE_SER_JSON_O_TEXTO'}
        _poner('prompt', {'prompt': p, 'fecha': time.strftime('%Y-%m-%dT%H:%M:%S%z')})
        return {'ok': True, 'propio': True}
    d = _dato('prompt')
    if d.get('prompt'):
        return {'prompt': d['prompt'], 'propio': True}
    ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'notas_organizador_prompt.json')
    with open(ruta, encoding='utf-8') as f:
        return {'prompt': json.load(f), 'propio': False}


def _json_de(txt):
    t = str(txt or '').strip()
    t = re.sub(r'^```(?:json)?\s*|\s*```$', '', t)
    i, j = t.find('{'), t.rfind('}')
    return json.loads(t[i:j + 1]) if i >= 0 and j > i else None


def _organizar():
    pr = notas_prompt().get('prompt') or {}
    entradas = [notas_leer({'id': x['id']}) for x in notas_inputs()]
    entradas = [{'id': e['id'], 'fecha': e.get('fecha'), 'texto': e.get('texto')} for e in entradas if e.get('texto')]
    if not entradas:
        return {'error': 'SIN_INPUTS'}
    if not LLM_CALL:
        return {'error': 'GAP_FICHA4_HTTP (harness sin llm_call)'}
    modelo = str(pr.get('modelo') or 'ficha-qwen38max')
    msgs = [{'role': 'system', 'content': json.dumps(pr, ensure_ascii=False)[:12000]},
            {'role': 'user', 'content': json.dumps({'inputs': entradas}, ensure_ascii=False)[-60000:]}]
    d = LLM_CALL({'caller_id': 'agenda-notas', 'plugin_id': 'puente_chat', 'workflow_id': 'notas-dag', 'task_type': 'code',
                  'modelo': modelo, 'messages': msgs, 'max_tokens': 6000})
    if not d.get('reply'):
        return {'error': 'GAP_FICHA4', 'detalle': str(d.get('error') or '') + ' ' + str(d.get('detalle') or ''), 'modelo': modelo}
    try:
        dag = _json_de(d['reply'])
    except ValueError:
        dag = None
    if not isinstance(dag, dict) or not isinstance(dag.get('nodos'), list):
        return {'error': 'LLM_SIN_JSON_DAG', 'modelo': modelo, 'respuesta': str(d['reply'])[:1500]}
    for n in dag['nodos']:
        if isinstance(n, dict) and n.get('estado') not in ESTADOS_DAG:
            n['estado_original'] = n.get('estado')
            n['estado'] = ESTADOS_DAG[4]
    vista = {'dag': dag, 'modelo': d.get('modelo') or modelo, 'inputs': len(entradas), 'fecha': time.strftime('%Y-%m-%dT%H:%M:%S%z')}
    _poner('vista', vista)
    return vista


def _en_hilo(tipo, fn):
    tid = tipo + '-' + _hl.sha256(str(time.time()).encode()).hexdigest()[:10]
    _TRABAJOS[tid] = {'estado': 'procesando'}

    def corre():
        try:
            _TRABAJOS[tid] = {'estado': 'completado', 'resultado': fn()}
        except Exception as x:  # noqa: BLE001
            _TRABAJOS[tid] = {'estado': 'error', 'error': type(x).__name__ + ' ' + str(x)[:200]}
    _th.Thread(target=corre, daemon=True).start()
    return {'estado': 'procesando', 'trabajo': tid}


def pendientes(a):
    acc = str(a.get('accion') or 'vista')
    if acc == 'organizar':
        return _en_hilo('dag', _organizar) if a.get('asincrono') else _organizar()
    if acc == 'prompt_leer':
        return notas_prompt()
    if acc == 'prompt_guardar':
        return notas_prompt({'prompt': a.get('prompt')})
    if acc == 'trabajo':
        return _TRABAJOS.get(str(a.get('trabajo') or ''), {'error': 'TRABAJO_NO_EXISTE'})
    return _dato('vista') or {'vacio': True}


def notas(a):
    acc = str(a.get('accion') or 'listar')
    if acc == 'guardar':
        return notas_guardar(a)
    if acc == 'leer':
        return notas_leer(a)
    return {'inputs': notas_inputs()}


ROOM_DEF = ['ficha-qwen38flash', 'ficha-dsv4flash']  # ROOM por defecto: Qwen 3.8 Flash + DeepSeek V4 Flash (README chat bot §3.10)


def _room(tema, part, rondas):
    nombres = {x['id']: x.get('nombre') or x['id'] for x in _ficha4_texto()}
    hilo = []
    for r in range(1, rondas + 1):
        for pid in part:
            nom = nombres.get(pid, pid)
            ctx = '\n'.join('[%s] %s' % (h['nombre'], h['texto']) for h in hilo[-24:])[-9000:]
            orden = ('SALA DE CONFERENCIAS. Eres «%s». Ronda %d de %d. Tema del Usuario: %s\nConversacion hasta ahora:\n%s\n'
                     'Coincide o rebate a los demas citando su nombre. Maximo 120 palabras, en espanol.') % (nom, r, rondas, tema, ctx or '(empiezas tu)')
            txt = llamar_recurso('ficha4:' + pid, 'Participas en ROOM CONFERENCIAS de YAIWES.', orden)
            hilo.append({'ronda': r, 'id': pid, 'nombre': nom, 'texto': str(txt)[:2000]})
    return {'tema': tema, 'rondas': rondas, 'participantes': part, 'turnos': hilo}


def room_debatir(a):
    tema = str(a.get('tema') or '').strip()
    if not tema:
        return {'error': 'FALTA_TEMA'}
    ok = {x['id'] for x in _ficha4_texto()}
    part = [p for p in (a.get('participantes') or ROOM_DEF) if p in ok][:6] or ROOM_DEF
    rondas = max(1, min(3, int(a.get('rondas') or 1)))
    if a.get('asincrono'):
        return _en_hilo('room', lambda: _room(tema, part, rondas))
    return _room(tema, part[:3], min(rondas, 2))  # tool del chat: tope 3 participantes x 2 rondas para no agotar el tiempo


_BOTS_OK = ('status', 'modelos', 'listar', 'crear', 'enviar', 'estado', 'mirror', 'aprobar', 'archivos', 'recibos', 'agentes_repo', 'repo_leer', 'arquitectura', 'vigilar')


def chat_bots(a):
    acc = str(a.get('accion') or 'listar')
    if acc not in _BOTS_OK:
        return {'error': 'ACCION_NO_PERMITIDA_DESDE_TOOL', 'permitidas': list(_BOTS_OK)}
    from plugins.orquestador import plugin as orq
    p = dict(a.get('datos') or {}) if isinstance(a.get('datos'), dict) else {}
    p.setdefault('seccion', a.get('seccion') or 'web-general')
    if acc == 'crear':
        p['creado_por'] = 'llm-chat'
    return orq.handle(acc, p)


def crear_agente(a):  # rama wip/chatbots-backend-mvp: la LLM del chat crea un agente en Chat BOTS
    return chat_bots({'accion': 'crear', 'seccion': a.get('seccion'), 'datos': {'nombre': a.get('nombre'), 'sistema': a.get('sistema'),
                                                                                'modelo': a.get('modelo') or 'ficha-qwen38flash'}})


def componentes_backend(a):
    comp = re.sub(r'[^\w.-]', '', str(a.get('componente') or ''))
    ruta = str(a.get('ruta') or '').strip('/')
    if '..' in ruta:
        return 'ERROR: ruta no permitida'
    base = _COMP_RAIZ + ('/' + comp + '/code' if comp else '')
    return github_leer({'repo': 'router-universal-router-inteligente-', 'ruta': base + ('/' + ruta if ruta and comp else ''), 'rama': 'main', 'lineas': a.get('lineas')})


def http_accion(action, p):
    # HTTP /plugins/puente_chat/call/<action> (mismo plugin del chat): notas, pendientes, room_debatir, chat_bots
    p = dict(p or {})
    if action == 'notas':
        return notas(p)
    if action == 'pendientes':
        return pendientes(dict(p, asincrono=p.get('asincrono', True)))
    if action == 'room_debatir':
        return room_debatir(dict(p, asincrono=True)) if p.get('accion') != 'trabajo' else _TRABAJOS.get(str(p.get('trabajo') or ''), {'error': 'TRABAJO_NO_EXISTE'})
    if action == 'chat_bots':
        return chat_bots(p)
    return {'error': 'ACCION_DESCONOCIDA'}


def _j(f):
    return lambda a: (lambda r: r if isinstance(r, str) else json.dumps(r, ensure_ascii=False)[:12000])(f(a))


_A = {'type': 'array', 'items': S}
TOOLS.extend([
    _fn('notas', 'Bloc de notas de Antonio: guarda un input block VERBATIM 1:1 (inmutable, con sha256), lista los inputs o lee uno. accion: guardar (texto), listar, leer (id ej. in-0001).', {'accion': S, 'texto': S, 'id': S}, ['accion']),
    _fn('pendientes', 'Panel de pendientes: organiza los input blocks en un DSL DAG (nodos=tareas, aristas=dependencias, 5 estados 🔴🟡🟢⚫⚪) con el prompt JSON editable. accion: vista, organizar, prompt_leer, prompt_guardar (prompt JSON), trabajo (trabajo).', {'accion': S, 'prompt': S, 'trabajo': S}, ['accion']),
    _fn('room_debatir', 'ROOM CONFERENCIAS: debate entre modelos de la Ficha 4 por turnos (cada uno coincide o rebate citando nombres). participantes: ids de la Ficha 4 (ej. ficha-qwen38max, ficha-qwen38flash, ficha-dsv4flash, ficha-glm52); rondas 1-2.', {'tema': S, 'participantes': _A, 'rondas': {'type': 'integer'}}, ['tema']),
    _fn('chat_bots', 'Chat BOTS (agentes sub-chat del chat abierto, max 50): accion status, modelos, listar, crear, enviar, estado, mirror, aprobar, archivos, recibos, agentes_repo, repo_leer, arquitectura, vigilar; datos: objeto con los campos de la accion (ej. {"id":"ag-...","mensaje":"..."}).', {'accion': S, 'seccion': S, 'datos': O}, ['accion']),
    _fn('crear_agente', 'Crea un agente (sub-chat) en Chat BOTS del chat abierto con su system y un modelo de la Ficha 4 (ficha-qwen38max, ficha-qwen38flash, ficha-dsv4pro, ficha-dsv4flash, ficha-glm52...).', {'nombre': S, 'sistema': S, 'modelo': S}, ['nombre', 'sistema']),
    _fn('componentes_backend', 'Lee los componentes del backend del chat bot descargados en router main "componentes/chat-bot" (agent-zero, OpenManus, OpenHands, openhands-software-agent-sdk, openhands-automation, Agent-S, browser-use, context7, rea, CLI-Anything, strix, artemis). Sin componente lista la carpeta; con componente y ruta lee code/<ruta>.', {'componente': S, 'ruta': S, 'lineas': S}, []),
])
FUNCS.update({'notas': _j(notas), 'pendientes': _j(pendientes), 'room_debatir': _j(room_debatir), 'chat_bots': _j(chat_bots),
              'crear_agente': _j(crear_agente), 'componentes_backend': componentes_backend})
SISTEMA += (' Tienes tambien: notas (bloc de notas verbatim), pendientes (DSL DAG de tareas con prompt JSON editable), room_debatir (ROOM '
            'CONFERENCIAS entre modelos de la Ficha 4), chat_bots y crear_agente (Chat BOTS) y componentes_backend (codigo de los componentes del chat bot).')


# ===== DSL G18/G19/G10 — paralelo por tool, buzon al Director y reglas de la biblioteca =====
import concurrent.futures as _cf_d
from contextvars import ContextVar as _CV

_PROF_DELEGACION = _CV('riu_prof_delegacion', default=0)  # DSL G18: un solo nivel — un subagente no delega
_REGLA_NODO = _CV('riu_regla_nodo', default=0)  # DSL G15: max 5 lecturas de regla por nodo


def _t_delegar_paralelo(a):
    # DSL G18/A06: fan-out por el MISMO Harness; cada subtarea hereda CAP_READ, max_tokens<=1500 y deadline <=120 s del nodo
    if _PROF_DELEGACION.get() >= 1:
        return 'GAP DELEGACION_ANIDADA: un subagente no puede crear mas subagentes (un solo nivel)'
    subs = (a.get('subtareas') or [])[:12]
    if not subs:
        return 'GAP DELEGACION_VACIA: falta subtareas'
    n = max(1, min(int(a.get('max_paralelo') or 4), 4))  # AUDIT: tope 4 = concurrencia recomendada Token Plan (3-4 agentes)
    try:
        from fichas.fichas_qwen import plugin as _fq_d  # noqa: PLC0415
        dl_nodo = float((_fq_d._NODO_CALL.get() or {}).get('deadline') or 0)  # deadline del nodo padre (ContextVar del lado ficha)
    except Exception:  # noqa: BLE001
        dl_nodo = 0

    def uno(i, s):
        tok = _PROF_DELEGACION.set(1)
        t0 = time.monotonic()
        restante = min(120.0, (dl_nodo - t0) if dl_nodo else 120.0)
        try:
            if restante <= 2:
                return i, 'GAP SUBTAREA_TIMEOUT'
            r = llamar_recurso(str(s.get('recurso') or 'ficha4:ficha-qwen38flash'), '', str(s['texto'])[:6000],
                               limite_tokens=int(s.get('max_tokens') or 1500), restante_s=restante)
            if _tm.monotonic() - t0 > 122:
                return i, 'GAP SUBTAREA_TIMEOUT'
            return i, r
        except Exception as x:  # noqa: BLE001
            return i, 'GAP SUBTAREA: ' + str(x)[:200]
        finally:
            _PROF_DELEGACION.reset(tok)
    with _cf_d.ThreadPoolExecutor(max_workers=n) as ex:
        res = dict(f.result() for f in _cf_d.as_completed([ex.submit(uno, i, s) for i, s in enumerate(subs)]))
    return '\n\n'.join('[SUBTAREA %d] %s' % (i + 1, str(res[i])[:4000]) for i in range(len(subs)))


def _t_preguntar_director(a):
    # DSL G19: el modelo deja una pregunta en la cola del Director y SIGUE con otra tarea (no se detiene)
    try:
        from fichas.fichas_qwen import plugin as _fq  # noqa: PLC0415
        db = _fq._buzon_db()
        if db is None:
            return 'GAP_BUZON_SIN_SQLITE'
        import time as _tt
        db.execute('INSERT INTO pendientes_director (proceso_id, pregunta, creado, respuesta, respondido) VALUES (?,?,?,NULL,NULL)',
                   (str(a.get('proceso_id') or ''), str(a.get('pregunta') or '')[:2000], _tt.time()))
        db.commit()
        return 'registrado; continua con otra tarea'
    except Exception as x:  # noqa: BLE001
        return 'GAP PREGUNTAR_DIRECTOR: ' + str(x)[:200]


def _t_regla_yaiwes(a):
    # DSL G10 capa D: el modelo pide UNA regla SRC-xxx o un heading, a demanda (max 5 por nodo)
    if _REGLA_NODO.get() >= 5:
        return 'GAP REGLA_LIMITE: maximo 5 reglas por nodo (lee solo la que necesitas)'
    _REGLA_NODO.set(_REGLA_NODO.get() + 1)
    try:
        from plugins.puente_chat import plugin as _pp  # noqa: PLC0415
        import json as _j2
        man = _j2.loads(_pp._prompt_lib('manifest.json') or '{}')
        q = str(a.get('id') or a.get('heading') or '').strip()
        hit = None
        if q.upper().startswith('SRC-'):
            hit = q.upper()
        else:
            for rid, rm in (man.get('reglas') or {}).items():
                if str(rm.get('heading') or '').upper() == q.upper() or q.upper() in str(rm.get('heading') or '').upper():
                    hit = rid
                    break
        if not hit or hit not in (man.get('reglas') or {}):
            return 'GAP REGLA_NO_EXISTE: ' + q + ' — validas: ' + ', '.join(sorted((man.get('reglas') or {}).keys())[:114])
        return _pp._prompt_lib(man['reglas'][hit]['archivo']) or 'GAP REGLA_VACIA'
    except Exception as x:  # noqa: BLE001
        return 'GAP REGLA_YAIWES: ' + str(x)[:200]


TOOLS.extend([
    _fn('delegar_paralelo', 'Reparte subtareas a varios modelos/recursos A LA VEZ (max 4 en paralelo, un solo nivel; subagentes solo lectura). subtareas: [{texto, recurso?, max_tokens?}] — recurso: ficha4:<modelo> | nvcode:<modelo> | groq:<modelo>.',
        {'subtareas': {'type': 'array', 'items': O}, 'max_paralelo': {'type': 'integer'}}, ['subtareas']),
    _fn('preguntar_director', 'Deja una pregunta en la cola del Director sin detenerte: devuelve "registrado" y tu sigues con otra tarea; la respuesta llega como instruccion en la siguiente vuelta.',
        {'pregunta': S, 'proceso_id': S}, ['pregunta']),
    _fn('regla_yaiwes', 'Lee UNA regla verbatim de la biblioteca YAIWES por id (SRC-001..SRC-114) o por heading. Maximo 5 por nodo — pide solo la que necesitas.',
        {'id': S, 'heading': S}, []),
])
FUNCS.update({'delegar_paralelo': _t_delegar_paralelo, 'preguntar_director': _t_preguntar_director,
              'regla_yaiwes': _t_regla_yaiwes})
SISTEMA += (' delegar_paralelo (reparte subtareas a varios modelos a la vez, un nivel),'
            ' preguntar_director (pregunta al Director sin detenerte), regla_yaiwes (una regla verbatim a demanda).')



# --- PARCHE_MIRROR (Director 2026-10-20): agentes mirror como tool del catalogo ---
_MIRRORS_BASE = tuple('%s-%02d' % (t, i) for t in ('hermes', 'openclaw', 'claudecode', 'codex') for i in range(1, 11))


def _t_mirror(a):
    agente = str(a.get('agente') or '')[:60]
    mensaje = str(a.get('mensaje') or '')
    modelo = str(a.get('modelo') or '')[:120]
    if not agente or not mensaje:
        return 'GAP_MIRROR_ARGS: agente y mensaje requeridos'
    if not modelo:
        try:
            from plugins.puente_chat import plugin as _pc
            ses = str((_pc._IDS_CTX.get() or {}).get('sesion') or '')
            modelo = str((_pc._mirror_cfg(ses).get('modelo') or {}).get(agente) or '')
        except Exception:
            modelo = ''
    if not modelo:
        return 'GAP_MIRROR_SIN_MODELO: configura el mirror con mirror_configurar(agente, modelo) o pasa modelo='
    return llamar_recurso(modelo if ':' in modelo else 'ficha4:' + modelo,
                          'Eres el agente mirror %s del sistema RIU. Responde correcto y breve.' % agente,
                          mensaje)


TOOLS.append(_fn('mirror_tarea',
    'Delega una tarea a un agente mirror (hermes-NN/openclaw-NN/claudecode-NN/codex-NN). El mirror usa como motor LLM la ficha/modelo configurada por sesion (ficha4:, ficha5, nvcode: o groq:) o el parametro modelo.',
    {'agente': S, 'mensaje': S, 'modelo': S}, ['agente', 'mensaje']))
FUNCS['mirror_tarea'] = _t_mirror
SISTEMA += ' mirror_tarea(agente, mensaje[, modelo]) delega una tarea a un agente mirror del staff.'
