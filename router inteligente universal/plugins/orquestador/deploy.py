"""Enrutador de deploy: GitHub, Hugging Face y Vercel. Solo recibe el token de acceso, lo guarda como secreto y ejecuta.
El token: (1) se recibe una vez por token_guardar: RAM + cifrado (scrypt+AES-256-GCM con RIU_VAULT_PASSPHRASE) en SQLite gov, o (2) sale del banco/entorno
(GITHUB_TOKEN, HF_TOKEN, VERCEL_TOKEN). NUNCA se devuelve, imprime, guarda en claro ni entra al sandbox.
Sube los archivos de la carpeta del agente (sandbox/archivos)."""
from __future__ import annotations
import base64, json, os, urllib.parse, urllib.request
from pathlib import Path

_SECRETOS: dict[str, str] = {}
_ENV = {'github': ['GITHUB_TOKEN', 'GH_TOKEN'], 'hf': ['HF_WRITE_TOKEN', 'HF_TOKEN'], 'vercel': ['VERCEL_TOKEN']}


_SCOPE = 'chat-ui:orq:gov:tokens'  # ":gov:" -> la fachada lo deja SOLO en SQLite (sin grafo ni replicas); viaja al bucket ya cifrado


def _clave(salt):
    from cryptography.hazmat.primitives.kdf.scrypt import Scrypt  # mismo esquema que el Banco de claves: scrypt + AES-256-GCM
    pw = os.environ.get('RIU_VAULT_PASSPHRASE') or os.environ.get('FICHA_CLAVE_BANCO') or ''
    if not pw:
        raise RuntimeError('SIN_RIU_VAULT_PASSPHRASE')
    return Scrypt(salt=salt, length=32, n=2 ** 15, r=8, p=1).derive(pw.encode())


def _cifrado_guardar(destino, token):
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    salt, nonce = os.urandom(16), os.urandom(12)
    ct = AESGCM(_clave(salt)).encrypt(nonce, token.encode(), destino.encode())
    from integration.chat_mvp.memoria_loader import _memory
    _memory().save(_SCOPE, 'token:' + destino, {'alg': 'scrypt+aes-256-gcm', 'salt': base64.b64encode(salt).decode(), 'nonce': base64.b64encode(nonce).decode(), 'ct': base64.b64encode(ct).decode()})


def _cifrado_leer(destino):
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        from integration.chat_mvp.memoria_loader import _memory
        r = _memory().sqlite.load(_SCOPE, 'token:' + destino)
        if not r:
            return ''
        d = r[0]['data']
        return AESGCM(_clave(base64.b64decode(d['salt']))).decrypt(base64.b64decode(d['nonce']), base64.b64decode(d['ct']), destino.encode()).decode()
    except Exception:  # noqa: BLE001
        return ''


def _token(destino):
    if _SECRETOS.get(destino):
        return _SECRETOS[destino]
    t = _cifrado_leer(destino)
    if t:
        _SECRETOS[destino] = t
        return t
    try:
        from integration.chat_mvp import providers
        ks = providers.env_keys({'github': 'github', 'hf': 'hf', 'vercel': 'vercel'}[destino])
        if ks:
            return ks[0]
    except Exception:  # noqa: BLE001
        pass
    return next((os.getenv(n) for n in _ENV.get(destino, []) if os.getenv(n)), '')


def destinos():
    return {d: bool(_token(d)) for d in _ENV}  # solo si hay token, jamas el valor


def guardar_token(destino, token):
    if destino not in _ENV:
        return {'error': 'DESTINO_INVALIDO', 'validos': list(_ENV)}
    if len(token) < 8:
        return {'error': 'TOKEN_INVALIDO'}
    _SECRETOS[destino] = token
    try:
        _cifrado_guardar(destino, token)
        return {'guardado': True, 'destino': destino, 'cifrado': True}
    except Exception as x:  # noqa: BLE001 - nunca se guarda en claro
        return {'guardado': True, 'destino': destino, 'cifrado': False, 'aviso': 'solo en RAM: ' + (str(x) if 'PASSPHRASE' in str(x) else type(x).__name__)}


def _req(metodo, url, tok, cuerpo=None, ctype='application/json'):
    data = cuerpo if isinstance(cuerpo, (bytes, type(None))) else json.dumps(cuerpo).encode()
    r = urllib.request.Request(url, data=data, method=metodo, headers={'Authorization': 'Bearer ' + tok, 'Content-Type': ctype, 'User-Agent': 'riu-orquestador'})
    try:
        with urllib.request.urlopen(r, timeout=60) as x:
            return x.status, json.loads(x.read() or b'{}')
    except urllib.error.HTTPError as e:
        return e.code, {'error': e.read().decode('utf-8', 'replace')[:300].replace(tok, '***')}


def desplegar(destino, repo, carpeta: Path, rama='main', dry_run=False, confirmado=False):
    archivos = sorted(f for f in Path(carpeta).glob('*') if f.is_file())
    plan = {'destino': destino, 'repo': repo, 'rama': rama, 'archivos': [f.name for f in archivos]}
    if destino not in _ENV:
        return {'error': 'DESTINO_INVALIDO', 'validos': list(_ENV)}
    if not repo or not archivos:
        return {'error': 'FALTA_REPO_O_ARCHIVOS', **plan}
    tok = _token(destino)
    if not tok:
        return {'error': 'SIN_TOKEN', **plan}
    if dry_run:
        return {'estado': 'plan', **plan}
    if not confirmado:
        return {'error': 'FALTA_CONFIRMACION', **plan}  # Desplegar pide confirmacion cada vez
    if destino == 'github':
        hechos = []
        for f in archivos:
            url = 'https://api.github.com/repos/%s/contents/%s' % (repo, urllib.parse.quote(f.name))
            s, cur = _req('GET', url + '?ref=' + urllib.parse.quote(rama), tok)
            body = {'message': 'orquestador: ' + f.name, 'content': base64.b64encode(f.read_bytes()).decode(), 'branch': rama}
            if s == 200 and cur.get('sha'):
                body['sha'] = cur['sha']
            s, d = _req('PUT', url, tok, body)
            hechos.append({'archivo': f.name, 'http': s})
        return {'estado': 'ok' if all(h['http'] < 300 for h in hechos) else 'parcial', 'resultados': hechos, **plan}
    if destino == 'hf':  # repo "spaces/usuario/nombre" o "usuario/nombre" (model); commit NDJSON
        tipo, rid = (repo.split('/', 1) if repo.split('/')[0] in ('spaces', 'datasets', 'models') else ('models', repo))
        lineas = [json.dumps({'key': 'header', 'value': {'summary': 'orquestador deploy'}})]
        lineas += [json.dumps({'key': 'file', 'value': {'path': f.name, 'content': base64.b64encode(f.read_bytes()).decode(), 'encoding': 'base64'}}) for f in archivos]
        s, d = _req('POST', 'https://huggingface.co/api/%s/%s/commit/%s' % (tipo, rid, rama), tok, '\n'.join(lineas).encode(), 'application/x-ndjson')
        return {'estado': 'ok' if s < 300 else 'error', 'http': s, 'commit': d.get('commitUrl'), **plan}
    team = os.getenv('VERCEL_TEAM_ID') or ''
    s, d = _req('POST', 'https://api.vercel.com/v13/deployments' + ('?teamId=' + team if team else ''), tok,
                {'name': repo, 'files': [{'file': f.name, 'data': base64.b64encode(f.read_bytes()).decode(), 'encoding': 'base64'} for f in archivos],
                 'projectSettings': {'framework': None}, 'target': 'preview'})
    return {'estado': 'ok' if s < 300 else 'error', 'http': s, 'url': d.get('url'), **plan}

