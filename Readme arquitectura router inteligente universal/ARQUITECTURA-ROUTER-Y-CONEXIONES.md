# ARQUITECTURA — ROUTER Y CONEXIONES (2026-09-21)

Archivo público: sin claves, contraseñas ni correos. Complementa `Claude notas/HANDOFF-PARCHE-RECUPERACION-2026-09-21.md` (estado, reglas y GAPs); ese archivo YA NO está en main (la limpieza del 2026-09-29 lo dejó solo en la rama de respaldo `backup-antes-limpieza-20260929`), ver 🔴 al final.
No se reescribió el README grande de esta carpeta (riesgo de corromper historial): este archivo se fusiona a él cuando se parta en tramos.

## Flujo
```
Cliente / agente (API key MAXBRY-001..100 hash-only, o RIU_AGENT_API_KEYS)
   → FastAPI  integration/chat_mvp/app.py
   → Enchufe Gate → RedUniversal   (hot-path certificado, router_hot_path.py)
   → resilience.ROUTER: concurrencia adaptativa 3→10 + cortacircuitos por clave + pool de claves
   → providers.chat(nvidia | hf | groq | deepseek | moonshot | minimax | local)   (Cerebras eliminado 2026-09-29)
En el chat, `provider="auto"` no es un proveedor más: el Router recorre la cadena `default` (más abajo) y elige el modelo turno a turno.
Claves: banco desbloqueado en memoria (vault_hook) → entorno del servidor → cabecera BYOK (X-Provider-Key)
```

## Endpoints (todos piden `X-API-Key` salvo `/chat`, `/chat/providers`, `/vault`)
| Ruta | Para qué |
|---|---|
| `GET /chat` | Interfaz del chat (proveedor y modelo, sin agente/con agente, documentos, GitHub multi-cuenta, agentes, almacenamiento, claves) |
| `POST /chat/send` | Turno de chat por el hot-path; caché por defecto (`refresh` la salta); historial; documentos; agente; commit/repo de procedencia. Con `provider="auto"` (el campo `model` se ignora) el Router elige el modelo con la cadena `default` (ver Resiliencia) y la respuesta trae `auto: true`, `provider`, `model` y `trace`; en modo automático NO hay caché de respuestas, la clave del cliente (`X-Provider-Key`) se ignora, `certified` es siempre `false`, una respuesta vacía no se guarda en el historial, y un fallo devuelve 502 con `detail = {error, trace}` (en los otros proveedores `detail` es un texto). Con cualquier otro proveedor el modelo sigue siendo obligatorio (`MODEL_REQUIRED`) |
| `POST /chat/route` | Enrutado por política: `group` = `default` \| `code` \| `minor` \| `g2`; respuesta con `route` y `trace` |
| `GET /chat/router/status` | Cadenas resueltas ahora, si es hora pico de DeepSeek, espacios de concurrencia, latencias, límite de tiempo por opción (`attempt_timeout_s`) y estado del pool de modelos (qué modelo está en enfriamiento) |
| `GET /chat/router/models` | Le pregunta de nuevo a NVIDIA y Groq qué modelos listan (red, plazo corto de 6 s por proveedor) y dice, por grupo, en qué orden se intentaría la cadena y qué opciones se saltan (`NOT_LISTED` / `COOLING`). Sigue las mismas reglas que una petición real: si el filtro deja el grupo vacío se ve `POOL_EMPTY_TRY_ALL` con la cadena completa, y un grupo sin respaldo autorizado sale con `pool_used: false` y sin saltos. Es solo un reporte: no reserva la sonda única de un modelo enfriado |
| `POST /chat/dag/run` | Ejecuta un plan `riu.dag/v1` (Claude escribe el plan; el Router lo ejecuta) |
| `POST /chat/jobs/run` | Trabajos en paralelo por agente (tope configurable, máx. 32) con commit real a una cuenta de GitHub |
| `GET /chat/usage` | Tokens, tokens en caché del proveedor, aciertos de caché de respuestas, costo estimado (`RIU_PRICES_JSON`) |
| `/chat/agents`, `/chat/documents`, `/chat/conversations`, `/chat/graph`, `/chat/storage(/sync)` | Agentes, documentos, historial, grafo de procedencia, almacenamiento en 4 sistemas |
| `/chat/github/{accounts,whoami,repos,file,commit}` | GitHub con cuenta seleccionable (etiqueta → variable de entorno, o token por petición) |
| `/vault`, `/vault/{status,unlock,lock,credentials,rotate,import}` | Banco secreto: abrir en memoria con TTL, cargar/rotar claves, importar un banco cifrado |
| `GET /chat/providers` (sin clave), `GET /chat/providers/{id}/models` | Lista de proveedores del chat: `auto` va primero (`configured` = la cadena `default` tiene alguna opción configurada ahora); `/chat/providers/auto/models` devuelve un solo seudo-modelo `auto`. El resto: catálogo real del proveedor |
| `/health`, `/v1/models`, `/v1/chat/completions` | Gateway certificado de Hugging Face (compatibilidad OpenAI) |

## Almacenamiento (RIU_DATA_DIR)
SQL (SQLite: conversaciones, mensajes, agentes) · grafo de procedencia con `valid_at` · caché de respuestas con TTL y contador de aciertos · documentos por sha256. Sincronización a un bucket de Hugging Face: implementada, probada solo con un sistema de archivos simulado.

## Resiliencia (`resilience.py`) — parámetros por defecto
- Concurrencia: 3 espacios; si hay espera ≥ 5 s sube a 10; si espera ≥ 20 s responde `ROUTER_SATURATED`.
- Cortacircuitos por (proveedor, clave, modelo): 3 fallos dentro de una misma ventana de 120 s → fuera 120 s → una prueba (si la prueba falla se reabre de inmediato, si sale bien se cierra). Un fallo más viejo que 120 s se perdona y ya no cuenta: una clave que falló una vez vuelve a ser la primera (claves 1-3 prioridad, 4 de reserva).
- Sin cambio de clave: 400, 404, 410, 422.
- Hora pico de DeepSeek: 01-04 y 06-10 UTC, lunes a viernes (verificado contra `router inteligente universal/Banco de claves/router_policy/peak.py`).
- Cadenas (vigentes desde 2026-09-29, Director 05:15): `default` Kimi K3 → GLM 5.3 (NVIDIA) → DeepSeek V4 Flash → Qwen 3.8 (Groq) → Nemotron ÚLTIMO, con respaldo automático (autorizado); `g2` Kimi K3 → GLM 5.3 → Groq (`RIU_G2_GROQ_MODEL`) → local (`RIU_G2_LOCAL_MODEL`) → DeepSeek V4 Flash → Nemotron; `code` MiniMax M3 → Nemotron; `minor` DeepSeek V4 Flash → Nemotron → MiniMax M3 (en pico solo MiniMax). Un grupo SIN autorización de respaldo sigue devolviendo `NEEDS_DIRECTOR_AUTH` (409).
- Antes (2026-09-21, ya NO vale; se conserva como historial): `g2` NVIDIA → Cerebras → local → DeepSeek; `code` MiniMax M3 → NVIDIA; `minor` DeepSeek → NVIDIA → MiniMax; `default` solo NVIDIA y sin respaldo.
- Lista de modelos disponibles (`model_pool.py`): el Router le pregunta a NVIDIA y Groq qué modelos listan (caché 5 min; se pregunta con plazo de 6 s, con como máximo 2 claves y solo con otra clave si el proveedor contestó un error HTTP; si el proveedor no responde, la lista viene vacía o no hay clave, el modelo se INTENTA igual y no se vuelve a preguntar hasta 60 s después). `hf` no tiene lista comprobada (sus ids los valida la compuerta certificada). Se salta una opción si el proveedor no la lista (`NOT_LISTED`) o si falló hace poco (`COOLING`, 120 s, `RIU_MODEL_COOLDOWN`; un valor que no sea un número finito ≥ 0 vale 120). Al terminar el enfriamiento UNA petición prueba el modelo (reserva de 30 s); las demás lo siguen saltando hasta que esa prueba conteste (vuelve a la cadena), falle (nuevo enfriamiento) o venza la reserva. Si el filtro deja la cadena vacía se intenta la cadena completa (`POOL_EMPTY_TRY_ALL`): el pool nunca deja al chat sin ruta. No cuentan como modelo muerto: un Router saturado (`ROUTER_SATURATED`) ni un error de la petición (400/422); sí cuentan 404, 429, 5xx y tiempos agotados. El orden de prioridad es la cadena; el pool solo dice qué opciones vale la pena intentar ahora. Solo se usa en grupos con respaldo autorizado.
- Límite de tiempo por opción: cada opción de la cadena menos la última tiene `RIU_CHAT_ATTEMPT_TIMEOUT` segundos (por defecto 30, multiplicado por `max_tokens/1024` sin bajar de la base y sin pasar nunca de 90 s; 0 o negativo = sin límite; un valor no numérico vale 30) para que un modelo lento no bloquee el chat; la última opción tiene UN presupuesto de 90 s (el plazo del proveedor) para todas sus claves juntas. Cuando el tiempo de una opción se acaba, sus claves restantes NO se prueban ni se marcan como falladas: la cadena sigue a la siguiente opción. El límite viaja por `contextvars` (`providers.ATTEMPT_DEADLINE`) y llega hasta la llamada HTTP aunque pase por `asyncio` y hilos. Si todo el chat depende de una sola opción (las demás están enfriadas), esa es «la última» y tiene 90 s.
- Salud por (proveedor, clave, modelo): un modelo que se cuelga ya no pone en enfriamiento a una clave sana para los demás modelos.
- Claves NVIDIA: orden del pool `NVIDIA_API_KEY`, `_1`, `_2`, `_3`, `_4`, `_5` (primero las del banco desbloqueado en memoria, luego las del entorno); la clave con fallos recientes pasa al final; si todas las claves de un modelo NVIDIA fallan, la cadena sigue a la siguiente opción (en `default`: GLM 5.3, luego DeepSeek V4 Flash, Qwen 3.8 en Groq y Nemotron al final). Regla del Director (02:06, `INPUT-BLOCK-VERBATIM-2026-09-29-director.md`): «prioridad con Nvidia; si están ocupadas las primeras 3, salta a la 4 o a Groq».
- Modelo NVIDIA de trabajo en volumen: `nvidia/nemotron-3-super-120b-a12b`.

## Variables de entorno
`RIU_CHAT_ALLOW_PROVIDER_LIVE=1` (permite intentar modelos HF no certificados) · `RIU_DATA_DIR` · `RIU_AGENT_API_KEYS` (JSON clave→agente) · `RIU_KEYSTORE_PATH` · `RIU_VAULT_PATH`, `RIU_VAULT_TTL` · `RIU_CACHE_TTL` · `RIU_PRICES_JSON` · `RIU_GITHUB_ACCOUNTS` (JSON etiqueta→variable) · `RIU_LOCAL_BASE_URL` · `RIU_G2_GROQ_MODEL`, `RIU_G2_LOCAL_MODEL` · `RIU_CHAT_ATTEMPT_TIMEOUT` (defecto 30 s), `RIU_MODEL_COOLDOWN` (defecto 120 s) · `HF_BUCKET_ID`, `HF_WRITE_TOKEN` · claves de proveedor (`NVIDIA_API_KEY_1..5`, `HF_TOKEN_1`, `GROQ_API_KEY_1..7`, …): opcionales; lo recomendado es el banco.

## DSL DAG determinista (`dag.py`, esquema provisional `riu.dag/v1`)
`input_block` literal en cada nodo · executor con autoridad NONE · PASS solo por `expect` (`contains`, `not_contains`, `regex`, `json_keys`, `max_chars`, `min_chars`) · sin `expect` = `DONE_UNVERIFIED` · reintento con las comprobaciones fallidas → `escalate_to` → FAIL (dependientes BLOCKED) · ledger encadenado por hash. El método de Fables (`yaiwes.node-executor/xray-v2`, en `Documentos del proyecto/Notas del Director (verbatim)/DSL-FABLES-yaiwes-node-executor-xray-v2.md`) manda; este esquema es una aproximación a adaptar.

## Cómo probarlo
- CI que existe hoy en main: `riu-chat-mvp-verify.yml` (pruebas del chat, autenticación y Hugging Face; sonda de permisos del token), `riu-chat-mvp-core-verify.yml` (Banco de claves), `riu-dag-run.yml` (plan DAG real). Los workflows `riu-nvidia-pool-test.yml` y `riu-nvidia-matrix.yml` que citaba la versión del 2026-09-21 NO existen ya. Las pruebas de la cadena (`tests/test_model_pool.py`, `tests/test_resilience.py`) ya están en la lista de `riu-chat-mvp-verify.yml` en la rama del bloque (entran a main con el merge) y además se corrieron con un flujo temporal (evidencia más abajo).
- Local: `cd "router inteligente universal"` y `uvicorn integration.chat_mvp.app:app --port 7860`; abrir `/chat` y `/vault`.

## Evidencia de este bloque (Bloque 1, 2026-09-29) — qué se probó y dónde
- Pruebas de la cadena: `tests/test_model_pool.py` (27, archivo nuevo) + `tests/test_resilience.py` (9, una nueva) + `tests/test_nvidia_pool.py` (4, sin cambios) → en el runner real pasan las 40 (corrida 36561019462, rama `bloque1-cadena-chat`, pruebas de FastAPI incluidas). En main esa corrida no encuentra `test_model_pool.py` porque solo existe en la rama. Toda la carpeta de pruebas: rama 181 pasan / 8 fallan / 6 errores; main 153 pasan / 8 fallan / 6 errores; el conjunto de pruebas que fallan es EXACTAMENTE el mismo en las dos (huella sha256 fa97bc78c2a8e444): esas 14 ya fallaban antes y no son de este bloque.
- Cadena real en vivo (misma corrida, claves reales del repositorio): NVIDIA lista 81 modelos (Kimi K3, GLM 5.3 y Nemotron listados), Groq lista 11 (Qwen 3.8 listado). `/chat/route` y `/chat/send provider=auto`: sano → Kimi K3 (1,6 s); Kimi marcado muerto → GLM 5.3 sin perder tiempo en Kimi; + GLM muerto → DeepSeek V4 Flash; + DeepSeek muerto → Qwen 3.8 (Groq, 0,2 s); + Qwen muerto → Nemotron; todos marcados muertos → se prueba la cadena completa (`POOL_EMPTY_TRY_ALL`) y contesta Kimi. La misma conversación se mantiene al cambiar de modelo. `/chat/providers` lista `auto` primero y `/chat/providers/auto/models` devuelve el seudo-modelo. Los mismos resultados se ven en las anotaciones de esa corrida (`B1_LIVE_*`).
- Las pruebas nuevas de `model_pool.py` y `resilience.py` se comprobaron rompiendo el código a propósito (11 roturas, las 11 detectadas por su prueba). Las de FastAPI (`/chat/providers`, `/chat/router/models`, `/chat/send auto`) solo se pueden ejecutar en el runner real; su comprobación por rotura va aparte (ver el registro del bloque en el handoff).
- Lo que NO está probado: el Router en vivo (Job de Hugging Face) no corre este código hasta que el Director ordene relanzarlo; la interfaz `chat_ui.html` no se tocó.

## 🔴 PENDIENTE de este bloque (Bloque 1, 2026-09-29) — no marcado como hecho
- 🔴 El Router en vivo (Job de Hugging Face) NO corre este código hasta que el Director ordene relanzarlo; el código importado no se recarga solo.
- 🔴 Autodescubrimiento por familia cuando un proveedor renombra un id (p. ej. glm-5 → glm-5.3): hoy la cadena usa ids fijos verificados; hay una función parecida en `agents-yaiwes/common/routes.py` (`disponibles()`) que NO se importó para no acoplar.
- 🔴 Interfaz: `chat_ui.html` no se editó. Como `/chat/providers` ya lista `auto`, la interfaz actual lo muestra como un proveedor más (con una fila de clave propia que no sirve, porque en automático se ignora `X-Provider-Key`) y sin aviso de que el campo modelo no cuenta. Pulido en la interfaz final (al final, con la habilidad de diseño del Director).
- 🔴 Ids de `hf` (DeepSeek V4 Flash, MiniMax M3) no se comprueban contra una lista: los valida la compuerta certificada (`core.hf_gate`). Esa compuerta deja pasar un modelo solo si está certificado o si `RIU_CHAT_ALLOW_PROVIDER_LIVE=1` (con descubrimiento). No se verificó el entorno del Job del Router en vivo (esa variable y el token de HF): si faltan, la opción DeepSeek falla rápido y la cadena sigue, pero conviene comprobarlo antes de relanzar.
- 🔴 Otros candidatos vistos en NVIDIA, NO usados hasta probarlos: kimi-k2.6, nemotron-3-ultra-550b-a55b, nemotron-3.5-lightning-30b-a3b. `z-ai/glm-5.3-flash` y `deepseek-ai/deepseek-v4.1-flash` dieron tiempo agotado en NVIDIA (no usar).
- 🔴 Regla del Director de las 02:06 («si están ocupadas las primeras 3, salta a la 4 o a Groq»): hoy se cumple con las claves 1→4 dentro de cada modelo NVIDIA y luego la siguiente opción de la cadena (GLM 5.3 antes de llegar a Groq). NO salta directo a Groq cuando NVIDIA está ocupada. Falta confirmar con el Director si quiere ese salto directo.
- 🔴 `g2`: Claude lo reescribió el 2026-09-29 para poner Nemotron último (Kimi K3 → GLM 5.3 → Groq → local → DeepSeek → Nemotron); falta el OK del Director.
- 🔴 Una respuesta vacía de un modelo cuenta como éxito: la cadena no pasa al siguiente y en `/chat/send` sale `empty: true` sin guardarse en el historial.
- 🔴 La salud es por (clave, modelo): una clave colgada se vuelve a aprender modelo por modelo (hasta 30 s por cada modelo nuevo antes de pasar a la siguiente opción).
- 🔴 La latencia de Kimi K3 varía: el límite por opción (30 s, `RIU_CHAT_ATTEMPT_TIMEOUT`) puede cortar a un Kimi lento pero vivo; ajustable sin tocar código.
- 🔴 Solo NVIDIA y Groq tienen lista de modelos consultable en este pool; `hf`, `deepseek`, `moonshot`, `minimax` y `local` no.
- 🔴 El modo automático de `/chat/send` no usa caché de respuestas, ignora la clave del cliente (BYOK) y siempre devuelve `certified: false`.
- 🔴 14 pruebas que ya fallaban en main y siguen fallando igual en la rama (huella fa97bc78c2a8e444): `test_vault_wordflow_jobs` (6 errores), `test_conector_*_v6` (6), `test_fast_close_global_e2e` (1) y `test_huggingface_openai_chat_registry::test_allowed_model_ids_does_not_raise_and_matches_runtime_verified` (1, y ese archivo está en la lista de `riu-chat-mvp-verify.yml`: ese flujo ya salía en rojo antes). No se tocaron.
- 🔴 `Claude notas/HANDOFF-PARCHE-RECUPERACION-2026-09-21.md` (citado al principio) ya no está en main; solo existe en la rama de respaldo `backup-antes-limpieza-20260929`. Falta decidir con el Director si se restaura.
- 🔴 Vercel sigue con `RIU_ROUTER_URL` desactualizada; despliegue único solo cuando el Director lo ordene.
