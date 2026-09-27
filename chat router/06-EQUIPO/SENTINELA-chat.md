# SENTINELA-CHAT — 2026-09-27T23:36Z
(LOOP común · versión: bd1b24f6007628c8 · modelo investigador: moonshotai/kimi-k3@NVIDIA_API_KEY_1)

OBJETIVO: Cerrar las tareas del Chat YAIWES por prioridad, con evidencia real y sin falsos verdes.
ESTADO LOOP: RESEARCH · NO_ENTREGADO
OBSERVED_SHA: b97210df5cd6

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
- tarea: T07
- estado: REVISE
- intento: 1
- fallo: NO_ENTREGADO
- siguiente: esperar; foco actual T05

INVESTIGACIÓN:
- fuentes consultadas: 0
- mínimo independiente objetivo: 3

CAUSA_RAIZ: Ruta con espacio sin escapar/comillas: `chat router/11-EVIDENCIA` no existe como path literal; pytest lo interpreta mal y no encuentra el directorio, por eso "no tests ran".

EVIDENCIA: Error literal de pytest: "file or directory not found: chat router/11-EVIDENCIA". Evidencia comunidad=[] (vacía). No hay tests ejecutados ni artefactos que respalden PASS.

NO_REGENERAR: No regenerar tests, ni renombrar masivamente, ni tocar código de sentinela-chat hasta confirmar la ruta real con `ls`.

REPARAR:
1. Ejecutar `ls` en la raíz del repo para localizar el directorio real (¿"chat router"? ¿"chat_router"? ¿"chat-router"?).
2. Invocar pytest con la ruta entre comillas: `pytest "chat router/11-EVIDENCIA" -v`.
3. Si el directorio no existe, crear `11-EVIDENCIA/` con los tests de cierre de tareas YAIWES.
4. Verificar que los tests recolectan: `pytest --collect-only`.

ACEPTACION: pytest corre con N tests collected, 0 errores de ruta, resultados guardados como evidencia real en 11-EVIDENCIA; solo entonces se evalúa PASS/FAIL por tarea.

CONTROL:
- PASS no lo decide la LLM.
- Cada ciclo relee HEAD; un informe con SHA viejo queda inválido.
- Si el mismo fallo se repite, escala a investigación antes de reintentar.
- El sentinela solo puede escribir informes/órdenes, no código del objetivo.
