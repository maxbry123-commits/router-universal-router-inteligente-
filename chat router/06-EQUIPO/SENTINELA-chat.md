# SENTINELA-CHAT — 2026-09-27T23:19Z
(LOOP común · versión: 2b406ed4fafbae72 · modelo investigador: moonshotai/kimi-k3@NVIDIA_API_KEY_1)

OBJETIVO: Cerrar las tareas del Chat YAIWES por prioridad, con evidencia real y sin falsos verdes.
ESTADO LOOP: REVISE · NO_ENTREGADO
OBSERVED_SHA: 891f06ad86fb

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
- tarea: T05
- estado: REVISE
- intento: 1
- fallo: NO_ENTREGADO
- siguiente: esperar; foco actual T04

INVESTIGACIÓN:
- fuentes consultadas: 0
- mínimo independiente objetivo: 3

CAUSA_RAIZ: Ruta con espacio "chat router/10-CHAT-FUNCIONES" pasada sin comillas a pytest → shell la parte en dos argumentos y ninguno existe; además el directorio probablemente no existe o está mal nombrado (¿"chat-router"?).

EVIDENCIA: Error literal "file or directory not found: chat router/10-CHAT-FUNCIONES" + "no tests ran in 0.00s". Evidencia comunidad=[] (vacía, sin verificación externa). No hay prueba de que existan tests en esa ruta.

NO_REGENERAR: No crear tests ficticios ni renombrar archivos sin confirmar el árbol real; no marcar PASS por "0 fallos" (0 tests ejecutados ≠ verde).

REPARAR: 1) Ejecutar `ls` / `find . -name "*CHAT-FUNCIONES*"` para localizar la ruta real. 2) Invocar pytest con comillas: `pytest "chat router/10-CHAT-FUNCIONES" -v` o corregir el nombre a `chat-router/...`. 3) Verificar que existan archivos `test_*.py` dentro. 4) Reejecutar y capturar salida completa.

ACEPTACION: PASS solo si pytest encuentra la ruta, ejecuta ≥1 test real con resultado OK, y la evidencia se adjunta literal (comando + salida). Estado actual: NO_ENTREGADO.

CONTROL:
- PASS no lo decide la LLM.
- Cada ciclo relee HEAD; un informe con SHA viejo queda inválido.
- Si el mismo fallo se repite, escala a investigación antes de reintentar.
- El sentinela solo puede escribir informes/órdenes, no código del objetivo.
