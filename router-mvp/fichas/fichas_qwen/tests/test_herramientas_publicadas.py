"""Cableado: toda herramienta que el Harness NOMBRA (muta/bloquea/despacha) debe estar PUBLICADA en un catalogo y tener ejecutor.
Desde la raiz del repo:  PYTHONPATH=. python3 fichas/fichas_qwen/tests/test_herramientas_publicadas.py"""
import re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import plugins.puente_chat.plugin as pcm  # noqa: E402
from plugins.puente_chat import capacidad as cap  # noqa: E402

SRC = Path(pcm.__file__).read_text(encoding='utf-8')


def _publicadas():
    h = pcm._herr()
    nom = {t['function']['name'] for t in h.TOOLS}
    return nom, {t['function']['name'] for t in pcm._MOTOR_TOOLS}, set(h.FUNCS)


def test_nombradas_en_es_mutacion_estan_publicadas():
    cuerpo = SRC[SRC.index('def _es_mutacion'):]
    cuerpo = cuerpo[:cuerpo.index('\ndef ', 10)]
    nombradas = set(re.findall(r"nom (?:==|in) \(?'([a-z_]+)'", cuerpo)) | set(re.findall(r"'([a-z_]+)'", ' '.join(re.findall(r"nom in \(([^)]*)\)", cuerpo))))
    h, m, f = _publicadas()
    libres = {'notas', 'pendientes', 'chat_bots', 'crear_agente'}  # dispatch propio de la app
    faltan = sorted(n for n in nombradas if n not in h | m | f | libres)
    assert not faltan, 'nombradas sin publicar ni ejecutor: %s' % faltan


def test_motor_tools_tienen_ejecutor():
    import json
    for t in pcm._MOTOR_TOOLS:
        n = t['function']['name']
        pcm._MOTOR_HAB.set(True)
        try:
            out = pcm._motor_ejecutar(n, {})
        finally:
            pcm._MOTOR_HAB.set(False)
        assert out is not None and 'tool desconocida' not in str(out), n


def test_escritoras_solo_en_write():
    from plugins.puente_chat.herramientas import TOOLS
    r = {t['function']['name'] for t in cap.catalogo_para('read', TOOLS)}
    assert 'github_escribir' not in r and 'hf_escribir' not in r


if __name__ == '__main__':
    n = 0
    for k, f in list(globals().items()):
        if k.startswith('test_'):
            f(); n += 1; print('PASS', k)
    print('CABLEADO: %d/%d PASS' % (n, n))
