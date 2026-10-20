"""PARCHE_AUD/AUD3 offline. Desde la raiz del repo:  PYTHONPATH=. python3 fichas/fichas_qwen/tests/test_parche_aud.py"""
import json, os, sys, tempfile, time
from pathlib import Path
RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ / 'fichas' / 'fichas_qwen' / 'modos'))
sys.path.insert(0, str(RAIZ / 'fichas' / 'fichas_qwen' / 'motor_json'))
os.environ['RIU_MOTOR_WS'] = tempfile.mkdtemp(prefix='aud_ws_')
import yaiwes_motor as ym  # noqa: E402
import motor_objetivo as mo  # noqa: E402


def _correr(vueltas, planner=None, estado0=None):
    it = iter(vueltas); st = {}
    def llamar(modo, prompt):
        if modo == 'auditor':
            return {'texto': '{"cumplido": false, "faltantes": []}', 'herramientas_ok': 1, 'mutaciones_ok': 1}
        if modo == 'planificador':
            return {'texto': planner or '{"tareas":["x"]}'}
        return next(it, _v('sigue', 'fin', herr=0, mut=0))
    obj = {'objetivo': 'O', 'modo_por_defecto': 'code', 'limites': {'pausa_entre_vueltas_s': 0}}
    if planner is None:
        obj['tareas'] = ['hacer X']
    res = mo.correr_objetivo(obj, llamar, lambda s: st.update(s), lambda *_: None, *( [estado0] if estado0 else []))
    return res, st


def _v(estado, nota='n', herr=1, mut=1, **extra):
    j = dict({'tarea': 'T1', 'estado': estado, 'resultado': 'r' + nota, 'evidencia': 'e' + nota, 'nuevas_tareas': [], 'nota_siguiente': nota}, **extra)
    return {'texto': json.dumps(j), 'herramientas_ok': herr, 'mutaciones_ok': mut}


def test_json_con_prosa_y_llaves():
    assert mo._json_de('antes {no es json} luego {"a": 1} y {otra}') == {'a': 1}
    assert mo._json_de('sin json') is None


def test_planner_no_puede_marcar_hecho():
    _, st = _correr([_v('sigue', 'a')] * 3, planner='{"tareas":[{"texto":"x","estado":"hecho","modo":"rapido"}]}')
    t = st['tareas'][0]
    assert t['estado'] != 'hecho' and t.get('modo') == 'code', t


def test_nuevas_tareas_string_no_se_parte():
    _, st = _correr([_v('sigue', 'a', nuevas_tareas='abc')] + [_v('sigue', 'b')] * 2)
    assert len(st['tareas']) == 1, st['tareas']


def test_lectura_con_avance_no_es_fallo():
    _, st = _correr([_v('sigue', 'l%d' % i, herr=3, mut=0) for i in range(5)])
    assert st['tareas'][0].get('continuaciones') == 5, st['tareas'][0]  # las 5 lecturas avanzaron; el relleno sin herramientas es el unico fallo


def test_needs_input_bloquea_sin_gastar_intentos():
    _, st = _correr([_v('needs_input', 'falta', herr=0, mut=0)])
    t = st['tareas'][0]
    assert t['estado'] == 'bloqueada' and t['intentos'] == 0 and t.get('falta'), t


def test_receipt_ids_string_es_falso():
    assert mo._recibos_falsos('receipt-inventado') == ['receipt-inventado']


def test_plan_sin_nombre_no_colisiona():
    p1 = [{'id': 'a', 'op': 'create_directory', 'path': 'd1'}]
    p2 = [{'id': 'a', 'op': 'create_directory', 'path': 'd2'}]
    assert ym.ejecutar(p1, 'wsn')['ok'] and ym.ejecutar(p2, 'wsn')['ok']


def test_meta_no_objeto_da_error_limpio():
    r = ym.ejecutar({'meta': 'x', 'ops': []}, 'wsm')
    assert not r['ok'] and 'GAP_META_TIPO' in json.dumps(r), r


def test_checkpoint_corrupto_no_invalida_otros():
    r = ym.ejecutar({'meta': {'name': 'buen'}, 'ops': [{'id': 'a', 'op': 'create_directory', 'path': 'q'}]}, 'wsc1')
    rid = r['receipts'][0]['receipt_id']
    bad = Path(os.environ['RIU_MOTOR_WS'], 'wsc0', '.receipts'); bad.mkdir(parents=True)
    (bad / 'roto.json').write_text('{no json', encoding='utf-8')
    (bad / 'lista.json').write_text('[1,2]', encoding='utf-8')
    ym._RECIBOS.clear()
    assert ym.recibo_existe(rid)


def test_receipts_mayusculas_reservado():
    r = ym.ejecutar({'meta': {'name': 'mm'}, 'ops': [{'id': 'a', 'op': 'create_directory', 'path': '.RECEIPTS'}]}, 'wsu')
    assert not r['ok'] and 'GAP_RUTA_RESERVADA' in json.dumps(r), r


def test_reanudar_no_cuenta_la_pausa():
    est = {'tareas': [{'id': 'T1', 'texto': 'x', 'estado': 'pendiente', 'intentos': 0, 'modo': 'code'}], 'vuelta': 2, 'resumen': [],
           't0': time.time() - 5 * 3600, 't_activo': 60, 'sin_progreso': 0}
    res, _ = _correr([_v('hecho', 'fin')], estado0=est)
    assert res['estado'] != 'LIMITE', res


if __name__ == '__main__':
    n = 0
    for k, f in list(globals().items()):
        if k.startswith('test_') and k != 'test_libro_sin_saltos_de_linea':
            f(); n += 1; print('PASS', k)
    print('AUD %d/%d' % (n, n))
