"""System prompt completo (fichas/system-prompt, sin editar) y formato de salida, listos para enviar. Rellena los huecos de plantilla como puente_chat._core_render."""
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
FICHA = RAIZ.parents[3] / 'router-mvp' / 'fichas' / 'system-prompt'  # el system prompt vive solo en la ficha
VARS = {'[ROL_ESPECIALIZADO]': 'el ROL DEL NODO indicado más abajo', '[NIVEL / ESPECIALIDAD / PLATAFORMA]': 'senior / el que exija la tarea / la del repositorio',
        '[PROYECTO]': 'YAIWES', '[RUTA]': 'el repositorio y rutas indicados en la tarea', '[TAREA EXACTA]': 'la tarea del último mensaje del usuario',
        '[RESULTADO]': 'el resultado verificable que pide la tarea', '[EXISTENTE/AUTO-DETECT]': 'el existente (auto-detectar)',
        '[OBJETIVO_FINAL]': 'el objetivo de la tarea del usuario', '[CRITERIOS_DE_EXITO]': 'los criterios de la tarea y de la DEFINITION OF DONE',
        '[FORMATO_EXACTO]': 'el formato que pida la tarea (si no pide, el FORMATO DE SALIDA de la ficha)'}


def _leer(ruta):
    return (RAIZ / ruta).read_text(encoding='utf-8')


def formato():
    return _leer('prompts/FORMATO_SALIDA.md').strip()


def _core():
    """Core literal con los mismos marcadores resueltos que sistema()."""
    core = (FICHA / 'system_core.md').read_text(encoding='utf-8')
    for k, v in VARS.items():
        core = core.replace(k, v)
    core = core.replace('[MODO]\n(ver bloque_1.md)\n', '').replace('\nEmpieza ahora.\n', '\n')
    core = re.sub(r'\n=+ FIN INPUT BLOCK MAESTRO UNIFICADO =+\n', '\n', core)
    return core.strip()


def sistema():
    """Core + bloques completos 3 y 4. Contrato original, sin cambios."""
    return '\n\n'.join([_core(),
                          (FICHA / 'bloques/bloque_3.md').read_text(encoding='utf-8').strip(),
                          (FICHA / 'bloques/bloque_4.md').read_text(encoding='utf-8').strip()])


def sistema_groq():
    """Solo Qwen3.8/Groq de cuota baja: core original sin recortar.
    Los bloques originales 3 y 4 quedan intactos en disco y el Harness.
    Esta síntesis conserva reglas esenciales de programación y verificación,
    sin recortar ni modificar el input del usuario o su Constitución.
    """
    return '\n\n'.join([_core(),
        "[CONTRATO CODIGO] Respeta la estructura, rutas y archivos del repositorio, "
        "nunca inventes resultados de herramientas ni secretos; input del usuario "
        "verbatim, cambios mínimos, validación antes de cada commit y un ejecutor por tarea.",
        "[CONTRATO TESTING] Ejecuta o solicita las pruebas necesarias y comprueba sus "
        "resultados; separa PASS, GAP y BLOQUEO. Confirma commits y ejecución real "
        "antes de declarar completada una tarea; si una dependencia falla, deja "
        "checkpoint recuperable sin ocultar el error."]) 
