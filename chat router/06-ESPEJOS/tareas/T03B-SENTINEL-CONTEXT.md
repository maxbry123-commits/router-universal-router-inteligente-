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
- faltan: []
- pytest/acceptance exit: 0
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
- GitHub:WiseLibs/better-sqlite3: 32-bit build succeeds, throws exceptions at runtime about integer length https://github.com/WiseLibs/better-sqlite3/issues/9

ANÁLISIS DEL INVESTIGADOR:
CAUSA_RAIZ: SCOPE_ESCAPE con pytest_exit=0 y faltan=[] indica que los 9 tests pasan pero el diff toca archivos fuera del alcance declarado de T03B (supervisor + SQLite), o se modificaron archivos protegidos/no listados en el contrato B.

EVIDENCIA: "9 passed in 2.12s" confirma corrección funcional; el veredicto determinista no reporta tests fallidos ni archivos faltantes, solo escape de scope → el problema es de límites del cambio, no de lógica.

GAPS: (1) No se especifica qué archivos constituyen el scope permitido de T03B ni cuáles se tocaron de más. (2) Sin lista de archivos modificados no puedo señalar el escape exacto. (3) Protocolo: falta criterio de si archivos de config/fixtures cuentan como scope.

NO_REGENERAR: No reescribir supervisor, capa SQLite ni los 9 tests — son correctos. No tocar lógica de negocio.

REPARAR: Revertir/retirar del diff todo archivo fuera del contrato B (supervisor + persistencia SQLite). Mover cambios extra a su tarea correspondiente o eliminarlos. Verificar con `git diff --name-only` contra la lista de scope antes de reenviar.

ACEPTACION: Diff limitado exclusivamente a archivos del contrato B, 9/9 tests en verde, veredicto sin SCOPE_ESCAPE.
