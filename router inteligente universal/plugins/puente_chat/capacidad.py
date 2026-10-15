"""Puerta de capacidades determinista (sin LLM): el software decide que puede ver/hacer el modelo.
CAP_NONE  -> sin catalogo de tools (tools/tool_choice ni se envian al proveedor)
CAP_READ  -> solo lectura: las tools puramente de escritura ni se presentan; una llamada mutante que se cuele la rechaza el Harness
CAP_WRITE -> lectura + escritura: solo cuando el input pidio servicio externo + orden explicita de modificar (o la ficha/nodo autoriza escribir)
"""
from __future__ import annotations
import re

CAP_NONE, CAP_READ, CAP_WRITE = 'none', 'read', 'write'

# intencion de servicio externo: GitHub, Hugging Face, repo/PR/commit/issue, tools/acceso. Palabras genericas como
# 'codigo', 'funcion', 'archivo', 'escribe' o 'crea' NO cuentan solas: pueden referirse a texto generado en la respuesta.
_EXTERNO = re.compile(r'(?i)github|hugging\s*face|huggingface|\bhf\b|\brepos?\b|repositorio|rama|\bbranch\b|\bcommits?\b|pull\s*request|\bpr\b|\bissues?\b|\bspaces?\b|datasets?|job\s*de\s*hf|tools?|herramientas?|acceso')

# orden de mutacion: crear/escribir/borrar/subir/commit/actualizar/eliminar/modificar/cambiar/...
_MUTA = re.compile(r'(crear?|escrib\w*|borr\w*|sub\w*|commit|actualiz\w*|elimin\w*|mov\w*|reemplaz\w*|modific\w*|cambi\w*|despleg\w*|reinici\w*|restaur\w*|implement\w*|arregl\w*|aplica\w*|apliqu\w*)', re.I)

# un 'no' antes del verbo lo niega: "no modifiques nada, solo revisa el repo" -> lectura
_NEG = re.compile(r'\bno\b[\wáéíóúñü ]{0,25}$', re.I)


def capacidad_de(texto: str | None) -> str:
    # el input actual decide: sin intencion externa -> NONE; externo + orden de mutar no negada -> WRITE; externo solo -> READ
    t = str(texto or '')
    if not _EXTERNO.search(t):
        return CAP_NONE
    for m in _MUTA.finditer(t):
        if not _NEG.search(t[:m.start()]):
            return CAP_WRITE
    return CAP_READ


# tools que SOLO escriben: en CAP_READ ni se muestran al modelo. github_api/hf_api/hf_almacenamiento se quedan porque
# sus operaciones de lectura (GET/listar/leer) son validas; sus mutaciones las sigue rechazando _es_mutacion/_bloqueo.
_PURO_ESCRIBE = ('github_escribir', 'hf_escribir')


_DESC_READ = {  # descripcion que ve el modelo en CAP_READ: los metodos mutantes ni se anuncian
    'github_api': 'Llama a la API de GitHub en modo SOLO LECTURA. metodo permitido: GET o HEAD.',
    'hf_api': 'Llama a la API de Hugging Face en modo SOLO LECTURA (la ruta empieza con /api/). metodo permitido: GET o HEAD.',
    'hf_almacenamiento': 'Almacenamiento permanente de Hugging Face en modo SOLO LECTURA. accion permitida: listar o leer.',
}


def catalogo_para(cap: str, tools: list | None) -> list | None:
    if cap == CAP_NONE:
        return None
    if cap == CAP_READ:
        import copy as _copy
        cat = []
        for t in (tools or []):
            f = t.get('function') or {}
            nom = str(f.get('name'))
            if nom in _PURO_ESCRIBE:
                continue  # tools puramente de escritura: ni se presentan
            t = _copy.deepcopy(t)
            f = t['function']
            if nom in _DESC_READ:
                f['description'] = _DESC_READ[nom]  # el modelo solo ve los metodos de lectura permitidos
                props = (f.get('parameters') or {}).get('properties') or {}
                if 'metodo' in props and isinstance(props['metodo'], dict):
                    props['metodo']['enum'] = ['GET', 'HEAD']  # la mutacion sigue rechazada por _es_mutacion/_bloqueo
                if 'accion' in props and isinstance(props['accion'], dict):
                    props['accion']['enum'] = ['listar', 'leer']
                props.pop('cuerpo', None)     # sin payload de escritura en lectura
                props.pop('contenido', None)
                req = (f.get('parameters') or {}).get('required') or []
                f.get('parameters', {})['required'] = [r for r in req if r in props]
            cat.append(t)
        return cat
    return list(tools or [])


def cap_min(a: str, b: str) -> str:
    # el nivel menor de los dos (none < read < write): una puerta nunca sube por encima de la otra
    orden = {CAP_NONE: 0, CAP_READ: 1, CAP_WRITE: 2}
    return a if orden.get(a, 0) <= orden.get(b, 0) else b
