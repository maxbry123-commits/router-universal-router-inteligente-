# T03C — CONTEXTO DEL SENTINELA

OBJETIVO: OmniRoute contrato C: auditoría externa y cierre
ALCANCE: chat router/08-OMNIROUTE
ARCHIVOS OBLIGATORIOS:
- DIAGNOSTICO.md
- README.md
- VALIDACION-EXTERNA.md

ACEPTACIÓN: grep -q 'VALIDACIÓN EXTERNA DE CIERRE' 'chat router/08-OMNIROUTE/DIAGNOSTICO.md' && grep -q 'NODE_VERSION_VERIFICADA' 'chat router/08-OMNIROUTE/DIAGNOSTICO.md' && grep -q 'OMNIROUTE_REF_VERIFICADA' 'chat router/08-OMNIROUTE/DIAGNOSTICO.md' && grep -q 'BETTER_SQLITE3_VERIFICADO' 'chat router/08-OMNIROUTE/DIAGNOSTICO.md' && grep -q 'HEALTH_ENDPOINT_VERIFICADO' 'chat router/08-OMNIROUTE/DIAGNOSTICO.md' && grep -q 'VEREDICTO_FINAL: PASS' 'chat router/08-OMNIROUTE/DIAGNOSTICO.md' && grep -q 'VALIDACION_T03C: PASS' 'chat router/08-OMNIROUTE/VALIDACION-EXTERNA.md' && test $(grep -Ec 'https?://' 'chat router/08-OMNIROUTE/DIAGNOSTICO.md') -ge 3

EVIDENCIA ACTUAL:
- causa: SCOPE_ESCAPE
- faltan: ['VALIDACION-EXTERNA.md']
- pytest/acceptance exit: 1
- scope_escape: True
- objective_drift: False

REGLAS:
- No regenerar archivos que ya pasen.
- No escribir fuera del ALCANCE.
- Si falta conocimiento, investigar antes de inventar.
- Corregir solo la causa demostrada y volver a ejecutar aceptación.

CHEQUEOS INDEPENDIENTES DEL OBJETIVO:
- grep -q '#9576' 'chat router/08-OMNIROUTE/VALIDACION-EXTERNA.md'
- grep -q '#9613' 'chat router/08-OMNIROUTE/VALIDACION-EXTERNA.md'

FUENTES ENCONTRADAS:
- Repositorio oficial/upstream: diegosouzapw/OmniRoute https://github.com/diegosouzapw/OmniRoute
- Repositorio oficial/upstream: WiseLibs/better-sqlite3 https://github.com/WiseLibs/better-sqlite3
- StackOverflow: How to convert this code into Antlr Groovy Grammar v4? https://stackoverflow.com/questions/40997897/how-to-convert-this-code-into-antlr-groovy-grammar-v4

ANÁLISIS DEL INVESTIGADOR:
CAUSA_RAIZ: El contrato C exige el artefacto VALIDACION-EXTERNA.md (auditoría externa/cierre) y no fue generado; además pytest_exit=1 indica suite roja, por lo que el cierre no es auditable. El SCOPE_ESCAPE sugiere que se trabajó fuera del alcance (posiblemente código/gramática ajeno, cf. evidencia ANTLR irrelevante) en lugar de producir el documento de validación.

EVIDENCIA: Veredicto determinista REVISE con faltan=['VALIDACION-EXTERNA.md']; pytest_exit=1. Evidencia comunidad: repos OmniRoute y better-sqlite3 (stack real del proyecto) son pertinentes; el hilo StackOverflow de ANTLR/Groovy es ruido sin relación con el contrato C.

GAPS: (1) Protocolo no define plantilla obligatoria de VALIDACION-EXTERNA.md (secciones: alcance, hallazgos, resultado pytest, hash/commit, firmante externo). (2) No hay gate que bloquee cierre con pytest≠0. (3) Falta criterio de "auditoría externa": ¿quién/qué cuenta como externo? (4) Sin filtro de relevancia de evidencia comunitaria.

NO_REGENERAR: No reescribir código de OmniRoute ni migraciones better-sqlite3 ya verificadas; no descartar evidencia de los repos oficiales; no tocar nada relacionado con ANTLR.

REPARAR: (1) Corregir los tests fallidos hasta pytest_exit=0 y capturar salida. (2) Crear VALIDACION-EXTERNA.md en raíz con: commit SHA, resultado pytest completo, lista de archivos auditados, hallazgos, referencias a repos upstream, declaración de cierre del contrato C. (3) Confirmar que no hay cambios fuera del scope declarado.

ACEPTACION: pytest_exit=0; VALIDACION-EXTERNA.md presente con todas las secciones; veredicto determinista sin faltantes ni SCOPE_ESCAPE.
