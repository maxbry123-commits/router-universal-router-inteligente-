# HANDOFF GLOBAL — router-universal-router-inteligente-
Actualizado: 2026-09-29 (segundo checkpoint ~16:30 Bogotá — sección «Checkpoint 2» abajo, que MANDA sobre el de las 11:20 si se contradicen; primer checkpoint ~11:20; antes, la versión de la mañana). Quien retome: lee esto, luego `CRAZY_WALL.json`, `ESTADO.json` y `BITACORA.jsonl` (misma carpeta). No inventes: si algo no está aquí, pregunta al Director.

**Todo lo del Router** (el Router, sus conexiones, claves, Hugging Face, Vercel y sus tareas T-00, T-01, T-03, T-10) vive SOLO en `router inteligente universal/HANDOFF-PROVISIONAL-ROUTER.md` y `router inteligente universal/CONECTAR-ROUTER.md`. Aquí no se repite el detalle, para no mezclar; PERO desde el 11:07 el Director ordena checkpoints progresivos también aquí, así que la sección «Checkpoint progresivo» de abajo trae el resumen y los punteros.

## Checkpoint progresivo 2026-09-29 (~11:20 Bogotá) — Router, chat como plugin y Plugin Host
Para quien llega sin contexto: el proyecto tiene UN Router de modelos de IA (un Job de Hugging Face); todo lo demás (el chat, los agentes, las pantallas) se conecta a él como un plugin. El Director ordenó (11:07) dejar el estado anotado por partes por si Anthropic se satura. Detalle completo, una sola nota: `Claude notas/CHECKPOINT-2026-09-29-1100-router-chat-plugins.md`. Estado técnico del Router: `router inteligente universal/HANDOFF-PROVISIONAL-ROUTER.md` (secciones 10 a 19). Bitácora: `BITACORA.jsonl` (B-0022 a B-0029). Rama de trabajo: `bloque1-cadena-chat` (todavía NO unida a main).
Marcas: ✅ VERIFICADO (ejecutado + probado + 4 pasadas de revisión + 3 rondas limpias seguidas) · 🟡 HECHO SIN PROBAR / probado a medias · 🔴 PENDIENTE · ⛔ BLOQUEADO. **Nada está ✅ todavía**: las rondas 1 y 2 de auditoría independiente salieron NO LIMPIAS (sin bloqueadores, con defectos reales ya corregidos en código).

### Órdenes del Director vigentes
- 10:55 (textual según el archivo de hechos): "Ok termina el router y activalo / El chat es solo un plugins más conectado al router" → autoriza relanzar el Job del Router tras terminarlo; el chat es UN plugin más, no el centro.
- 11:07 (paráfrasis; el texto literal no está en el repo): checkpoint progresivo (bitácora, estado JSON, handoff, Claude notas, Crazy Wall); no desviarse; terminar el Router primero (prioridad 1) con un agente auditándolo en paralelo; luego chat + agentes (prioridad 2): DSL DAG con loops, agente orquestador, Hermes y OpenClaw como asistente/sheriff/sentinela/supervisor/juez/guardián/investigador de contexto/manipulación de memoria y almacenamiento, harness de DeepSeek; generar un espejo (mirror) solo de Hermes+OpenClaw o de todo el equipo, y varias UI de chat una debajo de otra, todo separado, nada monolítico.
- 11:11 (paráfrasis): delegar varias tareas a varios agentes (Claude escribe el código, ellos hacen lo demás) para terminar lo antes posible.
- 05:18 (textual): 3 bucles de revisión + 4 pasadas por tarea terminada; sin eso no es ✅. 02:06 (textual): "El chat y los agentes de Hermes y open claw prioridad con Nvidia si está ocupado las primeras 3 Salta a la 4 o a groq" (hoy solo cubre el chat y a medias; Hermes/OpenClaw sin tocar).

### Estado por bloque
- 🟡 Prioridad 1, Bloque 1 (cadena de modelos del chat dentro del Router): hecho y probado en CI (corridas 36557644179, 36561019462, 36562078042 del flujo temporal; 183 pasan en la rama contra 153 en main con el mismo conjunto de 14 fallos previos; 42 pruebas de la cadena; mutaciones 27 de 28 detectadas; en vivo, la cadena Kimi K3 → GLM 5.3 → DeepSeek V4 → Qwen 3.8 (Groq) → Nemotron último funciona escalón por escalón). No es ✅.
- 🟡 Correcciones de la ronda 2 (9 puntos): subidas a la rama entre las 11:14 y las 11:18, SIN CI. [16:30] Superado: hubo también rondas 3 y 4 y todo está subido; ver «Checkpoint 2».
- 🔴 El Router VIVO (Job `6abb503a6b030d633f6a2dca`) no corre nada de esto; relanzarlo requiere: CI verde, Plugin Host mínimo, unir a main; y arreglar dos huecos del lanzador (no pasa `HF_TOKEN_1` ni `RIU_CHAT_ALLOW_PROVIDER_LIVE=1` al Job). [16:30 CORREGIDO: el Job SÍ pone `RIU_CHAT_ALLOW_PROVIDER_LIVE=1` (`router_job_persistent.py:74`); solo falta `HF_TOKEN_1`, y otro agente está activando el Router.]
- 🟡/🔴 Bloque 2, Plugin Host mínimo con el chat como primer plugin: EN CONSTRUCCIÓN por otro agente; sin código en la rama al 11:20, sin pruebas. [16:30 OBSOLETO: ya subido a la rama y probado en CI (🟡, no ✅).]
- 🔴 Bloque 3: registro de fichas, compilador ficha→flujo, agente operador, autodetección, gobernador de capacidad paralelo/cola, ZIP de subrouters montado APAGADO con interruptor, conectores plugin (HTTP, SSH, MCP, push), dataset Yaiwes y anclas del Control Plane.
- 🔴 Después del Router: chat + agentes (prioridad 2), IA local en la máquina de 32 GB, autoescalado, pantalla final (al último, con la skill de diseño que dará el Director).

### Tareas del Router que se mueven con esto (una línea cada una; detalle en el handoff del Router)
| # | Marca | Resumen |
|---|---|---|
| T-10 | 🟡 | Guía de conexión reescrita; `provider:"auto"` obligatorio; `RouterCliente` sin parche [16:30: ARREGLADO en la rama, commit `40924286`] |
| T-11 | 🔴 | IA local en 32 GB, después del Router |
| T-12 | 🟡 | Cadena del chat hecha y probada en CI en la rama; no en el Router vivo |
| T-13 | 🟡/🔴 | Claves NVIDIA 1→4 hechas para el chat; sin salto directo a Groq; Hermes/OpenClaw sin tocar |
| T-14 | 🔴 | Autoescalado: no existe |
| T-15 | 🟡/🔴 | Plugin Host en construcción por otro agente |
| T-16 | 🔴 | ZIP de subrouters/thinking: montar apagado con interruptor |
| T-17 / T-18 / T-19 | 🔴 | Cruce con Opus (parcial) / prueba del Router y equipo de 4 objetivos / aceleradores HF |
| T-20 | 🟡 | Lista de modelos disponibles + Nemotron último: hecho en la rama y probado en CI |
| T-21 / T-22 / T-23 / T-24 | 🔴 | Paralelo y cola / fichas / pantalla final / dataset y Control Plane |
| T-25 | — | No definida en ninguna fuente: no se inventó |

### Lo que decide el Director (detalle en la nota de checkpoint)
DeepSeek en hora pico (hoy se salta en `default`, `g2` y `minor`); Nemotron segundo en `minor`; OK a la reescritura de `g2`; salto directo a Groq; si una respuesta vacía debe pasar al siguiente modelo; plazo TOTAL de la cadena (hoy hasta ~210–450 s); OK al «tribunal» de plugins; borrar `.omniroute_proxy` y `.github/omniroute-relaunch.trigger`; rotar las 7 llaves Groq.

### Incidente y lección de hoy
El script local de mutaciones se interrumpió a las 10:55 y dejó una mutación en `model_pool.py` del árbol de trabajo local; se detectó por las pruebas locales antes de subir y se restauró (35/35); nada mutado llegó al repo. Lección: las mutaciones se corren en una COPIA o en CI, y las pruebas locales se corren ANTES de cada push.

### Estado de subida del código (HISTÓRICO de las 11:33; sustituido por la tabla de «Checkpoint 2»)
Estado de subida comprobado con `git fetch` a las 11:33 (Bogotá); rama `bloque1-cadena-chat` en el commit cb229a12. Un archivo cuenta como subido solo si el blob de la rama es igual a `git hash-object` del archivo local:
- `router inteligente universal/integration/chat_mvp/resilience.py` [cambio de la ronda 2]: local `c3043881` · rama `c3043881` → SUBIDO (blob igual)
- `router inteligente universal/integration/chat_mvp/model_pool.py` [cambio de la ronda 2]: local `34df8847` · rama `34df8847` → SUBIDO (blob igual)
- `router inteligente universal/integration/chat_mvp/router.py` [cambio de la ronda 2]: local `3b0445af` · rama `3b0445af` → SUBIDO (blob igual)
- `router inteligente universal/integration/chat_mvp/route_api.py`: local `83d2e677` · rama `83d2e677` → SUBIDO (blob igual)
- `router inteligente universal/integration/chat_mvp/providers.py`: local `bd96dd07` · rama `bd96dd07` → SUBIDO (blob igual)
- `router inteligente universal/tests/test_resilience.py` [cambio de la ronda 2]: local `26255aa3` · rama `26255aa3` → SUBIDO (blob igual)
- `router inteligente universal/tests/test_model_pool.py` [cambio de la ronda 2]: local `cc5b8fa1` · rama `cc5b8fa1` → SUBIDO (blob igual)
- `router inteligente universal/tests/test_chat_mvp_app.py`: local `fd64ad22` · rama `fd64ad22` → SUBIDO (blob igual)
Veredicto: las correcciones de la ronda 2 en resilience.py, model_pool.py y router.py están SUBIDAS a la rama. Siguen SIN CI (ninguna corrida las ha ejecutado).

## Checkpoint 2 — 2026-09-29 (~16:30 Bogotá) — MANDA sobre el de las 11:20 si se contradicen
Marcas: ✅ VERIFICADO (ejecutado + probado + 4 pasadas de revisión + 3 rondas limpias seguidas) · 🟡 HECHO SIN PROBAR / probado a medias · 🔴 PENDIENTE · ⛔ BLOQUEADO. **Nada está ✅.**
Detalle completo: `Claude notas/CHECKPOINT-2026-09-29-1100-router-chat-plugins.md` (sección 12) y `router inteligente universal/HANDOFF-PROVISIONAL-ROUTER.md` (sección 20). Bitácora: `BITACORA.jsonl` (B-0030 en adelante).

### A. Contexto y órdenes del Director
- Contexto: la ventana de Anthropic se agotó entre ~11:50 y ~15:20 (según el archivo de hechos); el Director reanudó a las 15:26 con «intenta terminar cerrar el router y hacer los de los agentes y el chat» (textual según el archivo de hechos). Orden del Director de las 16:14 (según el coordinador; el texto literal NO está en el repo): «terminar el Router ya; chat y agentes = cableado y workflow sin sobre-ingeniería; delegar a agentes, yo solo el código».
- Fuentes de esta actualización: la «ADENDA 15:50» del archivo de hechos (manda sobre la parte de las 11:15 si se contradicen), el mensaje del coordinador de las 16:2x y lo que verifiqué leyendo la rama con `git fetch` y `git show` a las 16:30 (Bogotá). Cada afirmación que dice «comprobado» la leí en el código o en el registro de commits; las cifras de CI vienen del archivo de hechos (no consulté las corridas).
- Rondas 3 y 4 de auditoría independiente: AMBAS NO LIMPIAS, sin bloqueadores (ronda 3: 3 ALTO de documentación/activación, 5 MEDIO y 8 BAJO). Nada es ✅: faltan 3 rondas limpias seguidas y las 4 pasadas por tarea (regla de las 05:18).

### B. Estado de subida de la rama `bloque1-cadena-chat` (sustituye al de las 11:33)
Estado de subida comprobado con `git fetch` a las 16:30 (Bogotá); rama `bloque1-cadena-chat` en el commit `69b2d6ec` (último commit de la rama: 16:10, todos `[skip ci]`). Un archivo cuenta como subido solo si el blob de la rama es igual a `git hash-object` del archivo local:
- `router inteligente universal/integration/chat_mvp/resilience.py`: local `9059048d` · rama `9059048d` → SUBIDO (blob igual)
- `router inteligente universal/integration/chat_mvp/model_pool.py`: local `34df8847` · rama `34df8847` → SUBIDO (blob igual)
- `router inteligente universal/integration/chat_mvp/router.py`: local `3df348b1` · rama `3df348b1` → SUBIDO (blob igual)
- `router inteligente universal/integration/chat_mvp/route_api.py`: local `83d2e677` · rama `83d2e677` → SUBIDO (blob igual)
- `router inteligente universal/integration/chat_mvp/providers.py`: local `e8c03459` · rama `e8c03459` → SUBIDO (blob igual)
- `router inteligente universal/integration/chat_mvp/app.py`: local `059d806a` · rama `059d806a` → SUBIDO (blob igual)
- `router inteligente universal/integration/plugin_host/host.py`: local `7956eeb2` · rama `7956eeb2` → SUBIDO (blob igual)
- `router inteligente universal/integration/plugin_host/api.py`: local `a0c11882` · rama `a0c11882` → SUBIDO (blob igual)
- `router inteligente universal/tests/test_plugin_host.py`: local `be5844fa` · rama `be5844fa` → SUBIDO (blob igual)
- `router inteligente universal/tests/test_model_pool.py`: local `ba5c3d47` · rama `ba5c3d47` → SUBIDO (blob igual)
- `router inteligente universal/tests/test_resilience.py`: local `26255aa3` · rama `26255aa3` → SUBIDO (blob igual)
- `router inteligente universal/tests/test_chat_mvp_app.py`: local `fd64ad22` · rama `fd64ad22` → SUBIDO (blob igual)
- `chat router/05-AGENTES/colmena/router_cliente.py`: local `3d9fd1dc` · rama `3d9fd1dc` → SUBIDO (blob igual)
Veredicto: todo lo de la tabla está SUBIDO a la rama (blob igual al local). SUBIDO no significa probado: los commits de la rama llevan `[skip ci]`; la evidencia de CI es la de los flujos temporales de la sección de CI. La rama NO está unida a `main`.

### C. Correcciones hechas desde las 11:20 y notas anteriores que eran falsas
- 🟡 `ROUTER_SATURATED` = 503 también en `/chat/send` con `auto`: `router.py` líneas 243-244: `503 if busy else 502`. Las notas de las 11:20 decían 502: obsoleto. Los otros fallos de `auto` (`ROUTER_ALL_ROUTES_FAILED`, `ROUTER_NO_ROUTE_AVAILABLE`) siguen siendo 502 con texto plano (≤ 900 caracteres). En `/chat/route` sigue siendo 503 (409 solo para `NEEDS_DIRECTOR_AUTH`, hoy ningún grupo).
- 🟡 `providers._http` enmascara la llave ANTES de cortar a 160 caracteres: `providers.py` líneas 98-99 (comprobado). Límite: la máscara solo cubre la llave exacta (hallazgo f abajo) y no tiene prueba propia.
- 🟡 413 ya no enfría el modelo, no reintenta en otra llave ni abre el cortacircuitos: `resilience.py`: `NO_FAILOVER = {400, 404, 410, 413, 422}` (línea 34) y `REQUEST_ERRORS = (400, 413, 422)` (línea 243); prueba `test_a_413_too_large_is_a_request_problem_no_other_key_no_breaker_no_cooling` en `test_model_pool.py` (comprobado). Antes de esto las notas decían «400/422» y «400, 404, 410, 422».
- 🟡 `run_policy`: el `try` empieza antes de `pool.filter`: `resilience.py` líneas 274-276 (comprobado): los arriendos de sonda se devuelven siempre, pase lo que pase después.
- 🟡 Pruebas endurecidas: Prueba de espera de hueco más estricta (1,5 s / 0,6 s, umbral 1,2 s; solo según el archivo de hechos, no lo verifiqué) y prueba de arranque del host con `TestClient` (commit `665a6142`, 16:00, comprobado en el registro de commits).
- 🟡 `host.py` ya no se cae con una ficha hostil: Un JSON anidado de 200 KB (`RecursionError`) o un `timeout_ms` de 400 dígitos (`OverflowError`) solo marcan ESE plugin como inválido; un estado ilegible o anidado se ignora (`host.py` líneas 222, 238 y 249, comprobado).
- 🟡 `RouterCliente` ARREGLADO en la rama: Commit `40924286` (11:45): manda `provider:"auto"` (`router_cliente.py` línea 107), lee `reply` primero (línea 91) y muestra el detalle del error; prueba nueva `chat router/05-AGENTES/colmena/tests/test_router_cliente_live.py` (commit `3ac20597`). Sin CI ejecutado (`[skip ci]`). Antes las notas decían «sin parche»: obsoleto. 🔴 Preexistente: `test_colmena.py::test_hive_block_por_sheriff` falla igual antes y después (según el archivo de hechos; no lo ejecuté).
- 🟡 CORRECCIÓN al hecho 10: el Job SÍ pone `RIU_CHAT_ALLOW_PROVIDER_LIVE=1`: `agents-yaiwes/common/router_job_persistent.py` línea 74: `os.environ.setdefault("RIU_CHAT_ALLOW_PROVIDER_LIVE", "1")`, desde el commit `b8c8a1cb` (2026-09-23) (comprobado). Las notas de las 11:20 decían que el Job NO lo tenía: obsoleto. Lo único que falta al Job es `HF_TOKEN_1`: el lanzador de `main` (leído a las 16:24) solo le pasa `GITHUB_TOKEN`, `RIU_ROUTER_API_KEY`, `RIU_AGENT_API_KEYS`, `NVIDIA_API_KEY_1..4` y `GROQ_API_KEY_2..7`. Sin `HF_TOKEN_1` el proveedor `hf` queda NOT_CONFIGURED: DeepSeek sale de la cadena `default` (queda Kimi → GLM → Qwen → Nemotron) y `code` y `minor` quedan solo con Nemotron.

### D. Plugin Host (Bloque 2) — ya subido a la rama
- Plugin Host (Bloque 2) SUBIDO a la rama (ya no «sin código»): `integration/plugin_host/{__init__,host,api}.py`, `plugins/{__init__.py, chat/{__init__.py, ficha.json, plugin.py}, thinking-modes/ficha.json, README-ROJO.md}` y `tests/test_plugin_host.py` (22 funciones `test_`). `app.py` lo monta UNA vez dentro de un `try` (líneas 38-44) y aplica la compuerta 503 «plugin chat apagado» a los routers `/chat` (`api.py` línea 26); si el host falla, el chat sigue (falla abierta, según el archivo de hechos). Chat = ON por defecto (`enabled_default: true`); `thinking-modes` = OFF (`enabled_default: false`) y sin código (placeholder: si se enciende, degrada). Ficha del chat en estado `testing`, sin firma GPG ni `tribunal_case_id` (dicho en su `nota_roja`). 🟡 hecho y probado en CI (71 pruebas de cadena+host, corrida 36630393673), NO ✅. Límite honesto: el chat sigue cableado directo en `app.py`; el «plugin chat» es hoy compuerta + estado (hallazgo i). 🔴 Sin cablear de lo de Fables: failover declarativo, presupuesto por nivel, evidencia L1–L4, hot-swap, sandbox C13; y falta el OK del Director al «tribunal».

### E. CI y pruebas (cifras del archivo de hechos; no consulté las corridas)
- Flujo temporal `tmp-bloque1-cadena-verify.yml` (sigue en `main`; comprobado a las 16:24). Corridas citadas: 36627207547 (falló porque al workflow le faltaba `plugins/` en el sparse-checkout: no era fallo de código), 36628329992 y 36630393673 (la última con código ANTERIOR a las correcciones de las 15:50).
- Corrida 36630393673 (cifras del archivo de hechos; yo NO consulté las corridas): carpeta de pruebas completa en la rama 212 pasan / 8 fallan / 6 error = el MISMO conjunto que `main` (huella `fa97bc78c2a8e444`; `main` 153 pasan) → no se rompió nada; cadena + host 71 pasan / 0 fallan; mutaciones de unidad 25/25 y de rutas 14/14 detectadas; en vivo con llaves reales la cadena funciona escalón por escalón (GLM a veces tarda más de 30 s y la cadena salta a DeepSeek).
- Corrida 36631448155: la cita el coordinador; su resultado NO consta en el archivo de hechos y no la consulté → 🔴 leer su resultado antes de dar por probadas las correcciones de las 15:50.
- Las correcciones de la ronda 4 (host robusto, 413) tienen pruebas nuevas que pasan en el shim local (`test_model_pool` 36 pasan / 0 fallan; `test_plugin_host` 18 pasan + 4 saltadas por falta de FastAPI) y se vuelven a correr en CI: 🟡 hasta ver ese resultado.
- Conteo por lectura de la rama a las 16:24 (no es ejecución): `test_model_pool.py` 36, `test_resilience.py` 12, `test_nvidia_pool.py` 4, `test_plugin_host.py` 22 → 74 funciones de cadena + host (71 en la corrida citada; la diferencia de 3 no está reconciliada, seguramente pruebas añadidas después: SIN VERIFICAR); `test_chat_mvp_app.py` 13. Las cifras viejas (42 de cadena, 183 en la carpeta completa) son de antes del Plugin Host.

### F. Hallazgos abiertos de la ronda 4 → 🔴 (ninguno es un cambio de código hecho)
- (a) Un plugin que retiene el GIL (por ejemplo un regex catastrófico) congela TODO el proceso, incluido `/health`: el arnés solo aísla por hilo; hace falta aislamiento por proceso.
- (b) Lanzador `riu-router-job-central.yml`: si las 3 escrituras del flag fallan igual cancela los Jobs viejos; si `/health` no llega a 200 en 480 s el Job nuevo queda vivo sin cancelar; la línea ~104 llama `.json()` sin proteger; la línea ~106 escribe `PAUSED=false` y anula una pausa puesta por el Director.
- (c) Pasar `HF_TOKEN_1` al Job deja dentro del Job el token que controla los Jobs (lo leería cualquier plugin `integration.*`): mejor un token solo de inferencia (decisión del Director, D14).
- (d) El CI permanente `riu-chat-mvp-verify.yml` NO lista `test_plugin_host.py`, no trae `plugins/` en el sparse-checkout ni `plugin_host/` en el filtro de rutas: hoy el host solo lo cubre el workflow temporal, que se va a borrar.
- (e) Un relanzamiento del Job pierde las conversaciones, la caché y el estado del chat (`RIU_DATA_DIR=/tmp/riu`) y el interruptor de plugins.
- (f) La máscara de llaves de `providers._http` solo cubre la llave exacta (un eco parcial o escapado en JSON no) y no tiene prueba.
- (g) `last_error` / `reason` de un plugin puede devolver el texto de una excepción.
- (h) `GET /plugins` es `def` síncrono: bloquea un hilo hasta 5 s (acotado por `MAX_INFLIGHT=8`).
- (i) El chat sigue cableado directo en `app.py`: el «plugin chat» es hoy compuerta + estado.
- (j) NVIDIA acepta llaves hasta `_5` (el Director habla de 4).
- (k) El arriendo de sonda toma por adelantado todos los modelos recuperados: mientras A prueba Kimi, B ve GLM como `COOLING` aunque esté sano (BAJO, de diseño).
- (l) `/chat/send` sin `auto` bloquea el event loop (ya está en `main`).
- (m) El tope real de concurrencia es el executor por defecto de asyncio (`min(32, cpu+4)` = 6 hilos en 2 vCPU): el tramo 3→10 no se alcanza y del 7º chat en adelante esperan en cola sin `ROUTER_SATURATED` (PLAUSIBLE, medido con 40 tareas × 0,5 s = 3,5 s).

### G. Prioridad 2: chat + agentes (orden 11:07, reafirmada el 16:14)
- Inventario de prioridad 2 (`INVENTARIO-PRIORIDAD2.md`, 372 líneas, en el scratchpad de esta sesión, NO en el repo; lo hizo un subagente de solo lectura y no ejecutó pruebas): el DAG `riu.dag/v1` de `chat_mvp/dag.py` corre pero no tenía loops ni nodos de ruta; sheriff, juez, sentinela, guardián e investigador existen como código determinista en `chat router/05-AGENTES/gobierno/`; las fuentes de Hermes y OpenClaw están en `Componente open soure router inteligente universal/` (`hermes-agent-v2026.9.24`, `openclaw-v2026.9.6`); el puente/gateway de asistentes es UNA llamada con un prompt de rol directo a NVIDIA con una sola llave (no el agente real; la regla de las 02:06 NO está implementada); el harness de DeepSeek es solo un patrón (falta el runtime); el generador de espejo del equipo estaba MISSING/PARTIAL; las UI de chat apiladas están PARTIAL (`13-CHAT-UI-SUITE`); `chat router/03-ESTADO/` no está en `main`.
- Plan de prioridad 2 en la rama `bloque2-agentes` (cabeza `197d1fc4`, 16:23; todos los commits `[skip ci]`; NO unida a `main`; 🟡 hecho sin CI, yo no ejecuté nada): (1) DAG con nodos `route:{group}` y `loop:{until,max_iterations}` (estados PASSED / MAX_ITERATIONS / REPEATED_x3; commits `c918d4a6`, `7124c25a` con `dag_cli` aceptando `group=`, y pruebas `test_dag_route_loop.py` en `645c5eca`); (2) espejo del equipo `gobierno/espejo_equipo.py` (modos hermes_openclaw / equipo_completo, dry-run por defecto; commits `698a189f` y `3bc2cdb0`); (3) restaurar `chat router/03-ESTADO/` (9 archivos) y `Claude notas/HANDOFF-PARCHE-RECUPERACION-2026-09-21.md` desde `backup-antes-limpieza-20260929` (commits de las 16:21 a las 16:23).
- 🔴 Todavía SIN commits (comprobado en la rama a las 16:24): grupo de política `assistants` y Hermes/OpenClaw apuntados al Router (con la regla de las 02:06), envoltura del harness de DeepSeek (~20 líneas: timeout → `degraded`), varias UI de chat apiladas.

### H. Activación del Router — en curso por otro agente
- Activación del Router (unir la rama a `main`, relanzar el Job y agregar `HF_TOKEN_1` a los secretos del Job): EN CURSO por otro agente (según el coordinador; no lo verifiqué). Estado del repo a las 16:24: la rama NO está unida a `main` (`git merge-base --is-ancestor` da falso); el lanzador de `main` todavía NO pasa `HF_TOKEN_1` al Job; `main` está en `9b1914e5` (commits «orch-chat P1» de las 16:11 que no son de este agente de notas). Job vivo conocido: `6abb503a6b030d633f6a2dca` (no reverificado). Al terminar esa activación hay que releer: la unión, el Job nuevo, `LIVE_URL`, `/health`, `/chat/router/status`, `/chat/send` con `provider:"auto"` y `/plugins`, y borrar los workflows temporales. Riesgos a tener presentes: hallazgos b y c (pasar el token que controla los Jobs al Job, D14).

### I. Contradicciones halladas en la segunda pasada (archivo de hechos, notas de las 11:20 y repo)
1. Hecho 10 del archivo de hechos (el Job no pone `RIU_CHAT_ALLOW_PROVIDER_LIVE`): FALSO, lo corrige la adenda de las 15:50 y lo confirmé leyendo `router_job_persistent.py:74` (`setdefault`, commit `b8c8a1cb` del 2026-09-23). Mis notas de las 11:20 lo repetían: quedan corregidas. Lo que sí falta es `HF_TOKEN_1`.
2. Saturado = 503: el archivo de hechos de las 11:15 decía 503 y el código de las 11:20 daba 502 en `/chat/send` con `auto`; desde la ronda 3 el código da 503 (`router.py:243-244`). Ahora hechos y código coinciden; las notas de las 11:20 que decían «502» quedan obsoletas.
3. «Sin código del Plugin Host» (notas de las 11:20): obsoleto; el host se subió a la rama a las 11:44 y se corrigió entre las 15:27 y las 16:10. Sigue siendo cierto que el chat está cableado directo en `app.py`.
4. «`RouterCliente` no funciona / sin parche» (notas de las 11:20): obsoleto; arreglado en la rama en el commit `40924286` (11:45).
5. Errores que no enfrían: «400/422» pasa a «400/413/422» (y `NO_FAILOVER` también incluye 404, 410).
6. Cifras de pruebas: «42 de cadena» y «183 en la carpeta completa» son anteriores al host; la corrida citada 36630393673 da 212 pasan / 8 fallan / 6 error en la carpeta completa y 71 de cadena+host; por conteo de la rama hay 74 funciones de cadena+host. La diferencia de 3 no está reconciliada (SIN VERIFICAR).
7. Bloques de «estado de subida» de las 11:33 (`cb229a12`, 8 archivos): obsoletos; la rama está en la cabeza indicada arriba y la tabla nueva sustituye a la vieja.
8. El «comentario de `peak.py`» de las notas anteriores era impreciso: es el comentario dentro de `resilience.py` que cita la ruta de `peak.py` (el commit `352327a4` solo toca `resilience.py`); `peak.py` no se modificó.
9. El docstring de `CircuitBreaker` sigue a medias (comprobado a las 16:24): `resilience.py` línea 65 todavía dice «lets one probe through after `cooldown` seconds» mientras el código en half-open deja pasar a todos; ni la ronda 3 ni la 4 lo corrigieron. 🔴
10. El coordinador cita la corrida 36631448155, que no está en el archivo de hechos: se anota sin resultado (🔴).
11. La rama `bloque2-agentes` restauró `chat router/03-ESTADO/` (9 archivos: `HANDOFF.md`, `BITACORA.jsonl`, `CRAZY_WALL.json`, `STATE.json`, `MEMORIA-INVENTARIO.json`, `MEMORIA-PRUEBA.json`, `OPUS-PENDIENTE.md`, `RECUPERACION-OMNIROUTE.yaml`, `RECOVERY.yaml`) desde la copia de respaldo de Opus: son copias VIEJAS con nombres iguales a los vigentes de `Estado y handoff global/`. Los vigentes son los de `Estado y handoff global/`; al unir esa rama no hay que confundirlos.
12. `Vercel/vercel-chat/api/chat.js` sigue llamando con `provider:'hf'` fijo (línea 31, comprobado en la rama); NO se toca Vercel. T-25 sigue sin estar definida en ninguna fuente y no se inventó.

### J. Próximos pasos, en orden
1. Leer el resultado de la corrida 36631448155 y volver a correr el CI sobre la rama con las correcciones de las 15:50 (🔴).
2. Ronda 5 de auditoría independiente; para ✅ hacen falta 3 rondas limpias seguidas y las 4 pasadas (🔴).
3. Que el otro agente termine la activación: unir a `main`, `HF_TOKEN_1` en los secretos del Job (mejor un token solo de inferencia: D14), relanzar con el lanzador único, verificar y borrar los workflows temporales (🔴 en curso, no verificado por mí).
4. Arreglos chicos: primera frase del docstring del cortacircuitos, listar `test_plugin_host.py` y `plugins/` en el CI permanente (hallazgo d), endurecer el lanzador (hallazgo b), prueba de la máscara de llaves (hallazgo f), aislamiento por proceso de los plugins (hallazgo a) (todos 🔴).
5. Prioridad 2 (orden de las 16:14: cableado y workflow, sin sobre-ingeniería, delegar a agentes): terminar en `bloque2-agentes` el grupo `assistants` con Hermes y OpenClaw apuntados al Router, el envoltorio del harness y las UI de chat apiladas; luego revisar y unir (🔴).
6. Decisiones del Director D1 a D14 (D14 nueva: token solo de inferencia para el Job).
7. Bloque 3, IA local, autoescalado y pantalla final siguen como estaban (🔴).

## Tareas (una ficha por tarea; cada enlace sirve como handoff y control de trabajo)
Base: https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/Estado%20y%20handoff%20global/tareas/

| # | Tarea | Estado | Ficha |
|---|---|---|---|
| T-02 | Reorganizar el repo en las raíces pedidas | PASS | `T-02-reorganizar-repo-en-raices.md` |
| T-04 | Equipo de los 4 objetivos conectado al Router único + sentinela | PENDIENTE | `T-04-equipo-4-objetivos-al-router.md` |
| T-05 | 20 sitios de investigación en el motor de búsqueda | PENDIENTE | `T-05-veinte-sitios-de-investigacion.md` |
| T-06 | Cadena Rowboat → Ruflo → Claude Code → Grok → Claude Code → 4 Meta | PENDIENTE | `T-06-cadena-rowboat-a-4-meta.md` |
| T-07 | Skills (ECC, Archify, Agent Skills, Ponytail) a esquema Sheriff/DSL DAG | PENDIENTE | `T-07-skills-a-esquema-sheriff.md` |
| T-08 | Memoria de Manus + puente Hugging Face | PENDIENTE | `T-08-memoria-manus-y-puente-hf.md` |
| T-09 | Un solo deploy final del chat en Vercel | BLOQUEADO (solo con orden del Director) | `T-09-vercel-deploy-final.md` |

Las tareas del Router (T-00, T-01, T-03, T-10) ya no están aquí: ver el handoff provisional del Router.

## Dónde está cada cosa (main)
`router inteligente universal/` (Router, `Banco de claves/`, `Componentes del Router/`) · `chat router/` · `Motores descarga extracción búsquedas/` · `Readme router inteligente universal/` · `Readme arquitectura router inteligente universal/` · `Claude notas/` (solo en curso; el checkpoint vigente es `CHECKPOINT-2026-09-29-1100-router-chat-plugins.md`) · `Estado y handoff global/` (esta carpeta) · `Huggingface/` · `Vercel/` · `Documentos del proyecto/`. Sueltos: `README.md`, `CLAUDE.md`, `vercel.json`.

## Reglas del Director (siempre)
- Seguir sus instrucciones textuales; sin alucinar, sin sobre-ingeniería; si hay duda, preguntar en texto plano (nada de widget de opciones: usa el móvil).
- Los modelos se llaman SOLO por el Router único (ver su handoff). Sin APIs de Anthropic.
- Nunca claves en el repo (es público): solo nombres de secretos.
- No instalar nada hasta que todo esté listo; un único deploy final, solo si él lo ordena.
- No tocar ni reiniciar el conector MCP (Space `claude-github-mcp-backup`). `keep-mcp-space-awake` sigue desactivado.
- Prohibido escribir código desde cero: podar, editar quirúrgico y cablear lo descargado.
- No borrar componentes: se reubican.
- Respuestas cortas (~10 líneas), español simple. Explicar el cómo antes de hacer.

## Abiertos / no inventar
- Rama `bloque1-cadena-chat`: NO está unida a main (comprobado a las 16:30); el código de la cadena del chat y el Plugin Host solo existen allí; `bloque2-agentes` (prioridad 2) tampoco está unida. Los workflows temporales (`tmp-bloque1-cadena-verify.yml`, en main) hay que borrarlos al terminar.
- `T-25`: no está definida en ninguna fuente; si existe, que el Director o el coordinador la definan (no se inventó).
- Cifras de pruebas de fuentes distintas que no se han reconciliado: 168 pasan / 8 fallan / 0 errores (corrida 36526076292) frente a 153 / 8 / 6 (main, carpeta completa); ver el handoff del Router, sección 18.
- "Prompt Master": no verificado qué es. Buscar en `Documentos del proyecto/Notas del Director (verbatim)/`; si no aparece, decir que no se sabe.
- El loop del repo `agentes` todavía usa la ruta vieja del banco (`Chat%20Mvp/…`); se resuelve en T-04.
- Workflows con rutas corregidas en la reorganización que no se probaron en vivo: `riu-microkernel-run`, `riu-agents-run`, `riu-chat-mvp-core-verify`, `riu-agent11-canonical-download` (además mira `hermes-agent/` en la raíz, que ahora está en `Componentes del Router/`), `riu-websearch`, `riu-websearch-run`, `riu-dag-run`, `riu-propagate-auth-secrets`.
- Link del chat de Manus: pendiente de que lo pase el Director (T-08).

## Cómo se trabaja (herramientas)
- GitHub por conector: `github_api` (puede lanzar workflows), `create_or_update_file` (usa `current_sha` para actualizar). Errores 502: reintentar, comprobando antes que la acción no se haya hecho.
- Cambios grandes: workflow de una sola vez con PAT (el token por defecto no puede empujar archivos de workflow), checkout parcial en lote (rápido) y `[skip ci]` en el commit para no disparar otros workflows. El workflow se borra a sí mismo al aplicar.
- Resultados de un run: leer las anotaciones del check-run (máx. 10 por paso).
