# Pruebas REALES de memoria_yaiwes: Store SQLite temporal (no stubs de memoria). Sin red, sin pytest: python test_memoria_real.py
import os
import sys
import tempfile
import types
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
for p in (REPO / 'router inteligente universal', REPO / 'chat router' / '04-MEMORIA'):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from integration.chat_mvp.store import Store  # noqa: E402
from memoria_yaiwes import QdrantLocalAdapter, build_memory  # noqa: E402


def _scope(owner, name):  # igual que puente_chat._scope_for
    return (name if name.startswith(owner + ':') else owner + ':' + name)[:80]


class _Obj:
    def __init__(self, **kw):
        self.__dict__.update(kw)


def _fake_qdrant(fail_upsert=False):
    mod = types.ModuleType('qdrant_client')
    models = types.SimpleNamespace(
        VectorParams=lambda size, distance: _Obj(size=size, distance=distance),
        Distance=types.SimpleNamespace(COSINE='cosine'),
        PointStruct=lambda id, vector, payload: _Obj(id=id, vector=vector, payload=payload),
        MatchValue=lambda value: _Obj(value=value),
        FieldCondition=lambda key, match: _Obj(key=key, match=match),
        Filter=lambda must: _Obj(must=must))
    almacen = {}

    class Client:
        def __init__(self, path):
            self.pts = almacen.setdefault(path, {})
            self.cols = almacen.setdefault(path + '#cols', set())

        def collection_exists(self, name):
            return name in self.cols

        def create_collection(self, collection_name, vectors_config):
            self.cols.add(collection_name)

        def upsert(self, collection_name, points):
            if fail_upsert:
                raise RuntimeError('disco lleno')
            for p in points:
                self.pts[p.id] = p

        def count(self, collection_name, exact=True):
            return _Obj(count=len(self.pts))

        def query_points(self, collection_name, query, query_filter, limit, with_payload):
            sc = query_filter.must[0].match.value
            fil = [p for p in self.pts.values() if p.payload['scope'] == sc]
            pts = sorted(((sum(a * b for a, b in zip(query, p.vector)), p) for p in fil), key=lambda x: -x[0])[:limit]
            return _Obj(points=[_Obj(payload=p.payload, score=s) for s, p in pts])
    mod.QdrantClient = Client
    mod.models = models
    return mod, almacen


class _Entorno:
    # aisla variables de entorno y el modulo qdrant_client por prueba
    def __init__(self, qdrant=None, **env):
        self.qdrant, self.env = qdrant, env

    def __enter__(self):
        self.tmp = tempfile.mkdtemp()
        self.prev = {k: os.environ.get(k) for k in ('RIU_QDRANT_LOCAL', 'RIU_QDRANT_PATH')}
        self.prev_mod = sys.modules.get('qdrant_client', '__nada__')
        os.environ['RIU_QDRANT_PATH'] = str(Path(self.tmp) / 'q')
        for k, v in self.env.items():
            os.environ[k] = v
        sys.modules['qdrant_client'] = self.qdrant  # None => ImportError (cliente no instalado)
        return Path(self.tmp)

    def __exit__(self, *a):
        for k, v in self.prev.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        if self.prev_mod == '__nada__':
            sys.modules.pop('qdrant_client', None)
        else:
            sys.modules['qdrant_client'] = self.prev_mod


def test_01_save_search_load_exacto():
    with _Entorno(None) as tmp:
        mem = build_memory(Store(tmp))
        dato = {'pregunta': 'hola', 'respuesta': 'mundo', 'n': [1, 2, {'x': 'ñ'}]}
        r = mem.save('agente', 'turno-1', dato)
        assert r['status'] == 'SAVED' and r['adapter'] == 'sqlite'
        assert mem.load('agente', 'turno-1')[0]['data'] == dato
        s = mem.search('agente', '', 10)
        assert any(f['data'] == dato for f in s['sqlite'])
        assert mem.search('agente', 'turno-1', 10)['graph']


def test_02_reinicio_recrea_fachada_sobre_el_mismo_sqlite():
    with _Entorno(None) as tmp:
        st = Store(tmp)
        m1 = build_memory(st)
        m1.save('s', 'k', {'v': 1})
        st.close()
        del m1
        m2 = build_memory(Store(tmp))
        assert m2.load('s', 'k')[0]['data'] == {'v': 1}
        assert any(f['data'] == {'v': 1} for f in m2.search('s', '', 5)['sqlite'])


def test_03_tipos_que_usa_puente_chat_sobreviven_al_reinicio():
    casos = {
        _scope('chat-ui', 'chat:s1'): [('turno-1', {'pregunta': 'p', 'respuesta': 'r'}), ('checkpoint', {'mensajes': [{'role': 'user', 'content': 'x'}]})],
        _scope('chat-ui', 'snapanc:s1:T1'): [('snapshot-anclados', {'ids': ['archivo:a.md'], 'hashes': ['abc']})],
        _scope('chat-ui', 'gov:T1'): [('gov-registro', {'task_id': 'T1', 'entrada': {'overlay': {'texto': 'REGLA'}, 'nombres': []}, 'hash': 'H'})],
    }
    with _Entorno(None) as tmp:
        st = Store(tmp)
        m1 = build_memory(st)
        for sc, regs in casos.items():
            for k, d in regs:
                assert m1.save(sc, k, d)['status'] == 'SAVED'
        st.close()
        m2 = build_memory(Store(tmp))
        for sc, regs in casos.items():
            for k, d in regs:
                assert m2.load(sc, k)[0]['data'] == d, (sc, k)
                assert any(f['data'] == d for f in m2.search(sc, '', 10)['sqlite']), (sc, k)


def test_04_fallo_del_grafo_no_pierde_el_dato_sqlite():
    with _Entorno(None) as tmp:
        mem = build_memory(Store(tmp))

        def boom(*a, **k):
            raise RuntimeError('grafo caido')
        mem.graph.save = boom
        r = mem.save('s', 'k', {'v': 9})
        assert r['status'] == 'SAVED' and r['adapter'] == 'sqlite'
        assert r['replica_gaps'] == [{'adapter': 'graph-sqlite-fallback', 'error': 'RuntimeError'}]
        assert mem.load('s', 'k')[0]['data'] == {'v': 9}


def test_05_qdrant_sin_cliente_es_gap_y_no_rompe():
    with _Entorno(None) as tmp:
        mem = build_memory(Store(tmp))
        h = mem.health()['adapters']['qdrant']
        assert h['runtime_status'] == 'GAP_CLIENT_NOT_INSTALLED' and h['semantic'] is False and h['truth'] == 'sqlite'
        r = mem.save('s', 'k', {'v': 1})
        assert r['status'] == 'SAVED' and 'qdrant' not in r['replicas']
        assert mem.rebuild_index()['status'] == 'GAP'


def test_06_qdrant_indexa_y_busca_sqlite_sigue_siendo_la_verdad():
    mod, _alm = _fake_qdrant()
    with _Entorno(mod) as tmp:
        mem = build_memory(Store(tmp))
        mem.save('s', 'plan', {'texto': 'revisar memory_runtime y storage'})
        mem.save('s', 'otro', {'texto': 'receta de cocina'})
        mem.save('z', 'ajeno', {'texto': 'memory_runtime en otro scope'})
        r = mem.save('s', 'k3', {'texto': 'nada'})
        assert r['replicas']['qdrant']['status'] == 'SAVED' and r['replicas']['qdrant']['mode'] == 'derived-index'
        res = mem.search('s', 'memory_runtime', 5)
        assert res['qdrant'][0]['key'] == 'plan' and all(x['scope'] == 's' for x in res['qdrant'])
        assert len(mem.load('s', 'plan')) == 1  # no se duplica desde el indice derivado
        h = mem.health()['adapters']['qdrant']
        assert h['runtime_status'] == 'CONNECTED' and h['records'] == 4 and h['embedding'] == 'LEXICAL_HASH_256' and h['semantic'] is False


def test_07_rebuild_reconstruye_el_indice_desde_sqlite():
    mod, alm = _fake_qdrant()
    with _Entorno(mod) as tmp:
        mem = build_memory(Store(tmp))
        mem.save('s', 'a', {'t': 'uno'})
        mem.save('s', 'b', {'t': 'dos'})
        alm[os.environ['RIU_QDRANT_PATH']].clear()  # se pierde el indice derivado
        assert mem.health()['adapters']['qdrant']['records'] == 0
        r = mem.rebuild_index()
        assert r['status'] == 'REBUILT' and r['indexed'] == 2 and r['total'] == 2
        assert mem.health()['adapters']['qdrant']['records'] == 2


def test_08_fallo_de_qdrant_en_runtime_no_invalida_el_guardado():
    mod, _alm = _fake_qdrant(fail_upsert=True)
    with _Entorno(mod) as tmp:
        mem = build_memory(Store(tmp))
        r = mem.save('s', 'k', {'v': 1})
        assert r['status'] == 'SAVED' and r['replicas']['qdrant']['status'] == 'GAP'
        assert mem.load('s', 'k')[0]['data'] == {'v': 1}
        r2 = mem.save('s', 'k2', {'v': 2})  # en enfriamiento: ni se intenta
        assert r2['status'] == 'SAVED' and 'qdrant' not in r2['replicas']


def test_09_qdrant_se_apaga_con_la_variable():
    mod, _alm = _fake_qdrant()
    with _Entorno(mod, RIU_QDRANT_LOCAL='0') as tmp:
        mem = build_memory(Store(tmp))
        assert mem.save('s', 'k', {'v': 1})['replicas'].get('qdrant') is None
        assert mem.health()['adapters']['qdrant']['runtime_status'] == 'GAP_DISABLED'


def test_10_embedding_determinista_y_normalizado():
    a = QdrantLocalAdapter.embed('Revisar memory_runtime y storage')
    assert a == QdrantLocalAdapter.embed('revisar MEMORY_RUNTIME y storage') and len(a) == 256
    assert abs(sum(v * v for v in a) - 1.0) < 1e-9
    assert not any(QdrantLocalAdapter.embed('   '))


if __name__ == '__main__':
    n = 0
    for nombre, f in sorted(globals().items()):
        if nombre.startswith('test_') and callable(f):
            f()
            n += 1
            print('OK', nombre)
    print('TOTAL', n, 'tests OK')
