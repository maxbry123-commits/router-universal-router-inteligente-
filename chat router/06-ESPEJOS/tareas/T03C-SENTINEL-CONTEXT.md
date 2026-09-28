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
CAUSA_RAIZ: El contrato C exige el artefacto VALIDACION-EXTERNA.md (auditoría externa/cierre) y no existe en el entregable; además pytest_exit=1 indica suite roja, por lo que el sentinela marca SCOPE_ESCAPE (alcance declarado sin evidencia de cierre).

EVIDENCIA: Veredicto determinista REVISE con faltan=['VALIDACION-EXTERNA.md']; pytest exit 1; fuentes comunidad solo referencian repos upstream (OmniRoute, better-sqlite3) y un hilo SO de ANTLR irrelevante para el cierre — ninguna aporta validación externa.

GAPS: (1) No hay protocolo definido de quién/firma la auditoría externa ni formato mínimo del documento. (2) Falta criterio de qué tests deben pasar antes del cierre (umbral de pytest). (3) Sin evidencia de revisión por tercero (issue/PR externo, checklist firmado). (4) Desconocido si VALIDACION-EXTERNA.md requiere hash/commit de referencia.

NO_REGENERAR: No reescribir código de OmniRoute ni tests existentes; no tocar gramática ANTLR; no inventar una "auditoría" auto-firmada sin revisión real.

REPARAR: (1) Ejecutar pytest, corregir fallos hasta exit=0 y guardar log. (2) Crear VALIDACION-EXTERNA.md en raíz con: alcance auditado, commit/hash, resultado pytest (exit 0 + resumen), checklist de contrato C, hallazgos y firma/identidad del auditor externo con fecha. (3) Referenciar evidencia verificable (enlace a PR/CI o revisor distinto del autor).

ACEPTACION: pytest_exit=0; VALIDACION-EXTERNA.md presente, con auditor identificable ≠ autor, resultados reproducibles y cierre explícito del contrato C; sentinela sin SCOPE_ESCAPE.
