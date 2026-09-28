# T03C1 — CONTEXTO DEL SENTINELA

OBJETIVO: OmniRoute C1: investigación externa verificable
ALCANCE: chat router/08-OMNIROUTE
ARCHIVOS OBLIGATORIOS:
- VALIDACION-EXTERNA.md

ACEPTACIÓN: grep -q 'VALIDACION_T03C1: PASS' 'chat router/08-OMNIROUTE/VALIDACION-EXTERNA.md' && grep -q '#9576' 'chat router/08-OMNIROUTE/VALIDACION-EXTERNA.md' && grep -q '#9613' 'chat router/08-OMNIROUTE/VALIDACION-EXTERNA.md' && test $(grep -Ec 'https?://' 'chat router/08-OMNIROUTE/VALIDACION-EXTERNA.md') -ge 3

EVIDENCIA ACTUAL:
- causa: NO_ENTREGADO
- faltan: ['VALIDACION-EXTERNA.md']
- pytest/acceptance exit: 2
- scope_escape: False
- objective_drift: False

REGLAS:
- No regenerar archivos que ya pasen.
- No escribir fuera del ALCANCE.
- Si falta conocimiento, investigar antes de inventar.
- Corregir solo la causa demostrada y volver a ejecutar aceptación.

CHEQUEOS INDEPENDIENTES DEL OBJETIVO:
- grep -qi 'v3.8.50' 'chat router/08-OMNIROUTE/VALIDACION-EXTERNA.md'
- grep -Eqi 'package[.]json|engines' 'chat router/08-OMNIROUTE/VALIDACION-EXTERNA.md'
- grep -Eqi 'health|monitoring' 'chat router/08-OMNIROUTE/VALIDACION-EXTERNA.md'
- grep -Eqi 'better-sqlite3' 'chat router/08-OMNIROUTE/VALIDACION-EXTERNA.md'

ANÁLISIS DEL INVESTIGADOR:
CAUSA_RAIZ: NO_ENTREGADO demostrada por evidencia determinista.
EVIDENCIA: faltan=['VALIDACION-EXTERNA.md'] pytest_exit=2.
NO_REGENERAR: ninguno; no hay entrega válida en main.
REPARAR: Crear únicamente los archivos faltantes declarados por el contrato: ['VALIDACION-EXTERNA.md']. Seguir la tarea literal y ejecutar la aceptación real.
ACEPTACION: OmniRoute C1: investigación externa verificable — ejecutar el comando contractual y exigir exit 0.
