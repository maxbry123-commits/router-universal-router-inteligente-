"""PARCHE_CICLO offline (INPUT BLOCK C10/C11/C12/C18): SIGUE->SIGUE->HECHO sin fallos; sin progreso = BLOQUEADO; corte de salida = continuacion, parcial no ejecutado.
Desde 'router inteligente universal/':  PYTHONPATH=. python3 plugins/fichas_qwen/tests/test_parche_ciclo.py"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import plugins.fichas_qwen.plugin as fq  # noqa: E402

fq._ck_guardar = lambda *a, **k: None
FICHA = {'loop': {'max_partes_codigo': 12, 'max_segundos_codigo': 600}}
NODO = {'id': 'N4'}


def _corre(guion):
    pasos = list(guion); llamadas = []; pedidos = []
    def fake(modelo, pedido, ficha, n, opts):
        pedidos.append(pedido); k = len(llamadas); llamadas.append(k)
        accion = pasos[k] if k < len(pasos) else pasos[-1]
        if accion == 'TRUNC':
            opts.setdefault('salidas_parciales', {})['N4'] = '{"ops":[{"id":"T1","op":"wri'
            raise RuntimeError('GAP_OUTPUT_TRUNCATED:N4')
        if 'tool' in accion:
            opts['herr'].setdefault('N4', []).append({'herramienta': 'github_escribir', 'ok': True, 'mutacion_real': True})
        return accion.replace('tool ', '')
    fq._llamar_harness_3 = fake
    opts = {'herr': {'N4': []}, 'out': {}, 'pid': 'p', 'fid': 'f', 'aprobado': True, 'muta': True, 'cap_in': 'write'}
    try:
        return fq._llamar_con_partes('m', 'haz X', FICHA, NODO, opts), None, pedidos, opts
    except RuntimeError as e:
        return None, str(e), pedidos, opts


def test_sigue_sigue_hecho_con_progreso():
    r, err, ped, _ = _corre(['tool parte1\nCONTINUAR_PARTE', 'tool parte2\nCONTINUAR_PARTE', 'tool fin\nTAREA_COMPLETA'])
    assert err is None and len(ped) == 3 and 'fin' in r


def test_sin_progreso_bloquea():
    r, err, ped, _ = _corre(['CONTINUAR_PARTE'])
    assert err and err.startswith('GAP_LOOP_SIN_PROGRESO') and len(ped) == 3


def test_progreso_intermitente_no_bloquea():
    r, err, ped, _ = _corre(['CONTINUAR_PARTE', 'CONTINUAR_PARTE', 'tool a\nCONTINUAR_PARTE', 'CONTINUAR_PARTE', 'tool b\nTAREA_COMPLETA'])
    assert err is None


def test_truncado_continua_y_el_parcial_es_dato():
    r, err, ped, o = _corre(['TRUNC', 'tool ok\nTAREA_COMPLETA'])
    assert err is None and len(ped) == 2
    assert 'SALIDA CORTADA' in ped[1] and 'NO ejecutado' in ped[1] and '"ops"' in ped[1]
    assert 'wri' not in (r or '')


def test_truncado_repetido_bloquea():
    r, err, ped, _ = _corre(['TRUNC'])
    assert err and err.startswith('GAP_LOOP_TRUNCADO_REPETIDO') and len(ped) == 4


def test_hecho_sin_mutacion_real_no_cierra():
    r, err, ped, _ = _corre(['listo\nTAREA_COMPLETA'])
    assert err and err.startswith('GAP_LOOP_SIN_EVIDENCIA_MUTADORA')


if __name__ == '__main__':
    n = 0
    for k, f in list(globals().items()):
        if k.startswith('test_'):
            f(); n += 1; print('PASS', k)
    print('CICLO: %d/%d PASS' % (n, n))
