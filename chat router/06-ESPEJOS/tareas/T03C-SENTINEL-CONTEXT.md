# T03C — CONTEXTO DEL SENTINELA

OBJETIVO: OmniRoute contrato C: auditoría externa y cierre
ALCANCE: chat router/08-OMNIROUTE
ARCHIVOS OBLIGATORIOS:
- DIAGNOSTICO.md
- README.md
- VALIDACION-EXTERNA.md

ACEPTACIÓN: grep -q 'VALIDACIÓN EXTERNA DE CIERRE' 'chat router/08-OMNIROUTE/DIAGNOSTICO.md' && grep -q 'NODE_VERSION_VERIFICADA' 'chat router/08-OMNIROUTE/DIAGNOSTICO.md' && grep -q 'OMNIROUTE_REF_VERIFICADA' 'chat router/08-OMNIROUTE/DIAGNOSTICO.md' && grep -q 'BETTER_SQLITE3_VERIFICADO' 'chat router/08-OMNIROUTE/DIAGNOSTICO.md' && grep -q 'HEALTH_ENDPOINT_VERIFICADO' 'chat router/08-OMNIROUTE/DIAGNOSTICO.md' && grep -q 'VEREDICTO_FINAL: PASS' 'chat router/08-OMNIROUTE/DIAGNOSTICO.md' && grep -q 'VALIDACION_T03C: PASS' 'chat router/08-OMNIROUTE/VALIDACION-EXTERNA.md' && test $(grep -Ec 'https?://' 'chat router/08-OMNIROUTE/DIAGNOSTICO.md') -ge 3

EVIDENCIA ACTUAL:
- causa: ARCHIVOS_INCOMPLETOS
- faltan: ['VALIDACION-EXTERNA.md']
- pytest/acceptance exit: 1
- scope_escape: False
- objective_drift: False

REGLAS:
- No regenerar archivos que ya pasen.
- No escribir fuera del ALCANCE.
- Si falta conocimiento, investigar antes de inventar.
- Corregir solo la causa demostrada y volver a ejecutar aceptación.

CHEQUEOS INDEPENDIENTES DEL OBJETIVO:
- grep -q '#9576' 'chat router/08-OMNIROUTE/VALIDACION-EXTERNA.md'
- grep -q '#9613' 'chat router/08-OMNIROUTE/VALIDACION-EXTERNA.md'

ANÁLISIS DEL INVESTIGADOR:
CAUSA_RAIZ: ARCHIVOS_INCOMPLETOS demostrada por evidencia determinista.
EVIDENCIA: faltan=['VALIDACION-EXTERNA.md'] pytest_exit=1.
NO_REGENERAR: todos los archivos existentes y no vacíos.
REPARAR: Conservar archivos existentes y completar solo los faltantes: ['VALIDACION-EXTERNA.md']. Después ejecutar la aceptación real.
ACEPTACION: OmniRoute contrato C: auditoría externa y cierre — ejecutar el comando contractual y exigir exit 0.
