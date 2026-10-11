"""Pruebas offline del DAG final (sin red, sin dependencias externas): gobernanza solo SQLite, rehidratacion,
fuente cambiada, anclas -> Graphiti (sin constitucion), concurrencia de modelos. python test_dag_final.py"""
import asyncio, importlib.util, json, os, sys, threading
from pathlib import Path

HERE = Path(__file__).resolve()
REPO = HERE.parents[3] if len(HERE.parents) > 3 else HERE.parent


def _find(env, tail):
    if os.environ.get(env):
        return Path(os.environ[env])
    for p in REPO.rglob(tail.split('/')[-1]):
        if str(p).replace('\\', '/').endswith(tail):
            return p
    raise FileNotFoundError(tail)


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec); sys.modules[name] = m; spec.loader.exec_module(m); return m


pc = _load('pc_dag', _find('PLUGIN_PY', 'puente_chat/plugin.py'))
mf = _load('mf_dag', _find('MEM_PY', 'memoria_yaiwes/__init__.py'))


class FakeGraphiti:
    def __init__(self): self.saved = []
    def _endpoint(self): return 'local'
    def save(self, scope, key, data): self.saved.append((scope, key, data)); return {'status': 'SAVED'}
    def search(self, scope, q, k=5): return []


class FakeMem:
    def __init__(self):
        self.rows = {}; self.components = {'graphiti': FakeGraphiti()}
    def save(self, scope, key, data): self.rows[(scope, key)] = data; return {'status': 'SAVED'}
    def search(self, scope, q, k=10):
        return {'sqlite': [{'data': v} for (s, _), v in self.rows.items() if s == scope]}


FILES = {}
MEM = FakeMem()
pc._memoria = lambda: (MEM, lambda dueno, sub: dueno + ':' + sub)
pc._archivo_memoria = lambda sesion, nombre: FILES.get(nombre)
pc._gov_ancla_leer = lambda sesion, nombre: ('TEXTO CONSTITUCIONAL SECRETO ' + nombre, 'gov:test')


def _reset():
    pc._SNAP_ANC.clear(); FILES.clear(); MEM.rows.clear(); MEM.components['graphiti'].saved.clear(); pc._ANC_GRAPHITI_HECHAS.clear()


def test_n1_gobernanza_solo_sqlite():
    calls = []
    class S:
        def save(self, *a): calls.append('sqlite'); return {}
    class G:
        name = 'graph'
        def save(self, *a): calls.append('graph')
    class C:
        IN_SAVE = True
        def _endpoint(self): return 'x'
        def save(self, *a): calls.append('comp'); return {}
    f = mf.MemoryFacade.__new__(mf.MemoryFacade); f.sqlite = S(); f.graph = G(); f.components = {'qdrant': C(), 'graphiti': C()}
    r = f.save('chat-ui:gov:T1', 'gov-registro', {'a': 1}); assert calls == ['sqlite'] and r.get('only_sqlite')
    calls.clear(); f.save('chat-ui:snapanc:s:t', 'snapshot-anclados', {}); assert calls == ['sqlite']
    calls.clear(); f.save('chat-ui:chat:s', 'nota', {}); assert calls == ['sqlite', 'graph', 'comp', 'comp']


def test_n5_rehidrata_tras_reinicio():
    _reset(); FILES['a.md'] = 'contenido original A'
    r1 = pc.resolver_anclados('s1', ['archivo:a.md'], 't1', 'pregunta')
    sha1 = r1['snapshot'][0]['sha256']
    pc._SNAP_ANC.clear()  # reinicio: se pierde la RAM, queda SQLite
    r2 = pc.resolver_anclados('s1', ['archivo:a.md'], 't1', 'otra pregunta')
    assert r2.get('rehidratado') and r2['snapshot'][0]['sha256'] == sha1
    assert 'contenido original A' in r2['texto'] and 'contenido no copiado' not in r2['texto']


def test_n5_fuente_cambiada_y_no_leible():
    _reset(); FILES['a.md'] = 'v1'
    pc.resolver_anclados('s1', ['archivo:a.md'], 't1', ''); pc._SNAP_ANC.clear()
    FILES['a.md'] = 'v2 cambiado'
    r = pc.resolver_anclados('s1', ['archivo:a.md'], 't1', '')
    assert r.get('gap') == 'SOURCE_CHANGED_DURING_TASK' and 'SOURCE_CHANGED_DURING_TASK' in r['texto'], r.get('gap')
    pc._SNAP_ANC.clear(); FILES.pop('a.md')
    r = pc.resolver_anclados('s1', ['archivo:a.md'], 't1', '')
    assert r.get('gap') == 'SOURCE_REHYDRATE_FAILED', r.get('gap')


def test_n6_anclas_a_graphiti_sin_constitucion():
    _reset(); FILES['arq.md'] = 'La arquitectura usa puente_chat'
    pc.resolver_anclados('s1', ['archivo:arq.md', 'constitucion:extra'], 't1', '')
    g = MEM.components['graphiti'].saved
    assert len(g) == 1 and g[0][2]['source_id'] == 'arq.md' and g[0][2]['source_sha256'] and g[0][2]['source_snapshot_id'] and g[0][2]['task_id'] == 't1'
    assert 'anchors:s1' in g[0][0]
    assert not any('CONSTITUCIONAL' in json.dumps(x[2]) or 'constitucion' in x[2]['source_type'] for x in g)
    # no hay constitucion en ningun registro de grafo; se repite sin duplicar
    pc._SNAP_ANC.clear(); pc.resolver_anclados('s1', ['archivo:arq.md', 'constitucion:extra'], 't1', '')
    assert len(g) == 1


def test_n8_derivados_marcados_y_verificados():
    _reset(); FILES['arq.md'] = 'texto'
    r = pc.resolver_anclados('s1', ['archivo:arq.md'], 't1', '')
    sha = r['snapshot'][0]['sha256']
    G = MEM.components['graphiti']
    G.search = lambda sc, q, k=5: [
        {'text': 'hecho bueno', 'provenance': {'source_id': 'arq.md', 'source_sha256': sha}},
        {'text': 'hecho falso', 'provenance': {'source_id': 'arq.md', 'source_sha256': 'otro'}}]
    out = pc._derivados('s1', 'arquitectura', ['archivo:arq.md'], r)
    assert out.startswith('[DATOS DERIVADOS') and 'hecho bueno' in out and 'hecho falso' not in out and 'authority=derived' in out


def test_n2_paralelo_sin_contaminacion():
    loop = asyncio.new_event_loop(); threading.Thread(target=loop.run_forever, daemon=True).start()
    pc._paso_llm = lambda prov, modelo, msgs, tope=120, mt=1200: modelo
    vistos = {}
    async def graphiti_llm():  # igual que YaiwesGraphitiLLM: to_thread -> call
        await asyncio.sleep(0.05)
        return await asyncio.to_thread(pc._graphiti_llm_ficha, [], 10)
    def proyecto(nombre, prov, modelo):
        pc._cablear_graphiti(prov, modelo)
        for _ in range(20):
            vistos.setdefault(nombre, set()).add(asyncio.run_coroutine_threadsafe(graphiti_llm(), loop).result(10))
    ts = [threading.Thread(target=proyecto, args=('A', 'qwencloud', 'qwen-x')), threading.Thread(target=proyecto, args=('B', 'deepseek', 'deepseek-y'))]
    [t.start() for t in ts]; [t.join() for t in ts]
    assert vistos == {'A': {'qwen-x'}, 'B': {'deepseek-y'}}, vistos


if __name__ == '__main__':
    fallos = 0
    for n, f in list(globals().items()):
        if n.startswith('test_'):
            try: f(); print('PASS', n)
            except Exception as e: fallos += 1; print('FAIL', n, repr(e)[:300])
    sys.exit(1 if fallos else 0)
