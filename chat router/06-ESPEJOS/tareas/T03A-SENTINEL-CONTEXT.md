# T03A — CONTEXTO DEL SENTINELA

OBJETIVO: OmniRoute contrato A: runtime e instalación reproducible
ALCANCE: chat router/08-OMNIROUTE
ARCHIVOS OBLIGATORIOS:
- start_omniroute.sh
- DIAGNOSTICO-RUNTIME.md

ACEPTACIÓN: bash -n 'chat router/08-OMNIROUTE/start_omniroute.sh' && grep -q 'NODE_VERSION_DECISION' 'chat router/08-OMNIROUTE/DIAGNOSTICO-RUNTIME.md' && grep -q 'BETTER_SQLITE3_INSTALL' 'chat router/08-OMNIROUTE/DIAGNOSTICO-RUNTIME.md' && test $(grep -Ec 'https?://' 'chat router/08-OMNIROUTE/DIAGNOSTICO-RUNTIME.md') -ge 2

EVIDENCIA ACTUAL:
- causa: ARCHIVOS_INCOMPLETOS
- faltan: ['DIAGNOSTICO-RUNTIME.md']
- pytest/acceptance exit: 2
- scope_escape: False
- objective_drift: False

REGLAS:
- No regenerar archivos que ya pasen.
- No escribir fuera del ALCANCE.
- Si falta conocimiento, investigar antes de inventar.
- Corregir solo la causa demostrada y volver a ejecutar aceptación.

CHEQUEOS INDEPENDIENTES DEL OBJETIVO:
- grep -q 'v3.8.50' 'chat router/08-OMNIROUTE/start_omniroute.sh'
- grep -q 'better-sqlite3' 'chat router/08-OMNIROUTE/start_omniroute.sh'

ANÁLISIS DEL INVESTIGADOR:
CAUSA_RAIZ: ARCHIVOS_INCOMPLETOS demostrada por evidencia determinista.
EVIDENCIA: faltan=['DIAGNOSTICO-RUNTIME.md'] pytest_exit=2.
NO_REGENERAR: todos los archivos existentes y no vacíos.
REPARAR: Conservar archivos existentes y completar solo los faltantes: ['DIAGNOSTICO-RUNTIME.md']. Después ejecutar la aceptación real.
ACEPTACION: OmniRoute contrato A: runtime e instalación reproducible — ejecutar el comando contractual y exigir exit 0.
