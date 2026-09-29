# CHECKPOINT 2026-09-29 (~11:20 Bogotá) — Router, chat como plugin y Plugin Host
Nota de checkpoint completa, escrita por el agente de notas por orden del Director (11:07: "checkpoint progresivo por si Anthropic se satura"). Regla: SINTETIZAR, NO RESUMIR; nada se marca ✅ sin evidencia; solo se escribe lo que está en el archivo de hechos del checkpoint (11:15) o lo que se verificó leyendo el repo; ninguna llave ni valor secreto (solo nombres).
Otras copias del mismo estado: `Estado y handoff global/BITACORA.jsonl` (B-0022 a B-0029), `HANDOFF.md`, `ESTADO.json` (clave `checkpoint_2026_09_29_1120`), `CRAZY_WALL.json` (nodos N-10 a N-19); detalle técnico: `router inteligente universal/HANDOFF-PROVISIONAL-ROUTER.md` (secciones 10 a 19).

## 0. En palabras simples (para el Director)
- Qué es: hay UN solo Router de modelos de IA. Todo lo demás (el chat, los agentes, las pantallas) se conecta a él; el chat es solo un plugin más (tu orden de las 10:55).
- Qué se construyó hoy: el Router ahora sabe pedir a NVIDIA y a Groq qué modelos están disponibles, recuerda cuáles dejaron de contestar y los deja descansar 2 minutos, y cuando un modelo falla pasa solo al siguiente. El orden para el chat es: Kimi K3, luego GLM 5.3, luego DeepSeek V4, luego Qwen 3.8 (Groq) y Nemotron al final. Si un modelo tarda más de 30 segundos, lo salta.
- Cómo fluye: alguien manda un mensaje al Router con la opción "automático"; el Router arma la lista de modelos disponibles, prueba el primero, y si no contesta a tiempo o da error prueba el siguiente hasta que uno responde; la conversación se mantiene aunque cambie el modelo.
- Qué está probado: el código se probó en un entorno de prueba con llaves reales y funcionó escalón por escalón; NO se ha probado en el Router que está encendido, porque ese no tiene el código nuevo todavía.
- Qué NO está listo: dos rondas de revisión independiente encontraron defectos (ya corregidos) y hacen falta tres rondas limpias seguidas para poder decir "verificado". Las últimas correcciones están subidas pero todavía no se han probado en el entorno de prueba. El Plugin Host (donde se conecta el chat como plugin) lo está construyendo otro agente. Hermes y OpenClaw no se han tocado. La pantalla va al final.
- Qué necesito de ti: las decisiones de la sección 6 (cada una explicada en simple, con lo que se hará si no contestas).

## 1. Marcas y regla de verificación
✅ VERIFICADO (ejecutado + probado + 4 pasadas de revisión + 3 rondas limpias seguidas) · 🟡 HECHO SIN PROBAR / probado a medias · 🔴 PENDIENTE · ⛔ BLOQUEADO. **Nada está ✅ todavía.** Las 4 pasadas (regla del Director de las 05:18, interpretación de Claude en `…-director-parte-4.md`): instrucciones, código fuente, archivos y documentos, ejecución; y 3 bucles: 3 vueltas seguidas de todo el bloque sin hallazgos nuevos. Los "PASS" antiguos del handoff del Router (T-00, T-01, T-03) vienen de corridas reales anteriores a esta regla y no se han reauditado con las 4 pasadas.

## 2. Órdenes del Director vigentes (con qué texto consta cada una)
- 10:55 (entre comillas tal como está en el archivo de hechos): "Ok termina el router y activalo / El chat es solo un plugins más conectado al router" → autoriza RELANZAR el Job del Router tras terminarlo; el chat es UN plugin más, no el centro.
- 11:07 (paráfrasis del archivo de hechos; el texto literal NO está en el repo): checkpoint progresivo (bitácora, estado JSON, handoff, Claude notas, Crazy Wall) por si Anthropic se satura; no desviarse; terminar el Router primero (prioridad 1) con un agente en paralelo auditándolo; luego chat + agentes (prioridad 2): DSL DAG con loops, agente orquestador, Hermes y OpenClaw como asistente / sheriff / sentinela / supervisor / juez / guardián / investigador de contexto / manipulación de memoria y almacenamiento, harness de DeepSeek; el sistema debe poder generar un espejo (mirror) solo de Hermes+OpenClaw o de todo el equipo, y varias UI de chat una debajo de otra, todo separado, nada monolítico.
- 11:11 (paráfrasis del archivo de hechos): delegar varias tareas a varios agentes (Claude escribe el código, los agentes hacen lo demás) para terminar lo antes posible.
- 05:18 (textual, `Readme arquitectura router inteligente universal/INPUT-BLOCK-VERBATIM-2026-09-29-director-parte-4.md`, solo en main): "una vez que hagas una salida cuando termines haces 3 bucles de revisión de todo verificación cruzada con el code fuente y los archivos y las instrucciones 4 pasadas por tarea terminada sin eso no está 100 pass ✅".
- 05:15 (textual, `…-director-parte-3.md`): cadena aprobada ("Si ese flujo Pero igual el router debe pedir a la api repuesta de modelos disponibles"); paralelo y cola con cimientos para crecer; el tribunal se explica; el ZIP se monta apagado y se enciende desde el chat o el panel, con notas en rojo; la pantalla y las fichas verdes de Fables son prototipo y la UI va al final; VPS, PC, smartphone, HF o web conectables como plugins (HTTP, SSH, MCP); todo en GitHub y HF solo puente/túnel, datasets de IA, almacenamiento y procesador; "sintetizar y no resumir".
- 02:06 (textual, `INPUT-BLOCK-VERBATIM-2026-09-29-director.md`, línea 36): "El chat y los agentes de Hermes y open claw prioridad con Nvidia si está ocupado las primeras 3 Salta a la 4 o a groq". Alcance: el chat Y los agentes de Hermes y OpenClaw. Hoy solo se cubre el chat (a medias); Hermes y OpenClaw NO se tocaron (🔴).
- Cadena aprobada del chat: Kimi K3 → GLM 5.3 → DeepSeek V4 → Qwen 3.8 (Groq) → Nemotron ÚLTIMO; si uno falla cae al siguiente; el Router pide a la API los modelos disponibles.

## 3. Estado por bloque
### 3.1 Bloque 1 — cadena de modelos del chat dentro del Router (prioridad 1) — 🟡
Rama `bloque1-cadena-chat` (NO unida a main), carpeta `router inteligente universal/integration/chat_mvp/`.
Qué hace el código:
- `model_pool.py` (nuevo): pide `/models` a NVIDIA y Groq (plazo 6 s por proveedor, máximo 2 llaves, caché 300 s o 60 s si la lista quedó desconocida); enfriamiento de 120 s por modelo que falló (`RIU_MODEL_COOLDOWN`); al terminar el enfriamiento UNA sola petición prueba el modelo con un "arriendo" de 30 s y las demás lo siguen saltando; si el filtro deja la cadena vacía se intenta la cadena completa (`POOL_EMPTY_TRY_ALL`); si un proveedor no lista, no responde o no hay llave, el modelo se INTENTA igual.
- `resilience.py`: política por grupo (`DEFAULT_POLICY`), plazo por opción (30 s base × `max_tokens`/1024, tope 90 s; la última opción 90 s para todas sus llaves), cortacircuitos por (proveedor, hash de llave, modelo) y limitador adaptativo 3→10 espacios (≥ 5 s de espera sube a 10; ≥ 20 s → `ROUTER_SATURATED`).
- `route_api.py`: `/chat/route` (grupo `default`/`code`/`minor`/`g2`), `/chat/router/status`, `/chat/router/models` (REPORTE: no gasta la sonda única), `/chat/jev`.
- `router.py`: `/chat/send` con `provider:"auto"` (el Router elige el modelo; el texto vuelve en `reply`; en auto no hay caché, se ignora `X-Provider-Key` y `certified` es siempre `false`), `/chat/providers` lista "auto" primero y `/chat/providers/auto/models` devuelve un seudo-modelo.
- `providers.py`: `ATTEMPT_DEADLINE`, el plazo de la opción en curso, que viaja por `contextvars` hasta la llamada HTTP.
Las 4 cadenas exactas (`resilience.DEFAULT_POLICY`, leídas en el código; todas con respaldo autorizado):
- `default`: `nvidia moonshotai/kimi-k3` → `nvidia z-ai/glm-5.3` → `hf deepseek-ai/DeepSeek-V4-Flash` (se salta en hora pico) → `groq qwen/qwen3.8-27b` → `nvidia nvidia/nemotron-3-super-120b-a12b` (último).
- `code`: `hf MiniMaxAI/MiniMax-M3` → Nemotron.
- `minor` (solo MiniMax en hora pico): `hf deepseek-ai/DeepSeek-V4-Flash` → Nemotron → `hf MiniMaxAI/MiniMax-M3`.
- `g2`: Kimi K3 → GLM 5.3 → `groq` (modelo de `RIU_G2_GROQ_MODEL`) → `local` (modelo de `RIU_G2_LOCAL_MODEL`) → DeepSeek V4 Flash (se salta en pico) → Nemotron. Reescrito por Claude; falta el OK del Director.
- Hora pico de DeepSeek: 01–04 y 06–10 UTC de lunes a viernes = en Bogotá 20:00–23:00 de domingo a jueves y 01:00–05:00 de lunes a viernes. En ese horario el chat automático NO usa DeepSeek.
- Comportamiento de errores: `/chat/route` responde 503 con `{error, trace}` (409 `NEEDS_DIRECTOR_AUTH` solo si un grupo no tuviera respaldo autorizado: hoy ninguno); `/chat/send` con `auto` responde 502 con un texto plano `CÓDIGO | traza ; traza` (≤ 900 caracteres). Un grupo desconocido usa `default`.
Evidencia (🟡; todo de flujos temporales en el runner de CI, NO del Router vivo; cifras del archivo de hechos, no consulté las corridas):
- Corridas del flujo temporal `tmp-bloque1-cadena-verify.yml` (vive en main, blob `a86b3504`): 36557644179, 36561019462, 36562078042.
- Carpeta de pruebas completa: 183 pasan en la rama contra 153 en main; el MISMO conjunto de 14 fallos previos en las dos (huella `fa97bc78c2a8e444`: `test_vault_wordflow_jobs` 6 errores, `test_conector_*_v6` 6, `test_fast_close_global_e2e` 1, `test_huggingface_openai_chat_registry` 1) → no se rompió nada.
- 42 pruebas de la cadena pasan. Mutaciones: 27 de 28 detectadas; la sobreviviente ("respuesta vacía guardada") se cubrió con una prueba nueva en `test_resilience.py` (blob `ddc69404`), que necesita FastAPI y de la que no consta corrida propia (🟡).
- En vivo con llaves reales (runner): cadena escalón por escalón OK (Kimi → GLM → DeepSeek(hf) → Qwen (Groq) → Nemotron) y `/chat/send` con `provider:"auto"` mantiene la conversación. Kimi K3 respondió lento hoy (25–30 s en 2 de 3 intentos): el Router lo salta tras 30 s y lo recuerda 2 min. El escalón DeepSeek(hf) se probó con `RIU_CHAT_ALLOW_PROVIDER_LIVE=1` y `HF_TOKEN_1` puestos en el runner, cosas que el Job vivo no tiene.
Estado de subida de las correcciones de la ronda 2 (comprobado con `git fetch` al escribir):
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

### 3.2 Auditorías independientes — NO LIMPIAS
- Ronda 1 (NO LIMPIA, sin bloqueadores, defectos reales). Corregido y con CI: un Router saturado ya no marca "modelo muerto"; 400/422 no enfrían el modelo; plazo por opción (30 s base × tokens/1024, tope 90 s; última opción 90 s); las llaves del mismo modelo no se siguen probando cuando se agotó el tiempo; el cortacircuitos perdona fallos viejos; sonda única. (Además: `/chat/router/models` con las mismas reglas que una petición real; "Automático" primero en `/chat/providers`; `RIU_MODEL_COOLDOWN` tolerante.)
- Ronda 2 (NO LIMPIA, sin bloqueadores, defectos reales). Subidas a la rama entre las 11:14 y las 11:18, SIN CI: (1) el tiempo esperando un hueco del limitador ya no se le cobra al modelo; (2) cualquier excepción de una opción pasa a la siguiente (no solo `RuntimeError`); (3) Router saturado corta la cadena al instante con `ROUTER_SATURATED` y no enfría modelos; (4) los arriendos de sonda no usados o sin veredicto se devuelven (`release`, solo el propio); (5) `RIU_CHAT_ATTEMPT_TIMEOUT` no finito → 30; (6) el 502 de `/chat/send` trae un texto plano ("ERROR | traza ; traza", ≤ 900) en vez de un objeto; (7) docstring del cortacircuitos (a medias: la primera frase todavía dice "lets one probe through"); (8) comentario de `peak.py` (ya estaba corregido desde la ronda 1, commit 352327a4); (9) `z-ai/glm-5.3-flash` y `deepseek-ai/deepseek-v4.1-flash`: "posible arranque en frío: NO CONFIRMADO: no se usan hasta probarlos otra vez".
- Pruebas locales del agente que corrigió (con un `pytest` de mentira, sin FastAPI): `test_model_pool.py` 35 pasan, 0 fallan; `test_resilience.py` 7 pasan y 5 figuran como "fallan" porque en realidad se SALTAN (necesitan FastAPI: solo corren en CI).
- Siguiente: ronda 3 cuando la ronda 2 tenga CI; para ✅ hacen falta 3 rondas limpias seguidas y las 4 pasadas por tarea.

### 3.3 El Router vivo y la activación — 🔴
- El Router es un Job de Hugging Face cpu-basic 16 GB lanzado por `.github/workflows/riu-router-job-central.yml`. Job vivo: `6abb503a6b030d633f6a2dca`; auth: Bearer `HF_TOKEN_1` + `X-API-Key`. Corre el código de main ANTERIOR al Bloque 1: `default` = solo Nemotron (sin respaldo autorizado), `g2` = Nemotron → Groq → local → DeepSeek; `/chat/send` con `auto`, por el código de main, daría 400 `PROVIDER_UNKNOWN` en el Router vivo (no probado en vivo).
- Cambio seguro: el lanzador espera `/health` 200 del Job nuevo, escribe `LIVE_URL` en `router inteligente universal/agents-yaiwes/ROUTER_JOB_PAUSE.flag` y SOLO ENTONCES cancela los Jobs viejos.
- Huecos verificados en el lanzador: no pasa `HF_TOKEN_1` al Job (los secretos del Job son solo `GITHUB_TOKEN`, `RIU_ROUTER_API_KEY`, `RIU_AGENT_API_KEYS`, `NVIDIA_API_KEY_1..4`, `GROQ_API_KEY_2..7`) y no pone `RIU_CHAT_ALLOW_PROVIDER_LIVE=1` (su único `env` es `RIU_G2_GROQ_MODEL`). DeepSeek V4 Flash y MiniMax M3 (proveedor `hf`) no están certificados (el registro `model_registry.json` certifica solo `openai-community/gpt2` y `Qwen/Qwen3-8B`); sin la variable y el token la opción DeepSeek fallaría rápido y la cadena seguiría a Qwen. Plan: agregar ambos al lanzador (cambio de workflow: NO hecho) e informar al Director.
- Pasos: (1) CI verde de la rama; (2) Plugin Host mínimo con el chat como primer plugin; (3) unir a main; (4) relanzar; (5) verificar `/health`, `/chat/router/status`, `/chat/send` con `auto` y la lista de plugins; (6) borrar los workflows temporales.
- La URL cambia al relanzar: `RIU_ROUTER_URL` de Vercel quedará vieja. NO se toca Vercel ni el Space MCP `claude-github-mcp-backup` sin orden explícita.

### 3.4 Bloque 2 — Plugin Host mínimo (chat como primer plugin) — 🟡/🔴 EN CONSTRUCCIÓN
Lo construye otro agente. Al 11:20 no hay `plugins/`, ni `ficha.json`, ni código de Plugin Host en la rama (comprobado con `git ls-tree`), ni pruebas. Lo siguiente es el DISEÑO (de `ARQUITECTURA-ROUTER-FICHAS-FABLES.md` §8 y `universal_plugin_bus_v2_integrated.py` de Fables), no lo que ya funciona:
- Plugins en `plugins/<id>/ficha.json`, montados UNA vez por el Router.
- Regla del harness: envoltura obligatoria en cada llamada, removible, sin dependencia dura; ante fallo o timeout devuelve `{status:'degraded', reason}` sin tumbar el Router.
- NO se ejecuta código de terceros: el `ContractGenerator` y el `HotSwapManager` de Fables usan `exec` y NO se copian.
- "Tribunal" = comprobaciones automáticas (contrato válido, límites, sin llamadas peligrosas) + el OK del Director si el plugin puede actuar afuera (escribir en GitHub, entrar por SSH, gastar). Su OK a esa propuesta sigue 🔴 PENDIENTE.
- 🔴 Sin cablear de lo de Fables: failover declarativo, presupuesto por nivel, evidencia L1–L4, hot-swap, sandbox C13.

### 3.5 Bloque 3 — 🔴 PENDIENTE (va en rojo si no se llega)
Registro de fichas; compilador ficha→`riu.dag/v1`; agente operador; autodetección de conexiones; gobernador de capacidad paralelo/cola (sin tope fijo en el código; las dos opciones siempre disponibles); ZIP `yaiwes_subrouters_modulares.zip` (modos de pensamiento: instant, thinking, council, code): revisar su seguridad y montarlo APAGADO con interruptor en el chat y el panel (notas en rojo); conectores plugin (HTTP, SSH, MCP, push al celular; lo que necesite dependencias o llaves que no hay queda 🔴); dataset Yaiwes y anclas del Control Plane (T-24).

### 3.6 Otros pendientes vigentes — 🔴
IA local (DFlash 2, MTP, Flash Attention, KV Q8, Qwen 3.8 Q4 en la máquina de 32 GB) SOLO después del Router y pendientes; autoescalado (la de 16 GB siempre encendida despierta a las otras; escalar al 80 %; la de 32 GB duerme a los 5 min); cruzar con lo previo de Opus (rama `backup-antes-limpieza-20260929`); T-17/T-18; rotar las 7 llaves Groq (acción del Director); restaurar `Claude notas/HANDOFF-PARCHE-RECUPERACION-2026-09-21.md` (solo en la rama de respaldo); regla de infraestructura: todo en GitHub, HF solo puente/túnel, datasets de IA, almacenamiento y cómputo.

## 4. Dónde vive cada pieza
| Pieza | Ruta | Dónde | Marca |
|---|---|---|---|
| App del Router (FastAPI) | `router inteligente universal/integration/chat_mvp/app.py` | main y rama | (existente) |
| Pool de modelos | `…/integration/chat_mvp/model_pool.py` | solo rama | 🟡 |
| Políticas y cadenas | `…/integration/chat_mvp/resilience.py` | rama (main tiene la versión vieja) | 🟡 |
| Endpoints de ruta y estado | `…/integration/chat_mvp/route_api.py`, `router.py`, `providers.py` | rama | 🟡 |
| Pruebas de la cadena | `router inteligente universal/tests/test_model_pool.py`, `test_resilience.py` | rama | 🟡 |
| CI permanente del chat | `.github/workflows/riu-chat-mvp-verify.yml` | rama (main tiene la lista vieja) | 🟡 |
| Flujo TEMPORAL de verificación | `.github/workflows/tmp-bloque1-cadena-verify.yml` | solo main (blob `a86b3504`) | 🔴 borrar al terminar |
| Lanzador del Job | `.github/workflows/riu-router-job-central.yml` y `router inteligente universal/agents-yaiwes/common/router_job_persistent.py` | main | (existente; huecos en 3.3) |
| Dirección viva del Router | `router inteligente universal/agents-yaiwes/ROUTER_JOB_PAUSE.flag` (`LIVE_URL`, `PAUSED`) | main | (existente) |
| Prueba de solo lectura | `.github/workflows/riu-router-smoke.yml` | main | (existente) |
| Cómo conectar algo al Router | `router inteligente universal/CONECTAR-ROUTER.md` | rama | 🟡 |
| Handoff técnico del Router | `router inteligente universal/HANDOFF-PROVISIONAL-ROUTER.md` | rama | 🟡 |
| Arquitectura viva | `Readme arquitectura router inteligente universal/ARQUITECTURA-ROUTER-Y-CONEXIONES.md` | rama | 🟡 |
| Diseño de fichas / plugins | `Readme arquitectura router inteligente universal/ARQUITECTURA-ROUTER-FICHAS-FABLES.md` y los archivos de Fables en `Documentos del proyecto/Documentos proyectos router inteligente universal/` (los que empiezan por "enchufe universal parte 1/2") | main | 🔴 diseño |
| Palabras textuales del Director | `Readme arquitectura router inteligente universal/INPUT-BLOCK-VERBATIM-2026-09-29-director.md` (02:06, 02:35), `…-parte-2.md` (03:26, 03:27, 04:41), `…-parte-3.md` (05:15), `…-parte-4.md` (05:18; solo en main) | main | (registro) |
| Estado global | `Estado y handoff global/` (`BITACORA.jsonl`, `HANDOFF.md`, `ESTADO.json`, `CRAZY_WALL.json`, `tareas/`) | rama | 🟡 |
| Hora pico de DeepSeek | `router inteligente universal/Banco de claves/router_policy/peak.py` | main y rama | (existente) |
| Cliente para otros repos | `chat router/05-AGENTES/colmena/router_cliente.py` | main y rama | 🔴 sin parche (`provider`, `reply`) |
| Chat en Vercel | `Vercel/vercel-chat/api/chat.js`, `Vercel/HANDOFF-VERCEL.md` | main y rama | 🔴 llama con `provider:"hf"` fijo |
| Hermes / OpenClaw | `router inteligente universal/Componentes del Router/hermes-agent/` y su código descargado | main | 🔴 sin tocar |
| Copia de respaldo / notas de Opus | rama `backup-antes-limpieza-20260929` | rama de respaldo | (protegida) |
| Código de la ronda 2 | subido a la rama (ver estado de subida en 3.1) | rama | 🟡 sin CI |

## 5. Contradicciones halladas (notas anteriores / archivo de hechos frente al repo, verificadas por lectura el 2026-09-29 ~11:20)
1. La guia CONECTAR-ROUTER.md (version de la manana, no el archivo de hechos) decia llamar /chat/send sin provider y leer response/content/text/message: sin provider falla (rama: 400 MODEL_REQUIRED; main: 422 por falta de model) y el texto vuelve en reply; el cliente RouterCliente (chat router/05-AGENTES/colmena/router_cliente.py lineas 105-108 y 90) tiene el mismo error y no esta parcheado. provider auto solo existe en la rama: el Router vivo, por el codigo de main, daria 400 PROVIDER_UNKNOWN (no probado en vivo).
2. Router saturado: el archivo de hechos dice 503; en el codigo el 503 es solo de /chat/route (route_api.py); en /chat/send con auto cualquier RouteFailed sale como 502 con texto plano (router.py).
3. El comentario de peak.py figura como correccion de la ronda 2; ya estaba corregido en la rama desde la ronda 1 (commit 352327a4). En main sigue el comentario viejo hasta unir la rama.
4. Docstring del cortacircuitos (hecho 7 de la ronda 2): quedo a medias; su primera frase aun dice lets one probe through, y el codigo en half-open deja pasar a TODOS. La arquitectura tambien decia una prueba: corregido.
5. El salto de DeepSeek en hora pico tambien aplica al grupo minor (solo queda MiniMax), no solo a default y g2.
6. La tabla del handoff decia en T-13 que run_policy usa siempre la llave 1: incorrecto; core.key_pool expande al pool completo y Router.execute prueba las llaves por orden de salud.
7. Vercel/vercel-chat/api/chat.js llama a /chat/send con provider hf y model DeepSeek-V4-Flash fijos (no auto); y no aparece maxDuration 60 en ningun vercel.json del repo (no se consulto Vercel).
8. Cifras de pruebas: 168/8/0 (corrida 36526076292, conjunto de riu-chat-mvp-verify) frente a 153/8/6 (main, carpeta completa) NO estan reconciliadas (los 6 errores son de test_vault_wordflow_jobs, el grupo que el arreglo del puente del banco habia dejado en 0). 181 (corrida 36561019462) frente a 183 en la rama: el +2 coincide con las dos pruebas del commit 82209701. 42 pruebas de cadena en CI frente a 51 funciones test_ hoy en la rama (27+11+4 entonces; 35+12+4 ahora): la diferencia son pruebas anadidas despues, sin CI.
9. La cita de la regla del Director de las 02:06 en la arquitectura estaba parafraseada; ahora va textual, con su alcance (chat y agentes de Hermes y OpenClaw).
10. T-25: el pedido mencionaba T-11..T-25 pero ni el archivo de hechos ni el repo definen T-25; no se invento.
11. DeepSeek V4 Flash y MiniMax M3 (proveedor hf) no estan certificados: el registro model_registry.json solo certifica gpt2 y Qwen3-8B; la prueba en vivo del escalon DeepSeek(hf) se hizo en el runner CON RIU_CHAT_ALLOW_PROVIDER_LIVE=1 y HF_TOKEN_1, que el Job vivo no tiene.

## 6. Decisiones que necesita el Director (en palabras simples)
- **D1 · DeepSeek en hora pico.** Hoy el chat automatico se salta DeepSeek V4 Flash de 20:00 a 23:00 (domingo a jueves) y de 01:00 a 05:00 (lunes a viernes) hora de Bogota. Decidir si se deja asi o si se usa tambien en pico. Si no contesta: se deja como esta (se salta).
- **D2 · Grupo minor.** En el grupo minor Nemotron queda segundo (DeepSeek > Nemotron > MiniMax). Decidir si se cambia. Si no contesta: se deja como esta.
- **D3 · Grupo g2 reescrito.** Claude reescribio g2 (Kimi K3 > GLM 5.3 > Groq > local > DeepSeek > Nemotron) para dejar Nemotron ultimo. Falta su OK. Si no contesta: se deja reescrito hasta que diga otra cosa.
- **D4 · Salto directo a Groq.** Su regla de las 02:06 dice: si estan ocupadas las primeras 3 de NVIDIA, salta a la 4 o a Groq. Hoy se prueban las claves 1 a 4 dentro de cada modelo NVIDIA y luego la siguiente opcion de la cadena (GLM 5.3) antes de llegar a Groq. Confirmar si quiere el salto directo a Groq, y para el chat solo o tambien para Hermes y OpenClaw. Si no contesta: no se toca hasta que confirme.
- **D5 · Respuesta vacia.** Si un modelo contesta vacio hoy cuenta como exito: no pasa al siguiente y no se guarda en el historial. Decidir si debe contar como fallo. Si no contesta: se deja como esta.
- **D6 · Plazo total de la cadena.** No hay plazo total: con 5 opciones puede tardar de ~210 a ~450 s, y se dice que Vercel corta a los 60 s (SIN VERIFICAR). Decidir un tope total. Si no contesta: sin tope hasta que decida.
- **D7 · Tribunal de plugins.** Propuesta de Claude: pruebas automaticas primero (contrato valido, limites, sin llamadas peligrosas) y, si el plugin puede actuar afuera (escribir en GitHub, entrar por SSH, gastar), pide su OK con un boton en el panel o una orden en el chat. Falta su OK a esta propuesta. Si no contesta: se construye asi pero el OK sigue pendiente.
- **D8 · Huecos del lanzador.** El lanzador del Router no pasa HF_TOKEN_1 al Job ni pone RIU_CHAT_ALLOW_PROVIDER_LIVE=1. Sin eso el escalon DeepSeek V4 Flash fallaria. Plan: agregarlos al lanzador e informarle antes de relanzar. Si no contesta: se le informa antes de relanzar.
- **D9 · Restos de OmniRoute.** Quedan .omniroute_proxy en app.py (dentro de un try, no rompe) y .github/omniroute-relaunch.trigger. Decidir si se borran. Si no contesta: no se borran sin orden.
- **D10 · Notas de recuperacion.** Claude notas/HANDOFF-PARCHE-RECUPERACION-2026-09-21.md solo existe en la rama backup-antes-limpieza-20260929. Decidir si se restaura. Si no contesta: no se restaura sin orden.
- **D11 · Llaves de Groq.** Rotar las 7 llaves de Groq que se pegaron en un chat (accion suya). Si no contesta: pendiente suyo.
- **D12 · Vercel y direccion del Router.** Al relanzar, la URL del Router cambia y RIU_ROUTER_URL de Vercel queda vieja. NO se toca Vercel (ni el Space MCP) sin orden explicita; el despliegue final es uno solo y lo ordena el. Si no contesta: no se toca.
- **D13 · Estado de plugins entre reinicios.** El Job del Router es efimero: el estado de los plugins y el interruptor se pierden al reiniciar. Falta decidir donde se guardan (regla: todo en GitHub; HF solo puente). Si no contesta: sin resolver.

## 7. Lista roja completa 🔴
Hallazgos de las auditorías (numeración del archivo de hechos):
- 1. DeepSeek se salta en horas pico (01-04 y 06-10 UTC, lunes a viernes) en las cadenas default y g2 (en minor solo queda MiniMax) -> decision del Director.
- 2. El grupo minor deja a Nemotron segundo.
- 3. La reescritura del grupo g2 (Nemotron ultimo) necesita el OK del Director.
- 4. No hay salto directo a Groq cuando NVIDIA esta ocupada (regla 02:06): hoy solo funciona por el orden de llaves y la cadena. Hermes/OpenClaw sin tocar.
- 5. Una respuesta vacia de un modelo NO cuenta como fallo (no pasa al siguiente) -> decision.
- 6. Un fallo enfria el modelo 120 s para todos (diseno deliberado).
- 7. La cadena no tiene plazo TOTAL (hasta ~210-450 s) y se dice que Vercel tiene maxDuration 60 (no lo encontre en el repo: SIN VERIFICAR) -> decision.
- 8. El timeout HTTP es por lectura de socket, no de reloj de pared.
- 9. No hay single-flight en las llamadas a /models; /chat/router/models no tiene limite de frecuencia.
- 10. Los ids del proveedor hf (DeepSeek V4 Flash, MiniMax M3) no estan certificados y requieren RIU_CHAT_ALLOW_PROVIDER_LIVE=1 (hoy NO puesto en el Job) y HF_TOKEN_1 (hoy NO pasado al Job).
- 11. Restos de OmniRoute: .omniroute_proxy en app.py (dentro de un try) y .github/omniroute-relaunch.trigger.
- 12. Workflows temporales siguen en main (tmp-bloque1-cadena-verify.yml) -> borrar antes de terminar.
- 13. Persistencia del estado de plugins / interruptor entre reinicios del Job (el Job es efimero) sin resolver.
- 14. La UI no se toca (la opcion Automatico ya aparece en la lista del chat actual; UI final al ultimo).
- 15. La URL del Router cambia al relanzar -> RIU_ROUTER_URL de Vercel quedara vieja; NO se toca Vercel ni el Space MCP sin orden explicita.
- 16. Las rondas 1 y 2 de auditoria salieron NO LIMPIAS; se necesitan 3 rondas limpias seguidas para ✅.
Otros 🔴 vigentes: Plugin Host y Bloque 3 (3.4 y 3.5); Hermes/OpenClaw en la regla de las 02:06; autodescubrimiento por familia cuando un proveedor renombra un id (`glm-5` → `glm-5.3`); candidatos NVIDIA sin probar (`kimi-k2.6`, `nemotron-3-ultra-550b-a55b`, `nemotron-3.5-lightning-30b-a3b`); salud por (llave, modelo): una llave colgada se vuelve a aprender modelo por modelo (hasta 30 s por cada modelo nuevo); la latencia de Kimi K3 varía y el límite de 30 s puede cortar un Kimi lento pero vivo (ajustable con `RIU_CHAT_ATTEMPT_TIMEOUT`); solo NVIDIA y Groq tienen lista de modelos consultable; el modo automático no usa caché, ignora `X-Provider-Key` y devuelve `certified:false`; las 14 pruebas que ya fallaban en main (huella `fa97bc78c2a8e444`); restaurar `HANDOFF-PARCHE-RECUPERACION-2026-09-21.md`; T-11, T-14, T-17, T-18, T-19, T-21, T-22, T-23, T-24; parche de `RouterCliente`; primera frase del docstring del cortacircuitos; cambiar `provider:"hf"` en `Vercel/vercel-chat/api/chat.js` al desplegar.

## 8. Próximos pasos, en orden
1. Comprobar que la ronda 2 (subida 11:14-11:18) pasa CI: los commits llevan [skip ci], hay que lanzar el flujo temporal o el CI permanente sobre la rama y leer el resultado (🔴 sin hacer).
2. Ronda 3 de auditoria independiente sobre el codigo con la ronda 2; repetir hasta 3 rondas limpias seguidas (solo entonces ✅).
3. Terminar el Plugin Host minimo con el chat como primer plugin (otro agente lo construye) y darle pruebas; luego revisarlo (🔴).
4. Arreglos chicos pendientes: dos huecos del lanzador (HF_TOKEN_1 y RIU_CHAT_ALLOW_PROVIDER_LIVE=1), primera frase del docstring del cortacircuitos, parche de RouterCliente (provider auto y leer reply). Ninguno se hizo en este checkpoint (no se editaron .py ni workflows).
5. Decisiones del Director (D1 a D13).
6. Unir la rama bloque1-cadena-chat a main, relanzar el Router con el lanzador unico (orden 10:55), verificar /health, /chat/router/status, /chat/send con provider auto y la lista de plugins, y borrar los workflows temporales.
7. Bloque 3 (registro de fichas, compilador, agente operador, autodeteccion, gobernador de capacidad, ZIP apagado, conectores plugin, dataset Yaiwes/Control Plane).
8. Prioridad 2 (orden 11:07): DSL DAG con loops, agente orquestador, Hermes y OpenClaw en sus roles, harness DeepSeek, espejos, varias UI de chat; todo separado.
9. Despues: IA local en la maquina de 32 GB, autoescalado, cruce con lo previo de Opus (T-17/T-18), pantalla final (al ultimo, con la skill de diseno del Director).

## 9. Incidente y lección de hoy
El script local de mutaciones (`mutate2.py`) se interrumpió a las 10:55 cuando el Director rechazó la llamada y dejó UNA mutación aplicada en el árbol de trabajo local (`model_pool.py` sin el bloque del arriendo de sonda). Se detectó a las 11:1x porque las pruebas locales fallaban (3 fallos) ANTES de subir; se restauró y quedó 35/35. Nada mutado llegó al repo (el `model_pool.py` de la rama coincide con el archivo restaurado). LECCIÓN: (1) nunca correr mutaciones sobre el árbol de trabajo: en una COPIA o en CI; (2) correr las pruebas locales ANTES de cada push. (Incidente anterior, distinto: el vigilante de 32 GB que canceló el Router a las 02:15Z; ver el handoff del Router, sección 8.)

## 10. Reglas permanentes (mantener)
Sin llaves en el repo (público): solo nombres de secretos. Modelos solo por el Router único (NVIDIA hasta 4 llaves → Groq → DeepSeek V4 Flash; Nemotron ÚLTIMO); Cerebras y OmniRoute eliminados; sin APIs de Anthropic. Descargas solo por el motor de descarga/extracción. Vercel = solo UI, UN despliegue final cuando lo ordene el Director (auto-deploy OFF); no tocar ni reiniciar el Space MCP `claude-github-mcp-backup`; `keep-mcp-space-awake` sigue deshabilitado. No borrar componentes, solo reubicar. La raíz del Router debe poder moverse a otro repo. Sin código desde cero (podar, cirugía, cablear lo descargado). Respuestas cortas y en español simple; explicar el cómo antes de hacer; preguntas en texto plano (nada de widget de opciones, usa el móvil).

## 11. Cómo comprobar sin fiarte de esta nota
- Estado de subida: `git fetch origin bloque1-cadena-chat main` y comparar `git rev-parse origin/bloque1-cadena-chat:"<ruta>"` con `git hash-object "<ruta>"` de tu copia, archivo por archivo.
- Cifras de CI: abrir las corridas 36557644179, 36561019462 y 36562078042 del flujo temporal (al escribir esta nota NO se consultaron; vienen del archivo de hechos y de la arquitectura).
- Cadenas: leer `DEFAULT_POLICY` en `resilience.py` de la rama. Lanzador y huecos: leer `.github/workflows/riu-router-job-central.yml`.
- Nada de esto se ha probado en el Router vivo.
