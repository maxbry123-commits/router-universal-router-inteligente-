# ANEXO A — YAIWES SECRET BANK (banco propio de claves) — v1 — 2026-09-20
Anexo de `PLAN-MAESTRO-CHAT-MVP.md`. Diseño de origen: documento adjunto 3 de `INPUT-BLOCK-06-secret-bank-stack-plan-VERBATIM.md` (textual).

INSTRUCCIÓN DEL DIRECTOR (verbatim, INPUT-06): "Realiza una manera de usar mi propio banco secreto de claves si no se puede en Github lo haces en huggueface busca la manera ya estoy cansado de cada rato la vendita clave la idea del router inteligente universal es queanejs todas mis claves secretas crea algo"

PRINCIPIO: el Router no guarda ni imprime claves. Trabaja con `credential_ref`; el Secret Broker resuelve internamente y usa la clave en el momento de la llamada. El agente recibe la respuesta, nunca la clave.
REGLA MADRE: no escribir criptografía propia. Todo sale de SQLCipher (cifrado en reposo) y Argon2id (derivación de clave). Sin GitHub Secrets ni Hugging Face Secrets como banco: Hugging Face solo es almacenamiento físico.

## Por qué el repo NO puede ser el banco
`maxbry123-commits/router-universal-router-inteligente-` es PÚBLICO. Incluso un vault cifrado allí quedaría expuesto a fuerza bruta offline de la clave maestra. El vault vive fuera de git: disco persistente/bucket privado del Space (`COMAND-CENTER-1`).

## Mapa fuente → mecanismo → gap → destino (carpeta `Chat Mvp/secret_bank/`)
| Fuente (reuso) | Mecanismo | Gap que tapa | Destino |
|---|---|---|---|
| SQLCipher (`sqlcipher/sqlcipher`, BSD-3, push 2026-09-15) vía binding Python (`sqlcipher3-binary`; verificar wheel para py3.12) | Base de datos cifrada `vault.db` | Claves hoy en variables de entorno / GitHub Secrets | `vault.py` |
| Argon2id (`argon2-cffi`) | Clave del vault derivada de la passphrase; nunca se guarda | Contraseña cada vez que se usa una API | `kdf.py` |
| Diseño del adjunto (sección 5) | Sesión: `SESSION_ID` opaco en memoria con TTL; vault abierto mientras dure | Pedir clave por llamada | `session.py` |
| Diseño del adjunto (sección 4) | Broker: `use(credential_ref, agent_id, model, route)` ejecuta la llamada; NO existe `get_secret` | Agente viendo claves / prompt injection que pide la clave | `broker.py` |
| `red/identity_pool.py` (RIU-0079, ya usa `secret_env`) | Parche: `secret_ref` resuelto por el broker, con respaldo a env mientras dure la migración | 64 identidades con claves en env | parche en `identity_pool.py` |
| `integration/huggingface/chat_executor.py` (`_call_inference`) | `token = broker.use("huggingface/primary")` en vez de `os.getenv("HF_TOKEN")` | Token HF en env del servidor | parche en `chat_executor.py` |
| `security/api_key_manager.py` (MAXBRY-001..100) | NO se toca: identidad de agentes ENTRANTES (hash-only). El banco guarda claves de proveedores SALIENTES | — | — |
| Tabla `audit` | Registro de cada uso (quién, qué ref, qué modelo, resultado; jamás el valor) | Sin trazabilidad | `audit` en el vault |

## Modelo de datos (del adjunto)
`credential_id, provider, account, encrypted_value, scope, allowed_agents, allowed_models, allowed_routes, created_at, rotated_at, expires_at, enabled`. Postgres, Graphiti y AgentDB solo guardan `credential_ref = "provider/account"`, nunca el valor.

## Entrada de claves "una sola vez"
UI del banco (panel `/vault` del chat): proveedor, nombre, API key, permisos (Router, agentes, Ask Council…) → `POST /vault/credentials` con sesión desbloqueada → el valor deja de mostrarse. Proveedores previstos: Hugging Face, NVIDIA ×4, Cerebras ×6, Groq, DeepSeek, MiniMax, Kimi, GitHub por cuenta (`github/maxbry123`, `github/abc123`, `github/planeta123`).

## Amenazas y decisiones
1. Reinicio del Space ⇒ banco bloqueado (la clave maestra solo vive en memoria). Auto-desbloqueo con un secreto del Space debilita el modelo: NO por defecto (D2).
2. Passkey/WebAuthn: sirve para abrir la sesión; derivar la clave del vault con la extensión PRF/hmac-secret no está soportado de forma universal (no verificado): MVP = passphrase + Argon2id; passkey como segundo factor después.
3. Logs y respuestas: filtro de redacción en el gateway; un test falla si un secreto aparece en cualquier salida.
4. Migración: los secretos de GitHub existentes (`HF_TOKEN_1`, `CEREBRAS_API_KEY_1..6`) siguen siendo el arranque del host hasta que el banco esté poblado; después se retiran. Hasta entonces el "ni GitHub ni HF Secrets" es objetivo, no estado.
5. Los tokens pegados por el Director en el chat (1 HF, 3 GitHub) NO se usan ni se guardan: rotar y cargar los nuevos por la UI del banco o por Settings → Secrets.

## PASS por mecanismo (test que falla antes de cablearlo y pasa después; runner real)
- `vault.db` en disco no contiene el valor en claro (búsqueda de bytes).
- Sin sesión desbloqueada, `broker.use` falla cerrado.
- Agente sin permiso sobre el `credential_ref` ⇒ denegado y auditado.
- Rotación: la clave vieja deja de funcionar; la nueva funciona sin tocar al agente.
- Sesión expirada ⇒ bloqueo; ningún secreto en logs, respuestas ni Redis.
- E2E: llamada a Kimi K3 por el gateway usando el banco en lugar de `HF_TOKEN` en env.
PARCHE: un commit por mecanismo, revertible.
