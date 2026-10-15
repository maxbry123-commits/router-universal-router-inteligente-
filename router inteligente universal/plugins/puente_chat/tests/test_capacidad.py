"""Puerta de capacidades (determinista, sin LLM): los 10 casos del Director + filtrado de catalogo."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))  # repo root -> plugins.puente_chat.capacidad
from plugins.puente_chat.capacidad import capacidad_de, catalogo_para, CAP_NONE, CAP_READ, CAP_WRITE

T = {'github_escribir': {'function': {'name': 'github_escribir'}},
     'hf_escribir': {'function': {'name': 'hf_escribir'}},
     'github_leer': {'function': {'name': 'github_leer'}},
     'github_api': {'function': {'name': 'github_api'}},
     'hf_leer': {'function': {'name': 'hf_leer'}},
     'hf_api': {'function': {'name': 'hf_api'}},
     'hf_almacenamiento': {'function': {'name': 'hf_almacenamiento'}}}
FULL = list(T.values())

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
    if cat_write != set(T):
        errores.append('FAIL CAP_WRITE catalogo incompleto: %s' % cat_write)

    if errores:
        print(chr(10).join(errores))
        return 1
    print('PASS %d casos de politica + filtrado de catalogo' % len(CASOS))
    return 0


if __name__ == '__main__':
    sys.exit(main())
