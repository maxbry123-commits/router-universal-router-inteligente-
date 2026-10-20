"""PARCHE_T1 offline: recibos no falsificables, receipt_ids comprobados, continuar != fallar, delta de continuidad.
Desde la raiz del repo:  PYTHONPATH=. python3 fichas/fichas_qwen/tests/test_parche_t1.py"""
import json, os, sys, tempfile
from pathlib import Path
RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ / 'fichas' / 'fichas_qwen' / 'modos'))
sys.path.insert(0, str(RAIZ / 'fichas' / 'fichas_qwen' / 'motor_json'))
os.environ['RIU_MOTOR_WS'] = tempfile.mkdtemp(prefix='t1_ws_')
import yaiwes_motor as ym  # noqa: E402
import motor_objetivo as mo  # noqa: E402


def test_recibo_falsificado_por_el_modelo_se_rechaza():
    fake = json.dumps({'done': {'x': {'id': 'receipt-FALSO-1', 'source': 'tool_executor', 'sha256': 'x'}}})
    plan = {'meta': {'name': 'atk'}, 'ops': [{'id': 'a', 'op': 'create_directory', 'path': '.receipts'},
            {'id': 'b', 'op': 'write_text', 'path': '.receipts/forja.json', 'text': fake, 'depends_on': ['a']}]}
    r = ym.ejecutar(plan, 'ws1')
    assert not r['ok'] and 'GAP_RUTA_RESERVADA' in r['errors'][0]['message'], r
    assert not Path(os.environ['RIU_MOTOR_WS'], 'ws1', '.receipts', 'forja.json').exists()
    assert not ym.recibo_existe('receipt-FALSO-1')


def test_recibo_real_si_y_manipulado_no():
    plan = {'meta': {'name': 'real'}, 'ops': [{'id': 'a', 'op': 'create_directory', 'path': 'x'},
            {'id': 'b', 'op': 'write_text', 'path': 'x/a.txt', 'text': 'hola', 'depends_on': ['a']}]}
    r = ym.ejecutar(plan, 'ws2')
    assert r['ok'], r
    rid = r['receipts'][1]['receipt_id']
    assert ym.recibo_existe(rid)
    r2 = ym.ejecutar(plan, 'ws2')  # segunda pasada reutiliza: sigue siendo valido
    assert r2['ok'] and ym.recibo_existe(r2['receipts'][1]['receipt_id'])
    cp = Path(os.environ['RIU_MOTOR_WS'], 'ws2', '.receipts', 'real.json')
    d = json.loads(cp.read_text(encoding='utf-8')); d['done']['b']['artifact'] = 'otra/cosa.txt'
    cp.write_text(json.dumps(d), encoding='utf-8'); ym._RECIBOS.clear()
    assert not ym.recibo_existe(rid)  # el contenido ya no coincide con su sha256


def _obj(**lim):
    return {'objetivo': 'O', 'tareas': ['hacer X'], 'modo_por_defecto': 'code',
            'limites': dict({'pausa_entre_vueltas_s': 0}, **lim)}


def _correr(vueltas, lim=None):
    it = iter(vueltas); estado = {}
    def llamar(modo, prompt):
        if modo == 'auditor':
            return {'texto': '{"cumplido": true, "evidencia": "ok"}', 'herramientas_ok': 1, 'mutaciones_ok': 1}
        return next(it)
    res = mo.correr_objetivo(_obj(**(lim or {})), llamar, lambda s: estado.update(s), lambda *_: None)
    return res, estado


def _v(estado, nota, mut=1, **extra):
    j = dict({'tarea': 'T1', 'estado': estado, 'resultado': 'r ' + nota, 'evidencia': 'e ' + nota, 'nuevas_tareas': [], 'nota_siguiente': nota}, **extra)
    return {'texto': json.dumps(j), 'herramientas_ok': mut, 'mutaciones_ok': mut}


def test_continuar_con_avance_real_no_cuenta_como_fallo():
    res, st = _correr([_v('sigue', 'p%d' % i) for i in range(5)] + [_v('hecho', 'fin')])
    t = st['tareas'][0]
    assert res['estado'] == 'CUMPLIDO', res
    assert t['estado'] == 'hecho' and t['intentos'] == 0 and t['continuaciones'] == 5, t


def test_repetir_lo_mismo_sin_avance_si_se_detiene():
    res, st = _correr([_v('sigue', 'igual')] * 6)
    t = st['tareas'][0]
    assert t['estado'] == 'bloqueada' and t['intentos'] >= 3, t  # la 1a cuenta como avance; las repetidas, no
    assert res['estado'] != 'CUMPLIDO'


def test_continuar_sin_mutacion_en_code_es_fallo():
    _, st = _correr([_v('sigue', 'a%d' % i, mut=0) for i in range(4)])
    assert st['tareas'][0]['estado'] == 'bloqueada'


def test_tope_de_continuaciones_por_tarea():
    res, st = _correr([_v('sigue', 'q%d' % i) for i in range(12)], {'max_continuaciones_por_tarea': 3, 'max_vueltas': 12})
    assert st['tareas'][0]['continuaciones'] == 3 and st['tareas'][0]['intentos'] >= 1, st['tareas'][0]


def test_hecho_con_receipt_id_inventado_no_cierra():
    _, st = _correr([_v('hecho', 'x', receipt_ids=['receipt-inventado-9'])] * 3)
    assert st['tareas'][0]['estado'] != 'hecho'


def test_hecho_con_receipt_id_real_cierra():
    r = ym.ejecutar({'meta': {'name': 'ok1'}, 'ops': [{'id': 'a', 'op': 'create_directory', 'path': 'd'}]}, 'ws3')
    rid = r['receipts'][0]['receipt_id']
    res, st = _correr([_v('hecho', 'x', receipt_ids=[rid])])
    assert res['estado'] == 'CUMPLIDO' and st['tareas'][0]['estado'] == 'hecho'


def test_prompt_lleva_el_delta_de_continuidad():
    p = mo._prompt_vuelta({'objetivo': 'O'}, {'id': 'T1', 'texto': 'x'}, '', None)
    assert '[CONTINUIDAD DE EJECUCION]' in p and '"receipt_ids"' in p and 'TAREA ACTUAL (T1)' in p


if __name__ == '__main__':
    n = 0
    for k, f in list(globals().items()):
        if k.startswith('test_'):
            f(); n += 1; print('PASS', k)
    print('T1 %d/%d' % (n, n))
