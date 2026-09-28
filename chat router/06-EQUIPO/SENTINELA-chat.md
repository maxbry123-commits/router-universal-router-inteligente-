# SENTINELA-CHAT — 2026-09-28T02:21Z
(LOOP común · versión: 9f25e8e246217db9 · modelo investigador: no requerido)

OBJETIVO: Cerrar las tareas del Chat YAIWES por prioridad, con evidencia real y sin falsos verdes.
ESTADO LOOP: ACTIVE · executor_active
OBSERVED_SHA: cbe5a1f02042

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
- tarea: T03
- estado: ACTIVE
- intento: 2
- fallo: TESTS_FALLAN
- siguiente: esperar; foco actual T05

CONTROL:
- PASS no lo decide la LLM.
- Cada ciclo relee HEAD; un informe con SHA viejo queda inválido.
- Si el mismo fallo se repite, escala a investigación antes de reintentar.
- El sentinela solo puede escribir informes/órdenes, no código del objetivo.
