"""Comprueba que el codigo que CORRE (carpeta plugins/ o router-bundle.tar.gz) trae todos los parches.
Uso:  python3 verificar_parches_vivos.py [ruta_plugins | router-bundle.tar.gz]   (sin ruta: la carpeta plugins/ de este repo)
Sale con codigo 1 si falta alguno: el Space corre codigo viejo -> regenerar bundle y reiniciar (solo con orden del Director)."""
import sys
import tarfile
from pathlib import Path

REQ = {  # marcador -> archivos (sufijo) donde debe aparecer
    'PARCHE_N4': ('fichas_qwen/plugin.py', 'puente_chat/plugin.py'),
    'PARCHE_N7': ('fichas_qwen/plugin.py', 'puente_chat/plugin.py'),
    'PARCHE_E2E': ('puente_chat/plugin.py', 'puente_chat/herramientas.py'),
    'PARCHE_CICLO': ('fichas_qwen/plugin.py',),
    'PARCHE_ORDENES': ('fichas_qwen/plugin.py', 'fichas_qwen/modos/motor_objetivo.py'),
    'PARCHE_MOTOR_ENV': ('puente_chat/plugin.py',),
    'PARCHE_COLA': ('fichas_qwen/plugin.py',),
    'PARCHE_T1': ('fichas_qwen/motor_json/yaiwes_motor.py', 'fichas_qwen/modos/motor_objetivo.py'),
    'PARCHE_500K': ('puente_chat/herramientas.py', 'puente_chat/plugin.py', 'fichas_qwen/plugin.py'),
    'PARCHE_AUD3': ('fichas_qwen/motor_json/yaiwes_motor.py', 'fichas_qwen/modos/motor_objetivo.py'),
    'PARCHE_GH_URL_ENC': ('puente_chat/herramientas.py',),
    'PARCHE_AUD4': ('fichas_qwen/modos/motor_objetivo.py', 'fichas_qwen/plugin.py', 'puente_chat/plugin.py'),
    'PARCHE_VERIF': ('puente_chat/herramientas.py', 'fichas_qwen/plugin.py'),
    'PARCHE_RICARDO': ('fichas_qwen/modos/motor_objetivo.py', 'puente_chat/plugin.py'),
    'PARCHE_OPUS': ('fichas_qwen/plugin.py',),
    'PARCHE_BACK': ('fichas_qwen/plugin.py', 'fichas_qwen/mvp.py', 'puente_chat/plugin.py'),
    'PARCHE_AUD': ('fichas_qwen/motor_json/yaiwes_motor.py', 'fichas_qwen/modos/motor_objetivo.py', 'fichas_qwen/plugin.py'),
}
_SUF = {s for v in REQ.values() for s in v}


def _leer(origen):
    """-> {sufijo: texto}"""
    out = {}
    p = Path(origen)
    if p.is_file():
        with tarfile.open(p, 'r:*') as tf:
            for m in tf:
                if m.isfile() and m.size < 5_000_000:
                    for s in _SUF:
                        if m.name.endswith('/plugins/' + s) or m.name.endswith('plugins/' + s) or m.name.endswith('/' + s):
                            out[s] = tf.extractfile(m).read().decode('utf-8', 'replace')
    else:
        for s in _SUF:
            # layout nuevo: fichas_qwen/ en fichas/, puente_chat/ en plugins/ (o raiz de plugins vieja)
            for f in (p / s, p / 'fichas' / s, p / 'plugins' / s, p / 'router' / s):
                if f.is_file():
                    out[s] = f.read_text(encoding='utf-8', errors='replace')
                    break
    return out


def verificar(origen):
    textos = _leer(origen)
    faltan = []
    for marca, archivos in REQ.items():
        for a in archivos:
            if marca not in textos.get(a, ''):
                faltan.append('%s en %s' % (marca, a))
    return faltan


if __name__ == '__main__':
    origen = sys.argv[1] if len(sys.argv) > 1 else str(Path(__file__).resolve().parents[3])  # raiz del repo
    f = verificar(origen)
    for x in f:
        print('FALTA', x)
    print('CODIGO VIVO COMPLETO' if not f else 'CODIGO VIEJO: %d parches ausentes' % len(f))
    sys.exit(1 if f else 0)
