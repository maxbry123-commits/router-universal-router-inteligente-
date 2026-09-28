# T03B — CONTEXTO DEL SENTINELA

OBJETIVO: OmniRoute contrato B: supervisor y SQLite
ALCANCE: chat router/08-OMNIROUTE
ARCHIVOS OBLIGATORIOS:
- supervisor_omniroute.py
- mantenimiento_db.py
- tests/test_supervisor.py
- VALIDACION-SUPERVISOR-DB.md

ACEPTACIÓN: python -m pytest 'chat router/08-OMNIROUTE/tests/test_supervisor.py' -q && grep -q 'VALIDACION_T03B: PASS' 'chat router/08-OMNIROUTE/VALIDACION-SUPERVISOR-DB.md'

EVIDENCIA ACTUAL:
- causa: SCOPE_ESCAPE
- faltan: ['VALIDACION-SUPERVISOR-DB.md']
- pytest/acceptance exit: 2
- scope_escape: True
- objective_drift: False

REGLAS:
- No regenerar archivos que ya pasen.
- No escribir fuera del ALCANCE.
- Si falta conocimiento, investigar antes de inventar.
- Corregir solo la causa demostrada y volver a ejecutar aceptación.

CHEQUEOS INDEPENDIENTES DEL OBJETIVO:
- grep -q 'wait_port_free' 'chat router/08-OMNIROUTE/supervisor_omniroute.py'
- grep -q 'BACKOFF' 'chat router/08-OMNIROUTE/supervisor_omniroute.py'
- grep -q 'mmap_size' 'chat router/08-OMNIROUTE/mantenimiento_db.py'
- grep -q 'VACUUM' 'chat router/08-OMNIROUTE/mantenimiento_db.py'

FUENTES ENCONTRADAS:
- Repositorio oficial/upstream: diegosouzapw/OmniRoute https://github.com/diegosouzapw/OmniRoute
- Repositorio oficial/upstream: WiseLibs/better-sqlite3 https://github.com/WiseLibs/better-sqlite3

ANÁLISIS DEL INVESTIGADOR:
sin respuesta del modelo; usar evidencia determinista
