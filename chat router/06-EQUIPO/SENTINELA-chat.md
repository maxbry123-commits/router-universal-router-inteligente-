# SENTINELA-CHAT — 2026-09-28T00:05Z
(LOOP común · versión: a9dc69b2a1d74492 · modelo investigador: moonshotai/kimi-k3@NVIDIA_API_KEY_1)

OBJETIVO: Cerrar las tareas del Chat YAIWES por prioridad, con evidencia real y sin falsos verdes.
ESTADO LOOP: RESEARCH · TESTS_FALLAN
OBSERVED_SHA: 

PRIORIDADES:
1. T01 gobierno: código + tests reales + informe + commit en main
2. T02 colmena conectada al Router
3. T03 OmniRoute estable
4. T04 Claude Code ↔ NVIDIA
5. T05 funciones del chat
6. T06 Hermes/OpenClaw asistentes
7. T07 puerta de evidencia 12 goals
8. T08 motores base de fábrica

OBJETIVO ACTIVO:
- tarea: T01
- estado: REVISE
- intento: 1
- fallo: TESTS_FALLAN
- siguiente: esperar; foco actual T03A,T03B,T03C

INVESTIGACIÓN:
- fuentes consultadas: 5
- mínimo independiente objetivo: 3

CAUSA_RAIZ: `git merge --no-ff mirror/job-N` falla con exit 128 en el entorno de test (repo temporal sin `user.name`/`user.email` configurados, o la rama mirror/job-N no existe porque el commit previo también falló silenciosamente). No es bug de lógica de merge, es setup del fixture git.

EVIDENCIA: 2 tests fallan (test_diff_y_merge_selectivo, test_merge_bloqueado_por_sheriff), ambos en el mismo comando `git merge --no-ff`; 18 pasan. Exit 128 = error de git (identidad no configurada / ref inexistente), no conflicto de merge (que sería exit 1). Evidencia comunidad irrelevante (poetry/polars, sin relación).

NO_REGENERAR: No tocar la lógica de MirrorManager ni los otros 18 tests verdes; no "arreglar" mockeando subprocess (sería falso verde).

REPARAR: En el fixture/conftest del repo temporal de tests: `git config user.email "test@test"`, `git config user.name "Test"` (o `-c user.name=... -c user.email=...` en cada comando), y verificar que la rama `mirror/job-N` se crea con al menos 1 commit antes del merge. Capturar stderr del CalledProcessError para confirmar cuál de las dos causas es.

ACEPTACION: `pytest chat router/05-AGENTES/gobierno/tests/test_gobierno.py -v` → 20 passed, 0 failed, ejecutado en entorno limpio (CI) sin config git global del usuario.

CONTROL:
- PASS no lo decide la LLM.
- Cada ciclo relee HEAD; un informe con SHA viejo queda inválido.
- Si el mismo fallo se repite, escala a investigación antes de reintentar.
- El sentinela solo puede escribir informes/órdenes, no código del objetivo.
