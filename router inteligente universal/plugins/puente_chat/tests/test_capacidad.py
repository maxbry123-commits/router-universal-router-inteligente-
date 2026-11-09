"""Puerta de capacidades (determinista, sin LLM): los 10 casos del Director + filtrado de catalogo."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))  # repo root -> plugins.puente_chat.capacidad
from plugins.puente_chat.capacidad import capacidad_de, catalogo_para, CAP_NONE, CAP_READ, CAP_WRITE

from plugins.puente_chat.herramientas import TOOLS as FULL  # catalogo real con sus parametros

CASOS = [
    ("¿Qué modelo eres?", CAP_NONE),
    ("Escribe una función Python", CAP_NONE),
    ("Explícame este código", CAP_NONE),
    ("Revisa GitHub", CAP_READ),
    ("Busca este archivo en el repo", CAP_READ),
    ("Comprueba acceso a Hugging Face", CAP_READ),
    ("En GitHub crea prueba.txt", CAP_WRITE),
    ("Modifica este archivo del repositorio", CAP_WRITE),
    ("Escribe código para crear un archivo", CAP_NONE),
    ("No modifiques nada, solo revisa el repo", CAP_READ),
    # extras del spec
    ("Revisa este repo", CAP_READ),
    ("Busca un archivo en GitHub", CAP_READ),
    ("Comprueba Hugging Face", CAP_READ),
    ("No cambies nada; revisa el repositorio", CAP_READ),
    ("En GitHub escribe una función en archivo X", CAP_WRITE),
    ("¿Qué opinas de esta arquitectura?", CAP_NONE),
    ("Resume este texto", CAP_NONE),
    ("Corrige este fragmento que te pego aquí", CAP_NONE),
    ("Revisa este Space de Hugging Face", CAP_READ),
    ("Lee este archivo del repo", CAP_READ),
    ("Busca este modelo en Hugging Face", CAP_READ),
    ("Haz commit de este cambio en el repo", CAP_WRITE),
    ("Actualiza el Space de Hugging Face", CAP_WRITE),
    ("Sube este archivo al repo", CAP_WRITE),
    # regresiones de la auditoria: haz/hacer no autorizan mutacion por si solos
    ("Haz un resumen del repo", CAP_READ),
    ("Hacer una auditoría del repositorio", CAP_READ),
    ("En GitHub modifica X", CAP_WRITE),
    ("Haz un commit en el repo", CAP_WRITE),
    # auditoria 2: escribir/crear CONTENIDO sobre el repo no muta -> READ
    ("Escribe un resumen del repo", CAP_READ),
    ("Crea un informe del repositorio", CAP_READ),
    ("Escribe una auditoría del repo", CAP_READ),
    ("Genera un análisis de este repositorio", CAP_READ),
    # ...pero escribir/crear RECURSOS del sistema externo si muta -> WRITE
    ("En GitHub crea archivo X", CAP_WRITE),
    ("Escribe contenido en archivo X del repo", CAP_WRITE),
    ("Modifica archivo X del repositorio", CAP_WRITE),
    ("Haz commit", CAP_WRITE),
    ("Sube archivo X al repo", CAP_WRITE),
    # el Router es un sistema real del proyecto: corregirlo es WRITE; revisarlo es READ
    ("corrige el Router", CAP_WRITE),
    ("corregir el Router", CAP_WRITE),
    ("arregla el Router", CAP_WRITE),
    ("revisa el Router", CAP_READ),
    ("corrige el archivo del repo", CAP_WRITE),
    ("Corrige este fragmento que te pego aquí", CAP_NONE),
    ("corre el comando", CAP_NONE),
    ("Escribe un resumen del Router", CAP_READ),
]


def nombres(cat):
    return {t['function']['name'] for t in (cat or [])}


def main():
    errores = []
    for texto, esperado in CASOS:
        got = capacidad_de(texto)
        if got != esperado:
            errores.append('FAIL %r -> %s (esperaba %s)' % (texto, got, esperado))

    cat_none = catalogo_para(CAP_NONE, FULL)
    if cat_none is not None:
        errores.append('FAIL CAP_NONE catalogo: %r (esperaba None)' % (cat_none,))

    cat_read = nombres(catalogo_para(CAP_READ, FULL))
    if cat_read & {'github_escribir', 'hf_escribir'}:
        errores.append('FAIL CAP_READ muestra tools de escritura: %s' % cat_read)
    for debe in ('github_leer', 'github_api', 'hf_leer', 'hf_api', 'hf_almacenamiento'):
        if debe not in cat_read:
            errores.append('FAIL CAP_READ falta %s en catalogo' % debe)

    cat_write = nombres(catalogo_para(CAP_WRITE, FULL))
    if cat_write != nombres(FULL):
        errores.append('FAIL CAP_WRITE catalogo incompleto: %s' % cat_write)

    # CAP_READ no expone metodos de escritura ni en el esquema visible
    read_tools = {t['function']['name']: t['function'] for t in catalogo_para(CAP_READ, FULL)}
    for nom, param, permitido in (('github_api', 'metodo', {'GET', 'HEAD'}),
                                  ('hf_api', 'metodo', {'GET', 'HEAD'}),
                                  ('hf_almacenamiento', 'accion', {'listar', 'leer'})):
        f = read_tools[nom]
        props = (f.get('parameters') or {}).get('properties') or {}
        enu = set((props.get(param) or {}).get('enum') or [])
        if enu != permitido:
            errores.append('FAIL CAP_READ %s.%s enum=%s (esperaba %s)' % (nom, param, enu, permitido))
        for escr in ('cuerpo', 'contenido'):
            if escr in props:
                errores.append('FAIL CAP_READ %s expone parametro de escritura %s' % (nom, escr))
        if 'SOLO LECTURA' not in str(f.get('description')):
            errores.append('FAIL CAP_READ %s descripcion sin restriccion de lectura' % nom)

    if errores:
        print(chr(10).join(errores))
        return 1
    print('PASS %d casos de politica + filtrado de catalogo' % len(CASOS))
    return 0


def test_kwargs_gobernanza_llegan_a_pc_chat():
    # fichas_qwen._llamar_harness_1 debe pasar tarea_id/gobernanza/constitucion/nodo a pc._chat (auditoria de ChatGPT)
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
    import plugins.fichas_qwen.plugin as fq
    capt = []

    class _StubPC:
        FICHAS = {'qw-qwen-3-8-flash': ('n', 'u', 'm')}

        @staticmethod
        def _chat(p):
            capt.append(p)
            return {'choices': [{'message': {'content': 'ok'}}], 'constitucion': {}}

    fq._pc = lambda: _StubPC
    ficha = {'ficha': 'ficha1-modelos', 'dsl': {'timeouts': {'api_seconds': 60}, 'retry': {'max_attempts': 1}, 'tokens': {'max_output_tokens': 100}},
             'motor': {'limite_llamada_chars': 999999}, 'selector': [{'id': 'ficha-qwen38flash', 'tipo': 'texto'}]}
    opts = {'sesion': 's', 'aprobado': False, 'muta': False, 'cap_in': 'none', 'fid': 'ficha1-modelos', 'tarea_id': 't1',
            'gobernanza': {'x': 1}, 'constitucion': {'y': 2}, 'gov_ctx': {'z': 3}}
    fq._llamar_harness_1('ficha-qwen38flash', 'hola', ficha, {'id': 'N4'}, opts)
    p = capt[-1]
    for k in ('tarea_id', 'task_id', 'anclados', 'gobernanza', 'constitucion', 'constitucion_hash_esperado', 'gov_ctx', 'nodo_scope', 'nodo'):
        assert k in p, 'falta ' + k + ' en pc._chat'
    assert p['tools_habilitadas'] is False and p['cap_tools'] == 'none'
    print('PASS kwargs gobernanza llegan a pc._chat')


if __name__ == '__main__':
    test_kwargs_gobernanza_llegan_a_pc_chat()
    sys.exit(main())
