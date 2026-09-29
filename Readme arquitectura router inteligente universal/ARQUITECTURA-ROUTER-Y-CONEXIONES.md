# ARQUITECTURA — ROUTER Y CONEXIONES (2026-09-21)

Archivo público: sin claves, contraseñas ni correos. Complementa `Claude notas/HANDOFF-PARCHE-RECUPERACION-2026-09-21.md` (estado, reglas y GAPs).
No se reescribió el README grande de esta carpeta (riesgo de corromper historial): este archivo se fusiona a él cuando se parta en tramos.

## Flujo
```
Cliente / agente (API key MAXBRY-001..100 hash-only, o RIU_AGENT_API_KEYS)
   → FastAPI  integration/chat_mvp/app.py
   → Enchufe Gate → RedUniversal   (hot-path certificado, router_hot_path.py)
   → resilience.ROUTER: concurrencia adaptativa 3→10 + cortacircuitos por clave + pool de claves
   → providers.chat(nvidia | hf | groq | deepseek | moonshot | minimax | local)   (Cerebras eliminado 2026-09-29)
Claves: banco desbloqueado en memoria (vault_hook) → entorno del servidor → cabecera BYOK (X-Provider-Key)
```

## Endpoints (todos piden `X-API-Key` salvo `/chat`, `/chat/providers`, `/vault`)
| Ruta | Para qué |
|---|---|
| `GET /chat` | Interfaz del chat (proveedor y modelo, sin agente/con agente, documentos, GitHub multi-cuenta, agentes, almacenamiento, claves) |
| `POST /chat/send` | Turno de chat por el hot-path; caché por defecto (`refresh` la salta); historial; documentos; agente; commit/repo de procedencia. Con `provider="auto"` (sin poner modelo) el Router elige el modelo con la cadena `default` (ver Resiliencia) y la respuesta trae `auto: true`, `provider`, `model` y `trace`; con cualquier otro proveedor el modelo sigue siendo obligatorio (`MODEL_REQUIRED`) |
| `POST /chat/route` | Enrutado por política: `group` = `default` \| `code` \| `minor` \| `g2`; respuesta con `route` y `trace` |
| `GET /chat/router/status` | Cadenas resueltas ahora, si es hora pico de DeepSeek, espacios de concurrencia, latencias, límite de tiempo por opción (`attempt_timeout_s`) y estado del pool de modelos (qué modelo está en enfriamiento) |
| `GET /chat/router/models` | Le pregunta de nuevo a NVIDIA y Groq qué modelos listan (red, plazo corto) y dice, por grupo, en qué orden se intentaría la cadena y qué opciones se saltan (`NOT_LISTED` / `COOLING`) |
| `POST /chat/dag/run` | Ejecuta un plan `riu.dag/v1` (Claude escribe el plan; el Router lo ejecuta) |
| `POST /chat/jobs/run` | Trabajos en paralelo por agente (tope configurable, máx. 32) con commit real a una cuenta de GitHub |
| `GET /chat/usage` | Tokens, tokens en caché del proveedor, aciertos de caché de respuestas, costo estimado (`RIU_PRICES_JSON`) |
| `/chat/agents`, `/chat/documents`, `/chat/conversations`, `/chat/graph`, `/chat/storage(/sync)` | Agentes, documentos, historial, grafo de procedencia, almacenamiento en 4 sistemas |
| `/chat/github/{accounts,whoami,repos,file,commit}` | GitHub con cuenta seleccionable (etiqueta → variable de entorno, o token por petición) |
| `/vault`, `/vault/{status,unlock,lock,credentials,rotate,import}` | Banco secreto: abrir en memoria con TTL, cargar/rotar claves, importar un banco cifrado |
| `/health`, `/v1/models`, `/v1/chat/completions` | Gateway certificado de Hugging Face (compatibilidad OpenAI) |

## Almacenamiento (RIU_DATA_DIR)
SQL (SQLite: conversaciones, mensajes, agentes) · grafo de procedencia con `valid_at` · caché de respuestas con TTL y contador de aciertos · documentos por sha256. Sincronización a un bucket de Hugging Face: implementada, probada solo con un sistema de archivos simulado.

## Resiliencia (`resilience.py`) — parámetros por defecto
- Concurrencia: 3 espacios; si hay espera ≥ 5 s sube a 10; si espera ≥ 20 s responde `ROUTER_SATURATED`.
- Cortacircuitos por clave: 3 fallos seguidos → fuera 120 s → una prueba; luego cierra o reabre.
- Sin cambio de clave: 400, 404, 410, 422.
- Hora pico de DeepSeek: 01-04 y 06-10 UTC, lunes a viernes (`Chat Mvp/router_policy/peak.py`).
- Cadenas (vigentes desde 2026-09-29, Director 05:15): `default` Kimi K3 → GLM 5.3 (NVIDIA) → DeepSeek V4 Flash → Qwen 3.8 (Groq) → Nemotron ÚLTIMO, con respaldo automático (autorizado); `g2` Kimi K3 → GLM 5.3 → Groq (`RIU_G2_GROQ_MODEL`) → local (`RIU_G2_LOCAL_MODEL`) → DeepSeek V4 Flash → Nemotron; `code` MiniMax M3 → Nemotron; `minor` DeepSeek V4 Flash → Nemotron → MiniMax M3 (en pico solo MiniMax). Un grupo SIN autorización de respaldo sigue devolviendo `NEEDS_DIRECTOR_AUTH` (409).
- Antes (2026-09-21, ya NO vale; se conserva como historial): `g2` NVIDIA → Cerebras → local → DeepSeek; `code` MiniMax M3 → NVIDIA; `minor` DeepSeek → NVIDIA → MiniMax; `default` solo NVIDIA y sin respaldo.
- Lista de modelos disponibles (`model_pool.py`): el Router le pregunta a NVIDIA y Groq qué modelos listan (caché 5 min; si el proveedor no responde o no hay clave, el modelo se INTENTA igual). Se salta una opción si el proveedor no la lista (`NOT_LISTED`) o si falló hace poco (`COOLING`, 120 s, `RIU_MODEL_COOLDOWN`). Si el filtro deja la cadena vacía se intenta la cadena completa (`POOL_EMPTY_TRY_ALL`): el pool nunca deja al chat sin ruta. Un Router saturado no cuenta como modelo muerto. El orden de prioridad es la cadena; el pool solo dice qué opciones vale la pena intentar ahora. Solo se usa en grupos con respaldo autorizado.
- Límite de tiempo por opción: cada opción de la cadena menos la última tiene `RIU_CHAT_ATTEMPT_TIMEOUT` segundos (por defecto 30, multiplicado por `max_tokens/1024` sin bajar de la base; 0 = sin límite) para que un modelo lento no bloquee el chat; la última opción conserva el plazo completo del proveedor (90 s). El límite viaja por `contextvars` (`providers.ATTEMPT_DEADLINE`) y llega hasta la llamada HTTP aunque pase por `asyncio` y hilos.
- Salud por (proveedor, clave, modelo): un modelo que se cuelga ya no pone en enfriamiento a una clave sana para los demás modelos.
- Claves NVIDIA: orden del pool `NVIDIA_API_KEY`, `_1`, `_2`, `_3`, `_4`, `_5`; la clave con fallos recientes pasa al final; si NVIDIA está ocupada la cadena sigue a la siguiente opción (Groq).
- Modelo NVIDIA de trabajo en volumen: `nvidia/nemotron-3-super-120b-a12b`.

## Variables de entorno
`RIU_CHAT_ALLOW_PROVIDER_LIVE=1` (permite intentar modelos HF no certificados) · `RIU_DATA_DIR` · `RIU_AGENT_API_KEYS` (JSON clave→agente) · `RIU_KEYSTORE_PATH` · `RIU_VAULT_PATH`, `RIU_VAULT_TTL` · `RIU_CACHE_TTL` · `RIU_PRICES_JSON` · `RIU_GITHUB_ACCOUNTS` (JSON etiqueta→variable) · `RIU_LOCAL_BASE_URL` · `RIU_G2_GROQ_MODEL`, `RIU_G2_LOCAL_MODEL` · `RIU_CHAT_ATTEMPT_TIMEOUT`, `RIU_MODEL_COOLDOWN` · `HF_BUCKET_ID`, `HF_WRITE_TOKEN` · claves de proveedor (`NVIDIA_API_KEY_1..5`, `HF_TOKEN_1`, `GROQ_API_KEY_1..7`, …): opcionales; lo recomendado es el banco.

## DSL DAG determinista (`dag.py`, esquema provisional `riu.dag/v1`)
`input_block` literal en cada nodo · executor con autoridad NONE · PASS solo por `expect` (`contains`, `not_contains`, `regex`, `json_keys`, `max_chars`, `min_chars`) · sin `expect` = `DONE_UNVERIFIED` · reintento con las comprobaciones fallidas → `escalate_to` → FAIL (dependientes BLOCKED) · ledger encadenado por hash. El método de Fables (`yaiwes.node-executor/xray-v2`, en `Claude notas/`) manda; este esquema es una aproximación a adaptar.

## Cómo probarlo
- CI: workflows `riu-chat-mvp-verify.yml` (completo + proveedores reales), `riu-nvidia-pool-test.yml` (pool, banco, fleet, jobs, resiliencia), `riu-dag-run.yml` (plan DAG real), `riu-nvidia-matrix.yml` (claves × modelos).
- Local: `cd "router inteligente universal"` y `uvicorn integration.chat_mvp.app:app --port 7860`; abrir `/chat` y `/vault`.

## 🔴 PENDIENTE de este bloque (Bloque 1, 2026-09-29) — no marcado como hecho
- 🔴 El Router en vivo (Job de Hugging Face) NO corre este código hasta que el Director ordene relanzarlo; el código importado no se recarga solo.
- 🔴 Autodescubrimiento por familia cuando un proveedor renombra un id (p. ej. glm-5 → glm-5.3): hoy la cadena usa ids fijos verificados; hay una función parecida en `agents-yaiwes/common/routes.py` (`disponibles()`) que NO se importó para no acoplar.
- 🔴 `/chat/providers` y la interfaz no muestran todavía la opción "auto" (la interfaz final se hace al final, con la habilidad de diseño del Director).
- 🔴 Ids de `hf` (DeepSeek V4 Flash, MiniMax M3) no se comprueban contra una lista: los valida la compuerta certificada (`core.hf_gate`).
- 🔴 Otros candidatos vistos en NVIDIA, NO usados hasta probarlos: kimi-k2.6, nemotron-3-ultra-550b-a55b, nemotron-3.5-lightning-30b-a3b. `z-ai/glm-5.3-flash` y `deepseek-ai/deepseek-v4.1-flash` dieron tiempo agotado en NVIDIA (no usar).
- 🔴 Vercel sigue con `RIU_ROUTER_URL` desactualizada; despliegue único solo cuando el Director lo ordene.
