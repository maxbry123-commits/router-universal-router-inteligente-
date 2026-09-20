# PLAN MAESTRO — CHAT MVP (Router Inteligente Universal) — v1 — 2026-09-20

Método replicado de `agentes/Claude notas/PLAN-ANEXO-A-SKILLS-A-SCHEMA.md` y `PLAN-ANEXO-B-SEALS-MECANISMOS.md`: instrucción del Director citada textual con su fuente, regla madre, mapa fuente → mecanismo → gap → destino, orden de ejecución, PASS por fase, parche independiente y revertible.
Anexos de este plan: `PLAN-ANEXO-A-SECRET-BANK.md`, `PLAN-ANEXO-B-STORAGE-Y-CHAT-OPEN-SOURCE.md`. Sistema Jev: `SISTEMA-JEV-COMPONENTES.md`.
Estado: BORRADOR v1 con decisiones abiertas (sección 5). No se ejecuta la Fase 1 en adelante hasta que el Director las cierre o diga "defaults".

## 1. Instrucciones del Director que gobiernan el plan (textuales; fuente entre corchetes)
- "Después todo lo demás la prioridad CHat tu objetivo principal" [INPUT-05]
- "Hasta que no termines esto no pasas a paso 2" [INPUT-05]
- "Usa tu chat que pasa por router busca un chat open soure para no crearlo" [INPUT-06]
- "la idea del router inteligente universal es queanejs todas mis claves secretas crea algo" [INPUT-06, sic]
- "Realiza una manera de usar mi propio banco secreto de claves si no se puede en Github lo haces en huggueface" [INPUT-06]
- "Lo construyes en. Github con una raíz en main solo para poner lo del chat sin emojis es solo para explicar ➡️📂 Chat Mvp." [INPUT-06] → raíz nueva `Chat Mvp/` en `main`.
- "Si necesitas investigar usas los motores y para descargar usas los motores" [INPUT-06]
- "cada paso que das marcas y actulizas tu memoria de contexto en claude notas readme y lo que vas cerrando en ➡️📂 arquitectura router inteligente universal ➡️ ... haces un plan paso a paso y anotas todo en el Craxy wall bitácora stated JSON handoff" [INPUT-06]
- "📌 Elimina esto de la lista MiroThinker-8B yasserrmd/Neuro-Orchestrator-8B" [INPUT-06]
- Stack de datos: PostgreSQL + Redis + AgentDB + Graphiti sobre FalkorDB; "No kuzu"; Graphty solo backend/no UI [INPUT-06]

## 2. Regla madre
R1. REUSE > PATCH > ADAPT > GENERATE. Prohibido escribir desde cero lo que ya existe: chat open source, Graphiti, FalkorDB, SQLCipher, AgentDB, gateway HF, keystore MAXBRY, `identity_pool.py`, motores de búsqueda/descarga.
R2. Ningún secreto entra al repo (es PÚBLICO). Solo referencias (`credential_ref`). Los tokens pegados en el chat se consideran expuestos: rotar.
R3. PASS solo con evidencia de runner real (annotations de check-run, run id) — como RIU-0105/0107. Un test escrito no es un test ejecutado.
R4. Un mecanismo = un commit independiente y revertible. Nunca declarar integrado algo porque la carpeta exista.
R5. Investigar con el motor de búsqueda del Router (workflow `riu-websearch.yml`, sin tokens de LLM); descargar con los motores de descarga/extracción de `➡️📂motores de descarga extracción copiado movimiento archivos…`.
R6. Escribir solo en este repo (P3). Otros repos, solo lectura.
R7. El agente nunca ve una API key: el Router pide `credential_ref`, el Secret Broker resuelve (Anexo A).

## 3. Estado de partida (verificado en esta sesión)
| Hecho | Evidencia |
|---|---|
| Chat sobre el Router con selector Kimi K3 / DeepSeek V4 Flash+Pro / MiniMax M3 funciona por HTTP | run `35489744898`, 36 tests passed, E2E 200 |
| 100 keys MAXBRY-001..100 (solo hashes) aceptadas por el gateway | `test_keystore_auth.py` (36 passed) |
| `HF_TOKEN_1` = token fine-grained de `COMAND-CENTER-1` con `repo.write`, `job.write`, `inference.serverless.write`, `inference.endpoints.write`, `collection.write`, `discussion.write`, webhooks | run `35493036087` (RIU_HF_SCOPES) → CORRIGE lo dicho antes ("no puede crear Spaces"): SÍ puede escribir repos/Spaces y lanzar Jobs |
| Motor de búsqueda del Router corre y devuelve resultados (ddgs, 8/8, sin LLM) | run `35493077904` (RIU_SEARCH_1..3) |
| Catálogo router HF: 138 modelos; sirven Qwen3.5-9B, Muse-Glimmer-30B, Granite 4.2, Gemma 4, Ling 3.0, DeepSeek V4, Kimi K3, MiniMax M3 | run `35489878690` |
| Decider-2B-Vision existe: Apache-2.0, base Qwen3.5-2B-Base, updated 2026-09-17 (105 descargas) | run `35493036087` (RIU_HUB) |
| Secrets del repo: `CEREBRAS_API_KEY_1..6`, `HF_TOKEN_1`, `RIU_GITHUB_PAT_FULL_ACCESO`. Faltan: NVIDIA ×4, DeepSeek directa, tokens de las 3 cuentas GitHub | listado API |

## 4. Fases (orden de ejecución) — cada fase con PASS y parche independiente
| Fase | Qué | Reusa | PASS (evidencia de runner) |
|---|---|---|---|
| F0 | Registro verbatim de los 6 input blocks; seguridad de tokens pegados | — | Blocks 01-06 en `Claude notas/` (hecho); tokens rotados por el Director |
| F1 | Chat accesible ("acceso directo"): Space Docker privado en `COMAND-CENTER-1` que sirve el gateway del Router + `/chat` | `fastapi_gateway.py`, `chat_ui.html`, keystore; Dockerfile con `git clone --sparse` de este repo | `GET /health` 200 y `POST /v1/chat/completions` con key MAXBRY 200 sobre la URL del Space |
| F2 | Chat open source (Open WebUI recomendado) apuntando al Router: selector de modelos y "agentes" como presets, adjuntos | Open WebUI (Anexo B) | Modelo elegido en la UI responde vía Router; con y sin agente; adjunto cargado |
| F3 | Secret Bank: SQLCipher + sesión + broker + `credential_ref`; el Router deja de leer claves de env | `identity_pool.py` (`secret_env`), SQLCipher, argon2 | Tests: cifrado en disco, sin secreto en logs/respuestas/Redis, permiso denegado, rotación, sesión expirada bloquea |
| F4 | Almacenamiento: PostgreSQL + Redis + Graphiti/FalkorDB + AgentDB + ingestión de adjuntos + memoria chat/proyecto/global | Graphiti MCP server oficial + FalkorDB docker; Open WebUI `DATABASE_URL`/`REDIS_URL` | Un archivo adjunto queda en los 4 sistemas y se recupera en un chat nuevo (project_id) |
| F5 | Selector de cuenta GitHub (3 cuentas) vía broker (`github/<alias>`), lectura por defecto | Secret Broker | Cambiar de cuenta en la UI cambia el actor; escritura denegada sin permiso |
| F6 | Grupos 0/1/2, cascada NVIDIA/Cerebras → locales → DeepSeek V4 Flash, saturación 3→7→10, enjambre 50+ | `hf_scheduler.py`, `identity_pool.py`, Anexo de modelos | Prueba de carga con ≥50 keys efímeras |
| F7 | Los 3 métodos (Council, Code chain, Jev-like) | Documentos adjuntos INPUT-05 | (Paso 3 del Director; no antes de cerrar el chat) |

Regla de orden: F1 → F2 → F3 → F4 → F5; F6 y F7 solo después de que el Director declare cerrado el chat (INPUT-05).

## 5. Decisiones abiertas (definir antes de F1/F2)
D1. Dónde corren PostgreSQL, Redis y FalkorDB. Un Space Docker es un solo contenedor y su disco no persiste sin almacenamiento de pago; GitHub Actions es efímero. Opciones: (a) todo en el Space con `supervisord` + almacenamiento persistente de HF; (b) servicios gratuitos externos (Neon Postgres, Upstash Redis, FalkorDB Cloud); (c) tu VPS. Recomendación por costo cero: (b) para Postgres y Redis, y FalkorDB en (a) o (b) según el tamaño.
D2. Clave maestra del Secret Bank: passphrase + Argon2id ahora, passkey/WebAuthn después. Un reinicio del Space cierra el banco (la clave vive solo en memoria): hay que desbloquear tras cada reinicio.
D3. Chat: Open WebUI (un contenedor, Postgres + Redis nativos, licencia propia con cláusula de marca) vs LibreChat (MIT, agentes de primera clase, pero exige MongoDB). Recomendación: Open WebUI (encaja con "PostgreSQL = verdad").
D4. Lista de modelos: ¿LFM2-2.6B o LFM2.5-2.6B como worker del Grupo 1? (Hub: ambos existen; LFM2.5 es la nueva generación). Con MiroThinker-8B y Neuro-Orchestrator-8B eliminados, el Grupo 0 queda con LFM2.5-8B-A1B y OpenThinker3-7B + Command Center: ¿correcto?
D5. Cuentas GitHub: alias y permiso lectura/escritura por cuenta (por defecto lectura hasta que se active escritura).
D6. AgentDB (`ruvnet/agentdb`) tiene poca adopción (89 estrellas, último push 2026-07-30). ¿Se acepta el riesgo o se busca alternativa para "memoria de agentes"?

## 6. Correcciones a lo dicho antes en esta sesión
- "Mi token de HF no puede crear Spaces" era ERRÓNEO: solo miré los permisos globales; el token tiene `repo.write` sobre el namespace del usuario. `RIU-0105` y `RIU-0107` repiten esa conclusión y quedan corregidos por esta nota.
- Solo el INPUT BLOCK 05 estaba verbatim; los bloques 01-04 estaban resumidos. Corregido (ver `INPUT-BLOCKS-01-04-VERBATIM.md`).
- `REFERENCIAS-ADJUNTAS-INPUT-05-VERBATIM.md` contiene una frase duplicada (ver `…-ERRATA.md`).

## 7. Próximo delta seguro (cuando el Director confirme D1-D6 o diga "defaults")
F1: workflow `chat-mvp-deploy-space.yml` que, con `HF_TOKEN_1` (nunca impreso), crea el Space Docker privado, sube `Dockerfile` + `README.md` (YAML `sdk: docker`, `app_port: 7860`), fija variables/secretos del Space y comprueba `/health`. Raíz `Chat Mvp/` con el Dockerfile y la guía.
