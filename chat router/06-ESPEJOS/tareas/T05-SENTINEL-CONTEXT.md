# T05 — CONTEXTO DEL SENTINELA

OBJETIVO: Funciones del chat: Action Registry, Council, rewind, compact, Archify, WORK
ALCANCE: chat router/10-CHAT-FUNCIONES
ARCHIVOS OBLIGATORIOS:
- action_registry.py
- council.py
- rewind.py
- compact.py
- archify_cmd.py
- work.py
- rutas.py
- tests/test_funciones.py
- README.md

ACEPTACIÓN: SIMULADO=1 python -m pytest 'chat router/10-CHAT-FUNCIONES' -q

EVIDENCIA ACTUAL:
- causa: NO_ENTREGADO
- faltan: ['action_registry.py', 'council.py', 'rewind.py', 'compact.py', 'archify_cmd.py', 'work.py', 'rutas.py', 'tests/test_funciones.py', 'README.md']
- pytest/acceptance exit: 4
- scope_escape: False
- objective_drift: False

REGLAS:
- No regenerar archivos que ya pasen.
- No escribir fuera del ALCANCE.
- Si falta conocimiento, investigar antes de inventar.
- Corregir solo la causa demostrada y volver a ejecutar aceptación.

CHEQUEOS INDEPENDIENTES DEL OBJETIVO:
- grep -q 'def ejecutar' 'chat router/10-CHAT-FUNCIONES/action_registry.py'
- grep -q 'ask_council' 'chat router/10-CHAT-FUNCIONES/council.py'
- grep -q 'asyncio' 'chat router/10-CHAT-FUNCIONES/council.py'
- grep -q 'def volver' 'chat router/10-CHAT-FUNCIONES/rewind.py'
- grep -Eq 'flowchart|graph' 'chat router/10-CHAT-FUNCIONES/archify_cmd.py'
- grep -q 'RUNNING' 'chat router/10-CHAT-FUNCIONES/work.py'
- grep -Fq '/acciones/{action_id}' 'chat router/10-CHAT-FUNCIONES/rutas.py'
- grep -Fq '/council' 'chat router/10-CHAT-FUNCIONES/rutas.py'
- grep -Fq '/work' 'chat router/10-CHAT-FUNCIONES/rutas.py'

FUENTES ENCONTRADAS:
- Repositorio oficial/upstream: fastapi/fastapi https://github.com/fastapi/fastapi
- Repositorio oficial/upstream: karpathy/llm-council https://github.com/karpathy/llm-council
- Repositorio oficial/upstream: pytest-dev/pytest https://github.com/pytest-dev/pytest

ANÁLISIS DEL INVESTIGADOR:
sin respuesta del modelo; usar evidencia determinista
