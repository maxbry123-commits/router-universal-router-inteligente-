"""System prompt completo (fichas/system-prompt, sin editar) y formato de salida, listos para enviar. Rellena los huecos de plantilla como puente_chat._core_render."""
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
FICHA = RAIZ.parents[2] / 'fichas' / 'system-prompt'  # el system prompt vive solo en la ficha
VARS = {'[ROL_ESPECIALIZADO]': 'el ROL DEL NODO indicado más abajo', '[NIVEL / ESPECIALIDAD / PLATAFORMA]': 'senior / el que exija la tarea / la del repositorio',
        '[PROYECTO]': 'YAIWES', '[RUTA]': 'el repositorio y rutas indicados en la tarea', '[TAREA EXACTA]': 'la tarea del último mensaje del usuario',
        '[RESULTADO]': 'el resultado verificable que pide la tarea', '[EXISTENTE/AUTO-DETECT]': 'el existente (auto-detectar)',
        '[OBJETIVO_FINAL]': 'el objetivo de la tarea del usuario', '[CRITERIOS_DE_EXITO]': 'los criterios de la tarea y de la DEFINITION OF DONE',
        '[FORMATO_EXACTO]': 'el formato que pida la tarea (si no pide, el FORMATO DE SALIDA de la ficha)'}


def _leer(ruta):
    return (RAIZ / ruta).read_text(encoding='utf-8')


def formato():
    return _leer('prompts/FORMATO_SALIDA.md').strip()


def sistema():
    """core (con los huecos llenos) + bloque 3 (codigo) + bloque 4 (verificacion): el agente que ejecuta y verifica."""
    core = (FICHA / 'system_core.md').read_text(encoding='utf-8')
    for k, v in VARS.items():
        core = core.replace(k, v)
    core = core.replace('[MODO]\n(ver bloque_1.md)\n', '').replace('\nEmpieza ahora.\n', '\n')
    core = re.sub(r'\n=+ FIN INPUT BLOCK MAESTRO UNIFICADO =+\n', '\n', core)
    return '\n\n'.join([core.strip(), (FICHA / 'bloques/bloque_3.md').read_text(encoding='utf-8').strip(), (FICHA / 'bloques/bloque_4.md').read_text(encoding='utf-8').strip()])
