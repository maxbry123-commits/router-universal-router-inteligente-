"""Pruebas del MVP backend de Chat BOTS (gobierno, mirror por enlace, arquitectura). Sin red ni modelos: memoria y harness falsos.
Corre en GitHub Actions (riu-chatbots-backend-verify.yml), no en la computadora del bot."""
import json, os, sys, time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
os.environ['RIU_ORQ_DIR'] = '/tmp/riu-orq-test'
os.environ['ORQ_SANDBOX'] = 'local'

from plugins.orquestador import plugin as orq, gobierno as gob, mirror_repos as mir, arquitectura as arq  # noqa: E402


class _SQL:
    def __init__(self): self.d = {}
    def save(self, s, k, v): self.d[(s, k)] = json.loads(json.dumps(v))
    def load(self, s, k): return [{'data': self.d[(s, k)]}] if (s, k) in self.d else []
    def health(self): return {'status': 'CONNECTED'}


class _Mem:
    def __init__(self): self.sqlite = _SQL()
    def save(self, s, k, v): self.sqlite.save(s, k, v)


MEM = _Mem()
orq._mem = lambda: MEM
RESP = {'txt': 'hola'}


def _puente(accion, cuerpo):
    if accion == 'chat_async':
        return {'proceso_id': 'p-' + cuerpo['request_id']}
    return {'estado': 'listo', 'choices': [{'message': {'content': RESP['txt']}}]}


orq._puente = _puente


def _nuevo(**kw):
    orq._CACHE.clear()
    return orq.handle('crear', {'seccion': 'test', 'nombre': 'A', **kw})['agente']


def test_goal_lock_y_recibos():
    a = _nuevo(objetivo='sumar 2+2')
    assert a['objetivo'] == 'sumar 2+2'
    r = orq.handle('configurar', {'id': a['id'], 'seccion': 'test', 'objetivo': 'otra cosa'})
    assert r['error'] == 'OBJETIVO_BLOQUEADO'
    r = orq.handle('configurar', {'id': a['id'], 'seccion': 'test', 'objetivo': 'otra cosa', 'confirmado': True})
    assert r['agente']['objetivo'] == 'otra cosa'
    rec = orq.handle('recibos', {'id': a['id'], 'seccion': 'test'})
    assert [x['que'] for x in rec['recibos']] == ['crear', 'objetivo'] and rec['objetivo_intacto']
    assert rec['recibos'][1]['prev'] == rec['recibos'][0]['hash']


def test_enviar_estado_y_loop():
    a = _nuevo()
    for _ in range(3):
        orq.handle('enviar', {'id': a['id'], 'seccion': 'test', 'mensaje': 'hola'})
        v = orq.handle('estado', {'id': a['id'], 'seccion': 'test'})['agente']
    assert v['estado'] == 'bloqueado' and v['fallo'] == 'FAIL_MODEL'  # 3 respuestas iguales = loop


def test_watchdog_y_reiniciar():
    a = _nuevo()
    orq.handle('enviar', {'id': a['id'], 'seccion': 'test', 'mensaje': 'x'})
    ag = orq._cargar(a['id'], 'test'); ag['t0'] = time.time() - gob.TIMEOUT_S - 1
    r = orq.handle('vigilar', {'seccion': 'test'})
    assert a['id'] in r['recuperados']
    v = orq._vista(orq._cargar(a['id'], 'test'))
    assert v['estado'] == 'error' and v['fallo'] == 'FAIL_TIMEOUT'
    assert orq.handle('reiniciar', {'id': a['id'], 'seccion': 'test'})['agente']['estado'] == 'activo'


def test_redaccion_secretos():
    t = gob.redactar('token hf_' + 'a' * 30 + ' y ghp_' + 'b' * 30)
    assert 'hf_a' not in t and 'ghp_b' not in t and t.count('***') == 2


def test_mirror_por_enlace_sin_copiar():
    reg = {'agents': [{'agent_id': 'opencode', 'display_name': 'OpenCode', 'source_repo': 'maxbry123-commits/Agentes-motores-Wordflow-YAIWES',
                       'source_path': 'OpenCode/OpenCode', 'roles': ['writer']},
                      {'agent_id': 'goose', 'source_repo': 'operator_runtime', 'source_path': None}]}
    llamadas = []

    def _get(repo, ruta, ref='main'):
        llamadas.append((repo, ruta))
        return (200, json.dumps(reg).encode()) if ruta.endswith('agent_fleet_registry.json') else (200, b'# README OpenCode')
    mir._get = _get; mir._CACHE.update(t=0.0, v=None)
    ids = [x['agent_id'] for x in orq.handle('agentes_repo', {})['agentes']]
    assert ids == ['openclaw', 'hermes', 'opencode']  # goose sin repo: omitido
    ag = next(x for x in mir.agentes() if x['agent_id'] == 'opencode')
    assert ag['url'] == 'https://github.com/maxbry123-commits/Agentes-motores-Wordflow-YAIWES/tree/main/OpenCode/OpenCode'
    orq._CACHE.clear()
    m = orq.handle('mirror', {'seccion': 'test', 'de': 'repo:hermes'})['agente']
    assert m['repo']['url'] == 'https://github.com/maxbry123-commits/hermes-agent' and m['archivos'] == []
    assert 'hermes-agent' in orq._mensajes_llm(orq._cargar(m['id'], 'test'))[0]['content']
    r = orq.handle('repo_leer', {'agent_id': 'opencode'})
    assert r['texto'] == '# README OpenCode' and llamadas[-1] == ('maxbry123-commits/Agentes-motores-Wordflow-YAIWES', 'OpenCode/OpenCode/README.md')
    assert orq.handle('repo_leer', {'agent_id': 'opencode', 'ruta': '../x'})['error'] == 'RUTA_INVALIDA'


def test_arquitectura_archify():
    d = orq.handle('arquitectura', {})
    g = d['diagrama']
    assert g['schema_version'] == 1 and g['diagram_type'] == 'architecture' and g['meta']['title'] and g['meta']['output']
    ids = {c['id'] for c in g['components']}
    assert all(c['from'] in ids and c['to'] in ids for c in g['connections'])
    tipos = {'frontend', 'backend', 'database', 'cloud', 'security', 'messagebus', 'external'}
    assert all(c['type'] in tipos for c in g['components'])
    assert {p['estado'] for p in d['piezas']} <= {'hecho', 'en_curso', 'pendiente'}


def test_ficha_acciones():
    f = json.loads((RAIZ / 'plugins/orquestador/ficha.json').read_text())
    for a in ('vigilar', 'reiniciar', 'recibos', 'agentes_repo', 'repo_leer', 'arquitectura'):
        assert a in f['ejecucion']['allowed_actions']
