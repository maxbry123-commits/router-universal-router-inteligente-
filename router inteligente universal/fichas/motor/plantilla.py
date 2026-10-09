"""La PLANTILLA XRAY-V2 del Director (plantilla/PLANTILLA_XRAY_V2.yaml) se carga en CADA llamada de CADA ficha.
El bloque <user_query mode="verbatim"> se rellena con la entrada del nodo; la plantilla original no se resume ni se toca."""
import re

MARCA = re.compile(r'(<user_query mode="verbatim">).*?(</user_query>)', re.S)
CLAVES = ('schema: yaiwes.node-executor/xray-v2', '=== BEGIN_INPUT_BLOCK ===', '<user_query mode="verbatim">')


def faltan(plantilla):
    return [c for c in CLAVES if c not in plantilla]


def bloque_entrada(nodo, task_id, texto, paso, rutas):
    nl = chr(10)
    return nl.join(['PASO ' + str(paso) + ' 📌 TAREA ' + str(task_id) + ' 📌', texto, '', 'ROL DEL NODO: ' + nodo['rol'], '', 'NODO ' + nodo['id'],
                    'repo: maxbry123-commits/router-universal-router-inteligente- | branch: main', '',
                    'ORIGEN: ' + ', '.join(nodo.get('read_paths') or ['(tarea)']), 'DESTINO: ' + ', '.join(rutas or ['(salida)'])])


def armar(plantilla, mejoras, bloque):
    nl = chr(10)
    return MARCA.sub(lambda m: m.group(1) + nl + bloque + nl + m.group(2), plantilla, count=1) + nl + mejoras
