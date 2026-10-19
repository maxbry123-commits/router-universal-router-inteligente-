#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MCP Puente GitHub — servidor MCP por stdio que expone las tools GitHub del
Router Inteligente Universal (github_leer, github_escribir, github_api) para que
Claude entre a GitHub a traves del router, sin Vercel ni HuggingFace.

Uso (config MCP de Claude):
    python3 "router inteligente universal/mcp_puente_github.py"
    env: GITHUB_PERSONAL_ACCESS_TOKEN=<pat con contents:write>
"""
import base64
import json
import os
import sys
import urllib.request
import urllib.parse
import urllib.error

OWNER = 'maxbry123-commits'
API = 'https://api.github.com'
TOOLS = [
    {'name': 'github_leer',
     'description': 'Lee un archivo, o lista una carpeta, de un repositorio de GitHub de maxbry123-commits. En archivos largos usa lineas (ej "200-400") para leer un rango.',
     'inputSchema': {'type': 'object',
                     'properties': {'repo': {'type': 'string'},
                                    'ruta': {'type': 'string'},
                                    'rama': {'type': 'string'},
                                    'lineas': {'type': 'string'}},
                     'required': ['repo']}},
    {'name': 'github_escribir',
     'description': 'Crea o cambia un archivo en un repositorio de GitHub de maxbry123-commits (hace un commit).',
     'inputSchema': {'type': 'object',
                     'properties': {'repo': {'type': 'string'},
                                    'ruta': {'type': 'string'},
                                    'contenido': {'type': 'string'},
                                    'mensaje': {'type': 'string'},
                                    'rama': {'type': 'string'}},
                     'required': ['repo', 'ruta', 'contenido']}},
    {'name': 'github_api',
     'description': 'Llama a la API de GitHub con los permisos de la cuenta del Director. metodo: GET, POST, PUT, PATCH o DELETE.',
     'inputSchema': {'type': 'object',
                     'properties': {'metodo': {'type': 'string'},
                                    'ruta': {'type': 'string'},
                                    'cuerpo': {'type': 'object'}},
                     'required': ['metodo', 'ruta']}},
]


def _token():
    t = os.environ.get('GITHUB_PERSONAL_ACCESS_TOKEN') or os.environ.get('RIU_GITHUB_PAT')
    if not t:
        raise RuntimeError('FALTA GITHUB_PERSONAL_ACCESS_TOKEN en el entorno')
    return t


def _peticion(metodo, url, cuerpo=None, espera=40):
    req = urllib.request.Request(url, method=metodo)
    req.add_header('Authorization', 'Bearer ' + _token())
    req.add_header('Accept', 'application/vnd.github+json')
    req.add_header('X-GitHub-Api-Version', '2022-11-28')
    req.add_header('User-Agent', 'riu-mcp-puente-github')
    datos = None
    if cuerpo is not None:
        datos = json.dumps(cuerpo).encode('utf-8')
        req.add_header('Content-Type', 'application/json')
    try:
        with urllib.request.urlopen(req, datos, timeout=espera) as r:
            raw = r.read().decode('utf-8', 'replace')
            return r.status, (json.loads(raw) if raw else {})
    except urllib.error.HTTPError as e:
        raw = e.read().decode('utf-8', 'replace')
        try:
            return e.code, json.loads(raw)
        except ValueError:
            return e.code, raw


def github_leer(a):
    repo, ruta = a.get('repo'), a.get('ruta') or ''
    rama = a.get('rama') or 'main'
    lineas = a.get('lineas')
    if not ruta:
        ruta = ''
    q = urllib.parse.quote(ruta.strip('/'), safe='')
    url = '%s/repos/%s/%s/contents/%s?ref=%s' % (API, OWNER, repo, q, urllib.parse.quote(rama))
    st, d = _peticion('GET', url)
    if st >= 400:
        return 'ERROR %s: %s' % (st, json.dumps(d)[:400])
    if isinstance(d, list):
        return '\n'.join('%s%s %s' % ('[D] ' if x.get('type') == 'dir' else '    ',
                                    x.get('name'), x.get('size', '')) for x in d)
    if d.get('type') == 'file':
        try:
            txt = base64.b64decode(d.get('content') or '').decode('utf-8', 'replace')
        except Exception:
            return 'ERROR: no se pudo decodificar el archivo'
        if lineas:
            partes = str(lineas).split('-', 1)
            try:
                ini = max(1, int(partes[0])) - 1
                fin = int(partes[1]) if len(partes) > 1 and partes[1].strip() else None
                txt = '\n'.join(txt.split('\n')[ini:fin])
            except ValueError:
                return 'ERROR: lineas invalido (usa "200-400")'
        return txt
    return json.dumps(d)[:2000]


def github_escribir(a):
    repo, ruta = a.get('repo'), a.get('ruta')
    contenido, mensaje = a.get('contenido'), a.get('mensaje') or 'mcp puente: update'
    rama = a.get('rama') or 'main'
    q = urllib.parse.quote(str(ruta).strip('/'), safe='')
    base = '%s/repos/%s/%s/contents/%s' % (API, OWNER, repo, q)
    st, prev = _peticion('GET', base + '?ref=' + urllib.parse.quote(rama))
    sha = prev.get('sha') if st == 200 and isinstance(prev, dict) else None
    cuerpo = {'message': mensaje, 'branch': rama,
              'content': base64.b64encode(str(contenido).encode('utf-8')).decode('ascii')}
    if sha:
        cuerpo['sha'] = sha
    st, d = _peticion('PUT', base, cuerpo)
    if st >= 400:
        return 'ERROR %s: %s' % (st, json.dumps(d)[:400])
    return json.dumps({'ok': True, 'commit': (d.get('commit') or {}).get('sha', '')[:10],
                       'path': (d.get('content') or {}).get('path')})


def github_api(a):
    metodo = str(a.get('metodo') or 'GET').upper()
    if metodo not in ('GET', 'POST', 'PUT', 'PATCH', 'DELETE'):
        return 'ERROR: metodo invalido'
    st, d = _peticion(metodo, API + a.get('ruta', ''), a.get('cuerpo'))
    return json.dumps({'status': st, 'data': d})[:12000]


FUNCS = {'github_leer': github_leer, 'github_escribir': github_escribir, 'github_api': github_api}


def _responder(req_id, resultado=None, error=None):
    msg = {'jsonrpc': '2.0', 'id': req_id}
    if error is not None:
        msg['error'] = {'code': -32000, 'message': str(error)}
    else:
        msg['result'] = resultado
    sys.stdout.write(json.dumps(msg, ensure_ascii=False) + '\n')
    sys.stdout.flush()


def main():
    for linea in sys.stdin:
        linea = linea.strip()
        if not linea:
            continue
        try:
            req = json.loads(linea)
        except ValueError:
            continue
        metodo = req.get('method')
        req_id = req.get('id')
        if metodo in ('notifications/initialized', 'notifications/cancelled'):
            continue
        if metodo == 'initialize':
            _responder(req_id, {'protocolVersion': req.get('params', {}).get('protocolVersion', '2024-11-05'),
                                'capabilities': {'tools': {}},
                                'serverInfo': {'name': 'riu-mcp-puente-github', 'version': '1.0.0'}})
        elif metodo == 'tools/list':
            _responder(req_id, {'tools': TOOLS})
        elif metodo == 'tools/call':
            p = req.get('params') or {}
            fn = FUNCS.get(p.get('name'))
            if not fn:
                _responder(req_id, error='tool desconocida: %s' % p.get('name'))
                continue
            try:
                texto = fn(p.get('arguments') or {})
                _responder(req_id, {'content': [{'type': 'text', 'text': texto}],
                                    'isError': texto.startswith('ERROR') or texto.startswith('FALTA')})
            except Exception as x:  # noqa: BLE001
                _responder(req_id, {'content': [{'type': 'text', 'text': 'ERROR: ' + str(x)[:400]}],
                                    'isError': True})
        elif req_id is not None:
            _responder(req_id, error='metodo no soportado: %s' % metodo)


if __name__ == '__main__':
    main()
