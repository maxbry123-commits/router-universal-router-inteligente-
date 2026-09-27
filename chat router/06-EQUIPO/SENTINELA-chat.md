# SENTINELA-CHAT — 2026-09-27T22:48Z
(LOOP común · versión: a3e6f375449cf9cf · modelo investigador: moonshotai/kimi-k3@NVIDIA_API_KEY_1)

OBJETIVO: Cerrar las tareas del Chat YAIWES por prioridad, con evidencia real y sin falsos verdes.
ESTADO LOOP: REVISE · NO_ENTREGADO
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
- tarea: T04
- estado: REVISE
- intento: 1
- fallo: NO_ENTREGADO
- siguiente: esperar; foco actual T03

INVESTIGACIÓN:
- fuentes consultadas: 0
- mínimo independiente objetivo: 3

CAUSA_RAIZ: Ruta con espacio sin comillas ("chat router/09-CLAUDE-CODE") y/o directorio inexistente; pytest no encuentra el target → "no tests ran". Además Evidencia comunidad=[] confirma que nada se ejecutó.

EVIDENCIA: Error literal "file or directory not found: chat router/09-CLAUDE-CODE"; sin comillas el shell lo parte en dos argumentos ("chat" y "router/09-CLAUDE-CODE"), ambos inexistentes.

NO_REGENERAR: No marcar PASS ni verde; no inventar tests ni resultados; no asumir que el directorio existe.

REPARAR: 1) Verificar existencia: `ls "chat router/09-CLAUDE-CODE"`. 2) Si existe, ejecutar con comillas: `pytest "chat router/09-CLAUDE-CODE" -v`. 3) Si no existe, localizar ruta real: `find . -type d -name "*09-CLAUDE*"`. 4) Confirmar que contiene archivos test_*.py. 5) Renombrar directorio sin espacios (chat_router) para evitar recurrencia.

ACEPTACION: `pytest "<ruta_real>" -v` ejecuta ≥1 test con resultado real (pass/fail) y evidencia de salida adjunta; solo entonces se evalúa cierre de tarea.

CONTROL:
- PASS no lo decide la LLM.
- Cada ciclo relee HEAD; un informe con SHA viejo queda inválido.
- Si el mismo fallo se repite, escala a investigación antes de reintentar.
- El sentinela solo puede escribir informes/órdenes, no código del objetivo.
