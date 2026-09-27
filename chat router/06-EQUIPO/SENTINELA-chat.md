# SENTINELA-CHAT — 2026-09-27T23:16Z
(LOOP común · versión: 1a36c3b6f8bb2dd9 · modelo investigador: moonshotai/kimi-k3@NVIDIA_API_KEY_1)

OBJETIVO: Cerrar las tareas del Chat YAIWES por prioridad, con evidencia real y sin falsos verdes.
ESTADO LOOP: RESEARCH · OBJECTIVE_DRIFT
OBSERVED_SHA: 24e3ad411b8f

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
- tarea: T04
- estado: REVISE
- intento: 3
- fallo: OBJECTIVE_DRIFT
- siguiente: espejo relanzado

INVESTIGACIÓN:
- fuentes consultadas: 4
- mínimo independiente objetivo: 3

CAUSA_RAIZ: El "13 passed in 0.04s" es un verde falso: 13 tests en 0.04s indica suite trivial/mockeada, no validación real de las tareas del Chat YAIWES. Además, la "evidencia comunidad" son issues #13 de repos ajenos (aider, pytest, claude-code, litellm) — coincidencia numérica literal, sin relación con sentinela-chat.

EVIDENCIA: Ningún issue citado pertenece al repo objetivo; ninguno menciona YAIWES ni sentinela-chat. El log de pytest no muestra qué se testeó ni cobertura de las tareas pendientes.

NO_REGENERAR: No re-ejecutar pytest esperando otro resultado; no buscar más issues "#13" en GitHub; no declarar PASS por conteo de tests.

REPARAR: 1) Listar las tareas abiertas reales del Chat YAIWES (issues del repo propio, no externos). 2) Mapear cada tarea a un test concreto con aserción verificable. 3) Ejecutar suite con -v y cobertura, exigiendo trazabilidad tarea→test→evidencia.

ACEPTACION: Cada tarea cerrada solo si existe test nombrado que la cubre, ejecutado en verde con salida verbose, y evidencia vinculada al repo sentinela-chat — no a repos de terceros.

CONTROL:
- PASS no lo decide la LLM.
- Cada ciclo relee HEAD; un informe con SHA viejo queda inválido.
- Si el mismo fallo se repite, escala a investigación antes de reintentar.
- El sentinela solo puede escribir informes/órdenes, no código del objetivo.
