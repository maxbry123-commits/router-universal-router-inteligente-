# T03C2 — CONTEXTO DEL SENTINELA

OBJETIVO: OmniRoute C2: documentación y gate final
ALCANCE: chat router/08-OMNIROUTE
ARCHIVOS OBLIGATORIOS:
- DIAGNOSTICO.md
- README.md

ACEPTACIÓN: grep -q 'VALIDACIÓN EXTERNA DE CIERRE' 'chat router/08-OMNIROUTE/DIAGNOSTICO.md' && grep -q 'NODE_VERSION_VERIFICADA' 'chat router/08-OMNIROUTE/DIAGNOSTICO.md' && grep -q 'OMNIROUTE_REF_VERIFICADA' 'chat router/08-OMNIROUTE/DIAGNOSTICO.md' && grep -q 'BETTER_SQLITE3_VERIFICADO' 'chat router/08-OMNIROUTE/DIAGNOSTICO.md' && grep -q 'HEALTH_ENDPOINT_VERIFICADO' 'chat router/08-OMNIROUTE/DIAGNOSTICO.md' && grep -q 'VEREDICTO_FINAL:' 'chat router/08-OMNIROUTE/DIAGNOSTICO.md' && test $(grep -Ec 'https?://' 'chat router/08-OMNIROUTE/DIAGNOSTICO.md') -ge 3 && ! grep -q 'pytest cache directory' 'chat router/08-OMNIROUTE/README.md' && grep -qi 'OmniRoute' 'chat router/08-OMNIROUTE/README.md'

EVIDENCIA ACTUAL:
- causa: OBJECTIVE_DRIFT
- faltan: []
- pytest/acceptance exit: 1
- scope_escape: False
- objective_drift: True

REGLAS:
- No regenerar archivos que ya pasen.
- No escribir fuera del ALCANCE.
- Si falta conocimiento, investigar antes de inventar.
- Corregir solo la causa demostrada y volver a ejecutar aceptación.

CHEQUEOS INDEPENDIENTES DEL OBJETIVO:
- grep -q 'ENV_VARS_VERIFICADAS' 'chat router/08-OMNIROUTE/DIAGNOSTICO.md'
- grep -q 'START_COMMAND_VERIFICADO' 'chat router/08-OMNIROUTE/DIAGNOSTICO.md'
- grep -q 'ISSUES_ABIERTOS_RELEVANTES' 'chat router/08-OMNIROUTE/DIAGNOSTICO.md'
- grep -q 'RIESGO_RESIDUAL' 'chat router/08-OMNIROUTE/DIAGNOSTICO.md'
- grep -q 'CAMBIOS_NECESARIOS' 'chat router/08-OMNIROUTE/DIAGNOSTICO.md'

FUENTES ENCONTRADAS:
- Repositorio oficial/upstream: diegosouzapw/OmniRoute https://github.com/diegosouzapw/OmniRoute
- Repositorio oficial/upstream: WiseLibs/better-sqlite3 https://github.com/WiseLibs/better-sqlite3

ANÁLISIS DEL INVESTIGADOR:
sin respuesta del modelo; usar evidencia determinista
