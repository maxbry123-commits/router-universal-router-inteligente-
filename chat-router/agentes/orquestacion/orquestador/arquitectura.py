"""Arquitectura interna de Chat BOTS en formato Archify (https://github.com/tt-a1i/archify, MIT, skill de diagramas).

El backend NO renderiza: devuelve el JSON `diagram_type: architecture` (schema_version 1) + el estado de cada pieza.
El agente de frontend lo dibuja en la ventana de informacion de la pestana Chat BOTS (renderer de Archify, por enlace).
Estados: hecho = en main y probado; en_curso = codigo en rama, falta revision x3 / Android; pendiente = sin codigo.
Actualizar ESTADO a mano en cada commit del backend (y ESTADO-BACKEND.md)."""
from __future__ import annotations

ARCHIFY = {'repo': 'https://github.com/tt-a1i/archify', 'commit': '88d1ae4498b6a1df610badf690c5406882622d15', 'licencia': 'MIT',
           'instalar': 'npx skills add tt-a1i/archify -g'}
# id, tipo archify, etiqueta, sub, fila, columna, estado
PIEZAS = [
    ('ui', 'frontend', 'Chat BOTS (pestana)', 'orquestador.js', 0, 0, 'en_curso'),
    ('info', 'frontend', 'Ventana arquitectura', 'Archify render', 1, 0, 'pendiente'),
    ('orq', 'backend', 'Plugin orquestador', '/plugins/orquestador/call', 0, 1, 'en_curso'),
    ('gob', 'security', 'Gobierno determinista', 'goal lock, recibos, watchdog, loop', 1, 1, 'en_curso'),
    ('mirror', 'external', 'Mirror por enlace', 'repos de agentes', 2, 1, 'en_curso'),
    ('sbx', 'cloud', 'Sandbox', 'HF Jobs > Vercel > bwrap', 3, 1, 'en_curso'),
    ('harness', 'backend', 'HARNESS puente_chat', 'chat_async + resultado', 0, 2, 'hecho'),
    ('ficha', 'backend', 'FICHA 4', 'ficha4-workflow-yaiwes', 0, 3, 'hecho'),
    ('modelo', 'external', 'MODELO', 'Qwen / DeepSeek / GLM', 1, 3, 'hecho'),
    ('mem', 'database', 'memoria_yaiwes', 'SQLite riu_chat.sqlite3', 1, 2, 'hecho'),
    ('graf', 'database', 'Graphiti / Graphify', 'replicas (Graphiti OFF)', 2, 2, 'hecho'),
    ('bucket', 'cloud', 'Bucket HF', 'yaiwes-memoria-storage', 3, 2, 'hecho'),
    ('repos', 'external', 'Repos de agentes', 'openclaw, hermes-agent, Wordflow', 2, 0, 'hecho'),
]
CONEXIONES = [('ui', 'orq', 'HTTP POST', 'emphasis'), ('orq', 'harness', 'HTTP', 'emphasis'), ('harness', 'ficha', 'HTTP', 'emphasis'),
              ('ficha', 'modelo', '', 'emphasis'), ('orq', 'gob', 'controla', 'security'), ('orq', 'mem', 'facade.save', 'default'),
              ('mem', 'graf', 'replica', 'dashed'), ('mem', 'bucket', 'sync 60 s', 'dashed'), ('orq', 'sbx', 'ejecutar', 'default'),
              ('mirror', 'repos', 'lee por llamada', 'dashed'), ('orq', 'mirror', '', 'default'), ('info', 'orq', 'arquitectura', 'dashed')]


def diagrama():
    return {
        'schema_version': 1, 'diagram_type': 'architecture',
        'meta': {'title': 'Chat BOTS: COMPONENTE -> HARNESS -> HTTP -> FICHA -> MODELO', 'output': 'chatbots-arquitectura.html'},
        'layout': {'mode': 'grid', 'cols': 4},
        'components': [{'id': i, 'type': t, 'label': l, 'sublabel': s, 'row': r, 'col': c, 'tag': e} for i, t, l, s, r, c, e in PIEZAS],
        'connections': [{'id': '%s-%s' % (a, b), 'from': a, 'to': b, **({'label': lab} if lab else {}), 'variant': v} for a, b, lab, v in CONEXIONES],
    }


def estado():
    return {'archify': ARCHIFY, 'diagrama': diagrama(), 'piezas': [{'id': i, 'nombre': l, 'estado': e} for i, _, l, _, _, _, e in PIEZAS]}
