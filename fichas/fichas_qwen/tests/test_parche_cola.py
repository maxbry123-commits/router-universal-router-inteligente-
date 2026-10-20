"""PARCHE_COLA offline: cada parte>=2 de la cola recibe la tarea original (incl. plan aprobado al final) y el libro de recibos reales.
Desde la raiz del repo:  PYTHONPATH=. python3 fichas/fichas_qwen/tests/test_parche_cola.py"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import fichas.fichas_qwen.plugin as fq  # noqa: E402

fq._ck_guardar = lambda *a, **k: None
FICHA = {'loop': {'max_partes_codigo': 12, 'max_segundos_codigo': 600}}
NODO = {'id': 'N4'}
PROMPT = 'OBJETIVO_X ' + ('relleno ' * 900) + 'PLAN APROBADO: publicar a.txt y b.txt'


def _corre(guion, prompt=PROMPT, out=None):
    pasos = list(guion); pedidos = []
    def fake(modelo, pedido, ficha, n, opts):
        k = len(pedidos); pedidos.append(pedido)
        a = pasos[min(k, len(pasos) - 1)]
        if a.startswith('tool'):
            opts['herr'].setdefault('N4', []).append({'herramienta': 'github_escribir', 'accion': 'PUT', 'objetivo': 'dir/f%d.txt' % k, 'ok': True, 'mutacion_real': True})
        return a
    fq._llamar_harness_3 = fake
    opts = {'herr': {'N4': []}, 'out': out if out is not None else {}, 'pid': 'p', 'fid': 'f', 'aprobado': True, 'muta': True, 'cap_in': 'write'}
    return fq._llamar_con_partes('m', prompt, FICHA, NODO, opts), pedidos, opts


def test_parte2_lleva_tarea_original_con_el_plan_al_final():
    _, ped, _ = _corre(['tool uno\nCONTINUAR_PARTE', 'tool dos\nTAREA_COMPLETA'])
    assert 'TAREA ORIGINAL' in ped[1] and 'OBJETIVO_X' in ped[1] and 'PLAN APROBADO: publicar a.txt y b.txt' in ped[1]
    assert len(ped[1]) < 8000  # acotado: la cola no crece sin limite


def test_parte2_lleva_libro_de_recibos_reales():
    _, ped, _ = _corre(['tool uno\nCONTINUAR_PARTE', 'tool dos\nCONTINUAR_PARTE', 'tool tres\nTAREA_COMPLETA'])
    assert '- github_escribir PUT dir/f0.txt -> OK (cambio real)' in ped[1]
    assert 'dir/f0.txt' in ped[2] and 'dir/f1.txt' in ped[2]  # acumulado


def test_el_libro_viaja_en_el_checkpoint_y_se_reanuda():
    out = {}
    try:
        _corre(['tool uno\nCONTINUAR_PARTE', 'CONTINUAR_PARTE', 'CONTINUAR_PARTE', 'CONTINUAR_PARTE'], out=out)
    except RuntimeError as e:
        assert str(e).startswith('GAP_LOOP_SIN_PROGRESO')
    ck = out['__loop__:N4']
    assert 'dir/f0.txt' in ck['libro']
    r, ped, _ = _corre(['tool fin\nTAREA_COMPLETA'], out=out)  # reanuda desde el checkpoint (otra "vida" del proceso)
    assert 'dir/f0.txt' in ped[0] and 'fin' in r


def test_parte1_no_cambia():
    _, ped, _ = _corre(['tool x\nTAREA_COMPLETA'])
    assert 'LIBRO DE HERRAMIENTAS' not in ped[0] and ped[0].startswith('OBJETIVO_X')


if __name__ == '__main__':
    n = 0
    for k, f in list(globals().items()):
        if k.startswith('test_'):
            f(); n += 1; print('PASS', k)
    print('COLA: %d/%d PASS' % (n, n))
