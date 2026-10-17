"""Mirror de agentes por ENLACE (orden de Antonio, 17-oct: «Los mirror es para usarlo en chat bot. Así no copias de nuevo todo el agente»).

Nada del codigo de los agentes se copia al repo del Router ni al disco: el agente de Chat BOTS guarda solo el enlace
(repo + ruta) y lee por llamada, cuando hace falta, un archivo del repo del agente (mismo patron que plugins/hf_skills).
Fuentes:
- Flota: agent_fleet_registry.json de main (campos source_repo + source_path), leido por llamada.
- OpenClaw y Hermes: sus propios repos (forks del Director), fuera de main."""
from __future__ import annotations
import json, os, time, urllib.error, urllib.parse, urllib.request

REGISTRO = ('maxbry123-commits/router-universal-router-inteligente-', 'main',
            'chat router/workflow Loops code Yaiwes/code/wordflow_loop/wordflow_loop/agent_fleet/agent_fleet_registry.json')
PROPIOS = [{'agent_id': 'openclaw', 'nombre': 'OpenClaw', 'repo': 'maxbry123-commits/openclaw', 'ruta': '', 'roles': []},
           {'agent_id': 'hermes', 'nombre': 'Hermes', 'repo': 'maxbry123-commits/hermes-agent', 'ruta': '', 'roles': []}]
MAX_LEER = 12000
_CACHE = {'t': 0.0, 'v': None}
TTL_S = 600


def _get(repo, ruta, ref='main'):
    url = 'https://api.github.com/repos/%s/contents/%s?ref=%s' % (repo, urllib.parse.quote(ruta.strip('/')), urllib.parse.quote(ref))
    h = {'Accept': 'application/vnd.github.raw', 'User-Agent': 'riu-orq-mirror'}
    tok = (os.getenv('GITHUB_TOKEN') or '').strip()
    if tok:
        h['Authorization'] = 'Bearer ' + tok
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=20) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, b''
    except Exception:  # noqa: BLE001 - red caida
        return 0, b''


def enlace(ag):
    return 'https://github.com/%s%s' % (ag['repo'], ('/tree/main/' + urllib.parse.quote(ag['ruta'])) if ag.get('ruta') else '')


def agentes():
    """Lista de agentes con enlace. El registro se lee por llamada y se cachea TTL_S en RAM."""
    if _CACHE['v'] is not None and time.time() - _CACHE['t'] < TTL_S:
        return _CACHE['v']
    st, raw = _get(REGISTRO[0], REGISTRO[2], REGISTRO[1])
    flota = []
    if st == 200:
        try:
            for x in json.loads(raw.decode('utf-8', 'replace')).get('agents') or []:
                if x.get('source_repo', '').count('/') == 1:  # sin repo (operator_runtime) no hay enlace: se omite
                    flota.append({'agent_id': x.get('agent_id'), 'nombre': x.get('display_name') or x.get('agent_id'),
                                  'repo': x['source_repo'], 'ruta': x.get('source_path') or '', 'roles': x.get('roles') or []})
        except ValueError:
            pass
    v = PROPIOS + [x for x in flota if x['agent_id'] not in {p['agent_id'] for p in PROPIOS}]
    for x in v:
        x['url'] = enlace(x)
    if st == 200:  # sin registro (red caida / 403) no se cachea: se reintenta en la proxima llamada
        _CACHE.update(t=time.time(), v=v)
    return v


def buscar(agent_id):
    return next((x for x in agentes() if x['agent_id'] == agent_id), None)


def leer(agent_id, ruta='README.md'):
    """Lee UN archivo del repo del agente por llamada (no se guarda). ruta relativa a la carpeta del agente."""
    ag = buscar(agent_id)
    if not ag:
        return {'error': 'AGENTE_REPO_NO_EXISTE'}
    r = str(ruta or 'README.md').strip('/')
    if '..' in r.split('/'):
        return {'error': 'RUTA_INVALIDA'}
    st, raw = _get(ag['repo'], (ag['ruta'] + '/' + r) if ag.get('ruta') else r)
    if st != 200:
        return {'error': 'GITHUB_HTTP', 'http': st, 'url': ag['url']}
    return {'url': ag['url'], 'ruta': r, 'texto': raw[:MAX_LEER].decode('utf-8', 'replace'), 'truncado': len(raw) > MAX_LEER}
