# ARQUITECTURA — ROUTER Y CONEXIONES (2026-09-21)

Archivo público: sin claves, contraseñas ni correos. Complementa `Claude notas/HANDOFF-PARCHE-RECUPERACION-2026-09-21.md` (estado, reglas y GAPs).
No se reescribió el README grande de esta carpeta (riesgo de corromper historial): este archivo se fusiona a él cuando se parta en tramos.

## Flujo
```
Cliente / agente (API key MAXBRY-001..100 hash-only, o RIU_AGENT_API_KEYS)
   → FastAPI  integration/chat_mvp/app.py
   → Enchufe Gate → RedUniversal   (hot-path certificado, router_hot_path.py)
   → resilience.ROUTER: concurrencia adaptativa 3→10 + cortacircuitos por clave + pool de claves
   → providers.chat(nvidia | hf | cerebras | groq | deepseek | moonshot | minimax | local)
Claves: banco desbloqueado en memoria (vault_hook) → entorno del servidor → cabecera BYOK (X-Provider-Key)
```

## Endpoints (todos piden `X-API-Key` salvo `/chat`, `/chat/providers`, `/vault`)
| Ruta | Para qué |
|---|---|
| `GET /chat` | Interfaz del chat (proveedor y modelo, sin agente/con agente, documentos, GitHub multi-cuenta, agentes, almacenamiento, claves) |
| `POST /chat/send` | Turno de chat por el hot-path; caché por defecto (`refresh` la salta); historial; documentos; agente; commit/repo de procedencia |
| `POST /chat/route` | Enrutado por política: `group` = `default` \| `code` \| `minor` \| `g2`; respuesta con `route` y `trace` |
| `GET /chat/router/status` | Cadenas resueltas ahora, si es hora pico de DeepSeek, espacios de concurrencia, latencias |
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
- Cadenas: `g2` NVIDIA → Cerebras (`RIU_G2_CEREBRAS_MODEL`) → local (`RIU_G2_LOCAL_MODEL`) → DeepSeek V4 Flash; `code` MiniMax M3 → NVIDIA; `minor` DeepSeek V4 Flash → NVIDIA → MiniMax M3 (en pico solo MiniMax); `default` solo NVIDIA y sin respaldo: `NEEDS_DIRECTOR_AUTH` (409).
- Modelo NVIDIA de trabajo en volumen: `nvidia/nemotron-3-super-120b-a12b`.

## Variables de entorno
`RIU_CHAT_ALLOW_PROVIDER_LIVE=1` (permite intentar modelos HF no certificados) · `RIU_DATA_DIR` · `RIU_AGENT_API_KEYS` (JSON clave→agente) · `RIU_KEYSTORE_PATH` · `RIU_VAULT_PATH`, `RIU_VAULT_TTL` · `RIU_CACHE_TTL` · `RIU_PRICES_JSON` · `RIU_GITHUB_ACCOUNTS` (JSON etiqueta→variable) · `RIU_LOCAL_BASE_URL` · `RIU_G2_CEREBRAS_MODEL`, `RIU_G2_LOCAL_MODEL` · `HF_BUCKET_ID`, `HF_WRITE_TOKEN` · claves de proveedor (`NVIDIA_API_KEY_1..5`, `HF_TOKEN_1`, `CEREBRAS_API_KEY_1`, …): opcionales; lo recomendado es el banco.

## DSL DAG determinista (`dag.py`, esquema provisional `riu.dag/v1`)
`input_block` literal en cada nodo · executor con autoridad NONE · PASS solo por `expect` (`contains`, `not_contains`, `regex`, `json_keys`, `max_chars`, `min_chars`) · sin `expect` = `DONE_UNVERIFIED` · reintento con las comprobaciones fallidas → `escalate_to` → FAIL (dependientes BLOCKED) · ledger encadenado por hash. El método de Fables (`yaiwes.node-executor/xray-v2`, en `Claude notas/`) manda; este esquema es una aproximación a adaptar.

## Cómo probarlo
- CI: workflows `riu-chat-mvp-verify.yml` (completo + proveedores reales), `riu-nvidia-pool-test.yml` (pool, banco, fleet, jobs, resiliencia), `riu-dag-run.yml` (plan DAG real), `riu-nvidia-matrix.yml` (claves × modelos).
- Local: `cd "router inteligente universal"` y `uvicorn integration.chat_mvp.app:app --port 7860`; abrir `/chat` y `/vault`.
