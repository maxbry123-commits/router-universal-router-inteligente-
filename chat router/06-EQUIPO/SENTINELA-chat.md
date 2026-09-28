# SENTINELA-CHAT — 2026-09-28T00:31Z
(LOOP común · versión: 250e936e9d893c74 · modelo investigador: moonshotai/kimi-k3@NVIDIA_API_KEY_1)

OBJETIVO: Cerrar las tareas del Chat YAIWES por prioridad, con evidencia real y sin falsos verdes.
ESTADO LOOP: REVISE · NO_ENTREGADO
OBSERVED_SHA: 5caa5eeb1a85

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
- tarea: T08
- estado: REVISE
- intento: 1
- fallo: NO_ENTREGADO
- siguiente: esperar; foco actual T03A,T03B,T03C

INVESTIGACIÓN:
- fuentes consultadas: 0
- mínimo independiente objetivo: 3

CAUSA_RAIZ: Ruta con espacio "chat router/12-FABRICA-MOTORES" pasada sin comillas a pytest → el shell la parte en dos argumentos y ninguno existe; además el directorio probablemente no contiene tests (0 collected).

EVIDENCIA: Error literal "file or directory not found: chat router/12-FABRICA-MOTORES" + "no tests ran in 0.00s". Evidencia comunidad=[] (vacía, sin corroboración externa).

NO_REGENERAR: No crear tests ficticios ni marcar verde; no renombrar el directorio sin verificar referencias (imports, CI, scripts) que usen "chat router".

REPARAR: 1) Verificar existencia real: `ls "chat router/12-FABRICA-MOTORES"`. 2) Invocar con comillas: `pytest "chat router/12-FABRICA-MOTORES" -v`. 3) Si no hay tests, localizar el path correcto de tests del Chat YAIWES (`find . -name "test_*.py" -path "*sentinela*"`). 4) Considerar renombrar a `chat_router` y actualizar referencias.

ACEPTACION: `pytest "<path_correcto>"` ejecuta y reporta N tests collected con resultado real (pass/fail), evidencia pegada en la tarea; cero falsos verdes.

CONTROL:
- PASS no lo decide la LLM.
- Cada ciclo relee HEAD; un informe con SHA viejo queda inválido.
- Si el mismo fallo se repite, escala a investigación antes de reintentar.
- El sentinela solo puede escribir informes/órdenes, no código del objetivo.
