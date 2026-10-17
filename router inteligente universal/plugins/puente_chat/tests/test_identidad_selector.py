# Test determinista (sin red, sin LLM): al cambiar de selector en el mismo chat, el modelo nuevo
# no debe recibir la identidad del anterior como si fuera suya (Nemotron repetia "Soy Qwen ...").
# Extrae _contexto y el armado del system prompt de plugin.py. Uso: python test_identidad_selector.py
import re
from pathlib import Path

SRC = (Path(__file__).resolve().parent.parent / 'plugin.py').read_text(encoding='utf-8')
QWEN, NEMO = 'ficha-qwen-3-8-max', 'nv-nemotron-super'
TURNOS = [{'data': {'modelo': QWEN, 'pregunta': 'quien eres?', 'respuesta': 'Soy Qwen 3.8 Max, de Alibaba.'}}]


class Mem:
    def __init__(self, filas):
        self.filas = filas

    def search(self, sc, q, n):
        return list(self.filas)


def _ns(filas=TURNOS):
    i = SRC.index('_OTRO_MODELO = ')
    j = SRC.index('def _guardar(')
    ns = {'DUENO': 'chat-ui', '_memoria': lambda: (Mem(filas), lambda d, s: d + ':' + s)}
    exec(SRC[i:j], ns)
    return ns


def _sistema(model, ctx):
    # simulacion del armado real de _chat: mismas lineas de plugin.py (bloque "if ctx:")
    i = SRC.index('    if ctx:  # MEMORIA EXACTA')
    j = SRC.index('    if res_anc is not None and not res_anc.get(\'gap\')')
    bloque = '\n'.join(l[4:] for l in SRC[i:j].splitlines())
    ns = {'ctx': ctx, 'model': model, 'sistema': 'S Modelo seleccionado: x',
          'FICHAS': {NEMO: ('NV Nemotron 3 Super', 'nvidia', 'nvidia/nemotron-3-super-120b-a12b', 90),
                     QWEN: ('Qwen 3.8 Max', 'qwencloud', 'qwen3.8-max', 60)},
          'RESPALDO': {}, '_OTRO_MODELO': _ns()['_OTRO_MODELO']}
    exec(bloque, ns)
    return ns['sistema']


def test_1_turno_de_otro_modelo_queda_marcado():
    ctx = _ns()['_contexto']('s1', 'hola', NEMO)
    assert 'Asistente: Soy Qwen' not in ctx, ctx  # antes del fix: llegaba como "Asistente: Soy Qwen..." sin marca
    assert 'OTRO modelo: ' + QWEN in ctx and 'NO es tu identidad' in ctx, ctx


def test_2_system_de_nemotron_fija_su_identidad_despues_del_historial():
    ctx = _ns()['_contexto']('s1', 'quien eres?', NEMO)
    s = _sistema(NEMO, ctx)
    assert 'IDENTIDAD: tu eres NV Nemotron 3 Super (nvidia/nemotron-3-super-120b-a12b)' in s, s
    assert s.index('IDENTIDAD:') > s.index('Soy Qwen'), s  # la identidad va despues del historial


def test_3_mismo_modelo_o_turno_viejo_sin_modelo_no_cambia_nada():
    ctx = _ns()['_contexto']('s1', 'hola', QWEN)
    assert 'Asistente: Soy Qwen' in ctx and 'OTRO modelo' not in ctx
    assert 'IDENTIDAD:' not in _sistema(QWEN, ctx)
    viejo = [{'data': {'pregunta': 'p', 'respuesta': 'r'}}]
    assert _ns(viejo)['_contexto']('s1', 'hola', NEMO) == 'Usuario: p\nAsistente: r'
    assert _ns()['_contexto']('s1', 'hola') == 'Usuario: quien eres?\nAsistente: Soy Qwen 3.8 Max, de Alibaba.'  # llamante sin modelo: igual que antes


def test_4_chat_pasa_el_modelo_actual_a_contexto():
    cuerpo = SRC[SRC.index('def _chat(p):'):SRC.index('def _estado(')]
    assert re.search(r'_contexto\(sesion, pregunta, model\)', cuerpo)


if __name__ == '__main__':
    n = 0
    for k, f in sorted(globals().items()):
        if k.startswith('test_') and callable(f):
            f()
            n += 1
            print('OK', k)
    print('TOTAL', n, 'tests OK')
