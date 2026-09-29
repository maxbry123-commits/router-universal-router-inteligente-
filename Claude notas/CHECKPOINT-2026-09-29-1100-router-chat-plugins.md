# CHECKPOINT 2026-09-29 (~11:20 Bogotá, actualizado ~16:30) — Router, chat como plugin y Plugin Host
**SEGUNDA PASADA (~16:30): la sección 12 (al final) MANDA sobre lo escrito a las 11:20 si se contradice; las frases viejas afectadas llevan la marca [16:30]. El resumen en palabras simples de la segunda pasada está en 0.bis. Nada es ✅.**
Nota de checkpoint completa, escrita por el agente de notas por orden del Director (11:07: "checkpoint progresivo por si Anthropic se satura"). Regla: SINTETIZAR, NO RESUMIR; nada se marca ✅ sin evidencia; solo se escribe lo que está en el archivo de hechos del checkpoint (11:15) o lo que se verificó leyendo el repo; ninguna llave ni valor secreto (solo nombres).
Otras copias del mismo estado: `Estado y handoff global/BITACORA.jsonl` (B-0022 a B-0029), `HANDOFF.md`, `ESTADO.json` (clave `checkpoint_2026_09_29_1120`), `CRAZY_WALL.json` (nodos N-10 a N-19); detalle técnico: `router inteligente universal/HANDOFF-PROVISIONAL-ROUTER.md` (secciones 10 a 19).

## 0. En palabras simples (para el Director)
- Qué es: hay UN solo Router de modelos de IA. Todo lo demás (el chat, los agentes, las pantallas) se conecta a él; el chat es solo un plugin más (tu orden de las 10:55).
- Qué se construyó hoy: el Router ahora sabe pedir a NVIDIA y a Groq qué modelos están disponibles, recuerda cuáles dejaron de contestar y los deja descansar 2 minutos, y cuando un modelo falla pasa solo al siguiente. El orden para el chat es: Kimi K3, luego GLM 5.3, luego DeepSeek V4, luego Qwen 3.8 (Groq) y Nemotron al final. Si un modelo tarda más de 30 segundos, lo salta.
- Cómo fluye: alguien manda un mensaje al Router con la opción "automático"; el Router arma la lista de modelos disponibles, prueba el primero, y si no contesta a tiempo o da error prueba el siguiente hasta que uno responde; la conversación se mantiene aunque cambie el modelo.
- Qué está probado: el código se probó en un entorno de prueba con llaves reales y funcionó escalón por escalón; NO se ha probado en el Router que está encendido, porque ese no tiene el código nuevo todavía.
- Qué NO está listo: dos rondas de revisión independiente encontraron defectos (ya corregidos) y hacen falta tres rondas limpias seguidas para poder decir "verificado". Las últimas correcciones están subidas pero todavía no se han probado en el entorno de prueba. El Plugin Host (donde se conecta el chat como plugin) lo está construyendo otro agente. Hermes y OpenClaw no se han tocado. La pantalla va al final.
- Qué necesito de ti: las decisiones de la sección 6 (cada una explicada en simple, con lo que se hará si no contestas).

## 0.bis Actualización de las 16:30, en palabras simples
- Qué cambió: el Router ya no está solo «en construcción». Además de la cadena de modelos, ahora existe en la rama el «Plugin Host» (el sitio donde se enchufa el chat como primer plugin): tiene un interruptor para apagar el chat (si está apagado, el chat contesta «plugin chat apagado») y un modo seguro: si el host falla, el chat sigue funcionando. También se arregló el cliente que usan otros repos para hablar con el Router.
- Qué se probó: en el entorno de pruebas (corrida 36630393673) pasaron 71 pruebas de cadena y host y el conjunto de fallos viejos es EXACTAMENTE el mismo que en main, o sea no se rompió nada. Las correcciones de las 15:50 y la corrida 36631448155 todavía hay que leerlas. Nada está «verificado» (✅): dos rondas más de revisión independiente (3 y 4) encontraron defectos, sin bloqueadores.
- Qué NO cambió: el Router que está encendido sigue sin este código. Otro agente está haciendo la activación (unir la rama a main, relanzar y darle al Job el token de Hugging Face que le falta). Ojo Director: darle al Job ese mismo token que controla los Jobs es un riesgo; conviene uno solo de inferencia (decisión D14).
- Corrección de una nota mía: dije que al Job le faltaba una variable para usar DeepSeek por Hugging Face; era falso, esa variable ya la pone el Job. Solo falta el token.
- Prioridad 2 (tu orden de las 16:14: cableado y workflow, sin sobre-ingeniería): en la rama `bloque2-agentes` ya hay un DAG que puede llamar a la cadena de modelos y repetir en bucle, un generador de espejos del equipo (solo Hermes+OpenClaw o todo el equipo) y se restauraron las notas de estado viejas. Falta todavía: el grupo de asistentes con Hermes y OpenClaw apuntados al Router, la envoltura del harness de DeepSeek y las pantallas de chat apiladas.

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
- Comportamiento de errores: `/chat/route` responde 503 con `{error, trace}` (409 `NEEDS_DIRECTOR_AUTH` solo si un grupo no tuviera respaldo autorizado: hoy ninguno); `/chat/send` con `auto` responde 502 con un texto plano `CÓDIGO | traza ; traza` (≤ 900 caracteres) [16:30: salvo `ROUTER_SATURATED`, que es 503 desde la ronda 3]. Un grupo desconocido usa `default`.
Evidencia (🟡; todo de flujos temporales en el runner de CI, NO del Router vivo; cifras del archivo de hechos, no consulté las corridas):
- Corridas del flujo temporal `tmp-bloque1-cadena-verify.yml` (vive en main, blob `a86b3504`): 36557644179, 36561019462, 36562078042.
- Carpeta de pruebas completa: 183 pasan en la rama contra 153 en main; el MISMO conjunto de 14 fallos previos en las dos (huella `fa97bc78c2a8e444`: `test_vault_wordflow_jobs` 6 errores, `test_conector_*_v6` 6, `test_fast_close_global_e2e` 1, `test_huggingface_openai_chat_registry` 1) → no se rompió nada.
- 42 pruebas de la cadena pasan. Mutaciones: 27 de 28 detectadas; la sobreviviente ("respuesta vacía guardada") se cubrió con una prueba nueva en `test_resilience.py` (blob `ddc69404`), que necesita FastAPI y de la que no consta corrida propia (🟡).
- En vivo con llaves reales (runner): cadena escalón por escalón OK (Kimi → GLM → DeepSeek(hf) → Qwen (Groq) → Nemotron) y `/chat/send` con `provider:"auto"` mantiene la conversación. Kimi K3 respondió lento hoy (25–30 s en 2 de 3 intentos): el Router lo salta tras 30 s y lo recuerda 2 min. El escalón DeepSeek(hf) se probó con `RIU_CHAT_ALLOW_PROVIDER_LIVE=1` y `HF_TOKEN_1` puestos en el runner, cosas que el Job vivo no tiene.
Estado de subida de las correcciones de la ronda 2 (HISTÓRICO de las 11:33; sustituido por la tabla de la sección 12.B) (comprobado con `git fetch` al escribir):
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
- [16:30 CORREGIDO: el Job SÍ pone `RIU_CHAT_ALLOW_PROVIDER_LIVE=1` (`router_job_persistent.py:74`); solo falta `HF_TOKEN_1`; otro agente hace la activación, ver 12.H.] Huecos verificados en el lanzador (texto de las 11:20): no pasa `HF_TOKEN_1` al Job (los secretos del Job son solo `GITHUB_TOKEN`, `RIU_ROUTER_API_KEY`, `RIU_AGENT_API_KEYS`, `NVIDIA_API_KEY_1..4`, `GROQ_API_KEY_2..7`) y no pone `RIU_CHAT_ALLOW_PROVIDER_LIVE=1` (su único `env` es `RIU_G2_GROQ_MODEL`). DeepSeek V4 Flash y MiniMax M3 (proveedor `hf`) no están certificados (el registro `model_registry.json` certifica solo `openai-community/gpt2` y `Qwen/Qwen3-8B`); sin la variable y el token la opción DeepSeek fallaría rápido y la cadena seguiría a Qwen. Plan: agregar ambos al lanzador (cambio de workflow: NO hecho) e informar al Director.
- Pasos: (1) CI verde de la rama; (2) Plugin Host mínimo con el chat como primer plugin; (3) unir a main; (4) relanzar; (5) verificar `/health`, `/chat/router/status`, `/chat/send` con `auto` y la lista de plugins; (6) borrar los workflows temporales.
- La URL cambia al relanzar: `RIU_ROUTER_URL` de Vercel quedará vieja. NO se toca Vercel ni el Space MCP `claude-github-mcp-backup` sin orden explícita.

### 3.4 Bloque 2 — Plugin Host mínimo (chat como primer plugin) — 🟡/🔴 EN CONSTRUCCIÓN [16:30 OBSOLETO: ya subido y probado en CI (🟡), ver 12.D]
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
| Cliente para otros repos | `chat router/05-AGENTES/colmena/router_cliente.py` | main (viejo) y rama (parcheado) | 🟡 parcheado en la rama [16:30; a las 11:20: 🔴 sin parche] |
| Chat en Vercel | `Vercel/vercel-chat/api/chat.js`, `Vercel/HANDOFF-VERCEL.md` | main y rama | 🔴 llama con `provider:"hf"` fijo |
| Hermes / OpenClaw | `router inteligente universal/Componentes del Router/hermes-agent/` y su código descargado | main | 🔴 sin tocar |
| Copia de respaldo / notas de Opus | rama `backup-antes-limpieza-20260929` | rama de respaldo | (protegida) |
| Código de la ronda 2 | subido a la rama (ver estado de subida en 3.1) | rama | 🟡 sin CI [16:30: ver 12.B y 12.E] |
| Plugin Host | `router inteligente universal/integration/plugin_host/`, `plugins/`, `tests/test_plugin_host.py` | rama | 🟡 [16:30] |
| Prioridad 2 (DAG con loop, espejo, notas restauradas) | rama `bloque2-agentes` | rama | 🟡 sin CI [16:30] |

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

## 6. Decisiones que necesita el Director (en palabras simples) [16:30: se añadió la D14 al final de esta lista]
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

## 8. Próximos pasos, en orden (HISTÓRICO de las 11:20; la lista vigente está en 12.J)
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

## 12. ACTUALIZACIÓN 2 — 2026-09-29 ~16:30 Bogotá (MANDA sobre lo anterior si se contradice)
Marcas: ✅ VERIFICADO (ejecutado + probado + 4 pasadas de revisión + 3 rondas limpias seguidas) · 🟡 HECHO SIN PROBAR / probado a medias · 🔴 PENDIENTE · ⛔ BLOQUEADO. **Nada está ✅.**

### 12.A. Contexto y órdenes del Director
- Contexto: la ventana de Anthropic se agotó entre ~11:50 y ~15:20 (según el archivo de hechos); el Director reanudó a las 15:26 con «intenta terminar cerrar el router y hacer los de los agentes y el chat» (textual según el archivo de hechos). Orden del Director de las 16:14 (según el coordinador; el texto literal NO está en el repo): «terminar el Router ya; chat y agentes = cableado y workflow sin sobre-ingeniería; delegar a agentes, yo solo el código».
- Fuentes de esta actualización: la «ADENDA 15:50» del archivo de hechos (manda sobre la parte de las 11:15 si se contradicen), el mensaje del coordinador de las 16:2x y lo que verifiqué leyendo la rama con `git fetch` y `git show` a las 16:30 (Bogotá). Cada afirmación que dice «comprobado» la leí en el código o en el registro de commits; las cifras de CI vienen del archivo de hechos (no consulté las corridas).
- Rondas 3 y 4 de auditoría independiente: AMBAS NO LIMPIAS, sin bloqueadores (ronda 3: 3 ALTO de documentación/activación, 5 MEDIO y 8 BAJO). Nada es ✅: faltan 3 rondas limpias seguidas y las 4 pasadas por tarea (regla de las 05:18).

### 12.B. Estado de subida de la rama `bloque1-cadena-chat` (sustituye al de las 11:33)
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

### 12.C. Correcciones hechas desde las 11:20 y notas anteriores que eran falsas
- 🟡 `ROUTER_SATURATED` = 503 también en `/chat/send` con `auto`: `router.py` líneas 243-244: `503 if busy else 502`. Las notas de las 11:20 decían 502: obsoleto. Los otros fallos de `auto` (`ROUTER_ALL_ROUTES_FAILED`, `ROUTER_NO_ROUTE_AVAILABLE`) siguen siendo 502 con texto plano (≤ 900 caracteres). En `/chat/route` sigue siendo 503 (409 solo para `NEEDS_DIRECTOR_AUTH`, hoy ningún grupo).
- 🟡 `providers._http` enmascara la llave ANTES de cortar a 160 caracteres: `providers.py` líneas 98-99 (comprobado). Límite: la máscara solo cubre la llave exacta (hallazgo f abajo) y no tiene prueba propia.
- 🟡 413 ya no enfría el modelo, no reintenta en otra llave ni abre el cortacircuitos: `resilience.py`: `NO_FAILOVER = {400, 404, 410, 413, 422}` (línea 34) y `REQUEST_ERRORS = (400, 413, 422)` (línea 243); prueba `test_a_413_too_large_is_a_request_problem_no_other_key_no_breaker_no_cooling` en `test_model_pool.py` (comprobado). Antes de esto las notas decían «400/422» y «400, 404, 410, 422».
- 🟡 `run_policy`: el `try` empieza antes de `pool.filter`: `resilience.py` líneas 274-276 (comprobado): los arriendos de sonda se devuelven siempre, pase lo que pase después.
- 🟡 Pruebas endurecidas: Prueba de espera de hueco más estricta (1,5 s / 0,6 s, umbral 1,2 s; solo según el archivo de hechos, no lo verifiqué) y prueba de arranque del host con `TestClient` (commit `665a6142`, 16:00, comprobado en el registro de commits).
- 🟡 `host.py` ya no se cae con una ficha hostil: Un JSON anidado de 200 KB (`RecursionError`) o un `timeout_ms` de 400 dígitos (`OverflowError`) solo marcan ESE plugin como inválido; un estado ilegible o anidado se ignora (`host.py` líneas 222, 238 y 249, comprobado).
- 🟡 `RouterCliente` ARREGLADO en la rama: Commit `40924286` (11:45): manda `provider:"auto"` (`router_cliente.py` línea 107), lee `reply` primero (línea 91) y muestra el detalle del error; prueba nueva `chat router/05-AGENTES/colmena/tests/test_router_cliente_live.py` (commit `3ac20597`). Sin CI ejecutado (`[skip ci]`). Antes las notas decían «sin parche»: obsoleto. 🔴 Preexistente: `test_colmena.py::test_hive_block_por_sheriff` falla igual antes y después (según el archivo de hechos; no lo ejecuté).
- 🟡 CORRECCIÓN al hecho 10: el Job SÍ pone `RIU_CHAT_ALLOW_PROVIDER_LIVE=1`: `agents-yaiwes/common/router_job_persistent.py` línea 74: `os.environ.setdefault("RIU_CHAT_ALLOW_PROVIDER_LIVE", "1")`, desde el commit `b8c8a1cb` (2026-09-23) (comprobado). Las notas de las 11:20 decían que el Job NO lo tenía: obsoleto. Lo único que falta al Job es `HF_TOKEN_1`: el lanzador de `main` (leído a las 16:24) solo le pasa `GITHUB_TOKEN`, `RIU_ROUTER_API_KEY`, `RIU_AGENT_API_KEYS`, `NVIDIA_API_KEY_1..4` y `GROQ_API_KEY_2..7`. Sin `HF_TOKEN_1` el proveedor `hf` queda NOT_CONFIGURED: DeepSeek sale de la cadena `default` (queda Kimi → GLM → Qwen → Nemotron) y `code` y `minor` quedan solo con Nemotron.

### 12.D. Plugin Host (Bloque 2) — ya subido a la rama
- Plugin Host (Bloque 2) SUBIDO a la rama (ya no «sin código»): `integration/plugin_host/{__init__,host,api}.py`, `plugins/{__init__.py, chat/{__init__.py, ficha.json, plugin.py}, thinking-modes/ficha.json, README-ROJO.md}` y `tests/test_plugin_host.py` (22 funciones `test_`). `app.py` lo monta UNA vez dentro de un `try` (líneas 38-44) y aplica la compuerta 503 «plugin chat apagado» a los routers `/chat` (`api.py` línea 26); si el host falla, el chat sigue (falla abierta, según el archivo de hechos). Chat = ON por defecto (`enabled_default: true`); `thinking-modes` = OFF (`enabled_default: false`) y sin código (placeholder: si se enciende, degrada). Ficha del chat en estado `testing`, sin firma GPG ni `tribunal_case_id` (dicho en su `nota_roja`). 🟡 hecho y probado en CI (71 pruebas de cadena+host, corrida 36630393673), NO ✅. Límite honesto: el chat sigue cableado directo en `app.py`; el «plugin chat» es hoy compuerta + estado (hallazgo i). 🔴 Sin cablear de lo de Fables: failover declarativo, presupuesto por nivel, evidencia L1–L4, hot-swap, sandbox C13; y falta el OK del Director al «tribunal».

### 12.E. CI y pruebas (cifras del archivo de hechos; no consulté las corridas)
- Flujo temporal `tmp-bloque1-cadena-verify.yml` (sigue en `main`; comprobado a las 16:24). Corridas citadas: 36627207547 (falló porque al workflow le faltaba `plugins/` en el sparse-checkout: no era fallo de código), 36628329992 y 36630393673 (la última con código ANTERIOR a las correcciones de las 15:50).
- Corrida 36630393673 (cifras del archivo de hechos; yo NO consulté las corridas): carpeta de pruebas completa en la rama 212 pasan / 8 fallan / 6 error = el MISMO conjunto que `main` (huella `fa97bc78c2a8e444`; `main` 153 pasan) → no se rompió nada; cadena + host 71 pasan / 0 fallan; mutaciones de unidad 25/25 y de rutas 14/14 detectadas; en vivo con llaves reales la cadena funciona escalón por escalón (GLM a veces tarda más de 30 s y la cadena salta a DeepSeek).
- Corrida 36631448155: la cita el coordinador; su resultado NO consta en el archivo de hechos y no la consulté → 🔴 leer su resultado antes de dar por probadas las correcciones de las 15:50.
- Las correcciones de la ronda 4 (host robusto, 413) tienen pruebas nuevas que pasan en el shim local (`test_model_pool` 36 pasan / 0 fallan; `test_plugin_host` 18 pasan + 4 saltadas por falta de FastAPI) y se vuelven a correr en CI: 🟡 hasta ver ese resultado.
- Conteo por lectura de la rama a las 16:24 (no es ejecución): `test_model_pool.py` 36, `test_resilience.py` 12, `test_nvidia_pool.py` 4, `test_plugin_host.py` 22 → 74 funciones de cadena + host (71 en la corrida citada; la diferencia de 3 no está reconciliada, seguramente pruebas añadidas después: SIN VERIFICAR); `test_chat_mvp_app.py` 13. Las cifras viejas (42 de cadena, 183 en la carpeta completa) son de antes del Plugin Host.

### 12.F. Hallazgos abiertos de la ronda 4 → 🔴 (ninguno es un cambio de código hecho)
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

### 12.G. Prioridad 2: chat + agentes (orden 11:07, reafirmada el 16:14)
- Inventario de prioridad 2 (`INVENTARIO-PRIORIDAD2.md`, 372 líneas, en el scratchpad de esta sesión, NO en el repo; lo hizo un subagente de solo lectura y no ejecutó pruebas): el DAG `riu.dag/v1` de `chat_mvp/dag.py` corre pero no tenía loops ni nodos de ruta; sheriff, juez, sentinela, guardián e investigador existen como código determinista en `chat router/05-AGENTES/gobierno/`; las fuentes de Hermes y OpenClaw están en `Componente open soure router inteligente universal/` (`hermes-agent-v2026.9.24`, `openclaw-v2026.9.6`); el puente/gateway de asistentes es UNA llamada con un prompt de rol directo a NVIDIA con una sola llave (no el agente real; la regla de las 02:06 NO está implementada); el harness de DeepSeek es solo un patrón (falta el runtime); el generador de espejo del equipo estaba MISSING/PARTIAL; las UI de chat apiladas están PARTIAL (`13-CHAT-UI-SUITE`); `chat router/03-ESTADO/` no está en `main`.
- Plan de prioridad 2 en la rama `bloque2-agentes` (cabeza `197d1fc4`, 16:23; todos los commits `[skip ci]`; NO unida a `main`; 🟡 hecho sin CI, yo no ejecuté nada): (1) DAG con nodos `route:{group}` y `loop:{until,max_iterations}` (estados PASSED / MAX_ITERATIONS / REPEATED_x3; commits `c918d4a6`, `7124c25a` con `dag_cli` aceptando `group=`, y pruebas `test_dag_route_loop.py` en `645c5eca`); (2) espejo del equipo `gobierno/espejo_equipo.py` (modos hermes_openclaw / equipo_completo, dry-run por defecto; commits `698a189f` y `3bc2cdb0`); (3) restaurar `chat router/03-ESTADO/` (9 archivos) y `Claude notas/HANDOFF-PARCHE-RECUPERACION-2026-09-21.md` desde `backup-antes-limpieza-20260929` (commits de las 16:21 a las 16:23).
- 🔴 Todavía SIN commits (comprobado en la rama a las 16:24): grupo de política `assistants` y Hermes/OpenClaw apuntados al Router (con la regla de las 02:06), envoltura del harness de DeepSeek (~20 líneas: timeout → `degraded`), varias UI de chat apiladas.

### 12.H. Activación del Router — en curso por otro agente
- Activación del Router (unir la rama a `main`, relanzar el Job y agregar `HF_TOKEN_1` a los secretos del Job): EN CURSO por otro agente (según el coordinador; no lo verifiqué). Estado del repo a las 16:24: la rama NO está unida a `main` (`git merge-base --is-ancestor` da falso); el lanzador de `main` todavía NO pasa `HF_TOKEN_1` al Job; `main` está en `9b1914e5` (commits «orch-chat P1» de las 16:11 que no son de este agente de notas). Job vivo conocido: `6abb503a6b030d633f6a2dca` (no reverificado). Al terminar esa activación hay que releer: la unión, el Job nuevo, `LIVE_URL`, `/health`, `/chat/router/status`, `/chat/send` con `provider:"auto"` y `/plugins`, y borrar los workflows temporales. Riesgos a tener presentes: hallazgos b y c (pasar el token que controla los Jobs al Job, D14).

### 12.I. Contradicciones halladas en la segunda pasada (archivo de hechos, notas de las 11:20 y repo)
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

### 12.J. Próximos pasos, en orden
1. Leer el resultado de la corrida 36631448155 y volver a correr el CI sobre la rama con las correcciones de las 15:50 (🔴).
2. Ronda 5 de auditoría independiente; para ✅ hacen falta 3 rondas limpias seguidas y las 4 pasadas (🔴).
3. Que el otro agente termine la activación: unir a `main`, `HF_TOKEN_1` en los secretos del Job (mejor un token solo de inferencia: D14), relanzar con el lanzador único, verificar y borrar los workflows temporales (🔴 en curso, no verificado por mí).
4. Arreglos chicos: primera frase del docstring del cortacircuitos, listar `test_plugin_host.py` y `plugins/` en el CI permanente (hallazgo d), endurecer el lanzador (hallazgo b), prueba de la máscara de llaves (hallazgo f), aislamiento por proceso de los plugins (hallazgo a) (todos 🔴).
5. Prioridad 2 (orden de las 16:14: cableado y workflow, sin sobre-ingeniería, delegar a agentes): terminar en `bloque2-agentes` el grupo `assistants` con Hermes y OpenClaw apuntados al Router, el envoltorio del harness y las UI de chat apiladas; luego revisar y unir (🔴).
6. Decisiones del Director D1 a D14 (D14 nueva: token solo de inferencia para el Job).
7. Bloque 3, IA local, autoescalado y pantalla final siguen como estaban (🔴).

### 12.K. Cómo comprobarlo sin fiarse de esta nota
- `git fetch origin bloque1-cadena-chat bloque2-agentes main`; comparar `git rev-parse origin/bloque1-cadena-chat:"<ruta>"` con `git hash-object "<ruta>"` archivo por archivo (la tabla B lista las rutas); `git merge-base --is-ancestor origin/bloque1-cadena-chat origin/main` dice si ya se unió.
- CI: abrir las corridas 36627207547, 36628329992, 36630393673 y 36631448155 del flujo temporal (no las consulté).
### 12.L. Decisión nueva para el Director (en palabras simples)
- **D14 · Token del Job.** Para que DeepSeek funcione por Hugging Face, al Job hay que darle un token de Hugging Face. El que se usa hoy en el lanzador es el que controla los Jobs; si se le da al Job, cualquier plugin que corra dentro del Router podría leerlo. Lo más seguro es crear uno solo de inferencia. Si no contestas: el otro agente decide al activar y se te avisa (la activación está en curso; no lo verifiqué).
