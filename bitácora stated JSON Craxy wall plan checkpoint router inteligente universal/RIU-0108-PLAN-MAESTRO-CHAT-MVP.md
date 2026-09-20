# RIU-0108 — PLAN MAESTRO: CHAT MVP + SECRET BANK + ALMACENAMIENTO — 2026-09-20

Contrato: `tel.workflow/v3` · `FAIL_CLOSED_LOOP`. Alcance de escritura: solo este repo (P3). Formato replicado de `agentes/Claude notas/PLAN-ANEXO-A-SKILLS-A-SCHEMA.md` y `PLAN-ANEXO-B-SEALS-MECANISMOS.md` (regla del Director, principio, regla madre, inventario, mapa, orden, PASS y PARCHE por pieza, "nunca declarar integrado porque la carpeta exista").
Input textual: `Claude notas/INPUT-BLOCK-06-VERBATIM.md` (credenciales pegadas redactadas). Mensajes 01-04 textuales: `Claude notas/INPUT-BLOCKS-01-04-VERBATIM.md`. Prioridad única: el chat. El Paso 2 y el Paso 3 no empiezan hasta cerrarlo (orden del Director).
Estado del nodo: PLAN ESCRITO, DUDAS ABIERTAS (sección 6). No se construyó código del stack en este nodo.

## 1. Confirmación: ¿todas las instrucciones están anotadas 1 a 1?
| Input | Estado antes | Estado ahora |
|---|---|---|
| 01-04b | solo "resumen fiel" (RIU-0101, RIU-0105) | textual en `INPUT-BLOCKS-01-04-VERBATIM.md` |
| 05 | textual en 3 sitios (RIU-0107) | sin cambio (fe de erratas en `REFERENCIAS-ADJUNTAS-INPUT-05-ERRATA.md`) |
| 06 (este) | no anotado | textual en `INPUT-BLOCK-06-VERBATIM.md`; aquí, trazabilidad por instrucción (sección 2) |
El README de arquitectura y esta carpeta guardan el plan y la trazabilidad, no una tercera copia del texto completo del 06 (para no crear copias divergentes); si el Director exige la copia triple, se añade.

## 2. Trazabilidad instrucción por instrucción (cita textual → dónde se atiende)
| # | Cita textual del Director | Atención |
|---|---|---|
| I-06.01 | "Añade esto a el sistema jev que te di" | `Claude notas/SISTEMA-JEV-ADICION-decider-2b-vision.md` (verificado contra HF) |
| I-06.02 | "Valida confirma que todas mis instrucciones fueron anotadas" | sección 1 |
| I-06.03 | "Tienes en secreto de Github el token secreto de HF full acceso revisa y confirma" | sección 3.1: confirmado, HF_TOKEN_1 es FULL_ACCESO |
| I-06.04 | "En main tienes para descargar Componentes ➡️📂 motor descarga y extracción copiar y pegar" | S8 |
| I-06.05 | "Graphiti → construye/consulta la memoria de conocimiento / Graphty → visualiza gráficamente" | S4.3; Graphty no se instala |
| I-06.06 | Redis: "caché de respuestas … sesiones efímeras … locks … rate limits … deduplicación … colas ligeras … TTL" | S4.2 |
| I-06.07 | "Database principal PostgreSQL estado persistente y estructurado" | S4.1 |
| I-06.08 | "FalkorDB o Neo4j backend de Graphiti" / "No kuzu ❌" | S4.3 con FalkorDB (Neo4j alternativa); Kuzu descartado |
| I-06.09 | "Graphty → nodos solo usas el backend no UI" | sin UI de Graphty |
| I-06.10 | "AgentDB = episodios + skills + patrones + memoria vectorial aprendida; Graphiti = entidades + hechos + relaciones + evolución temporal. PostgreSQL conserva IDs y referencias" | S4.1, S4.3, S4.4 |
| I-06.11 | "Lo construyes en. Github con una raíz en main solo para poner lo del chat sin emojis … ➡️📂 Chat Mvp." | S1: carpeta raíz `Chat Mvp/` (sin emoji) |
| I-06.12 | Enlaces oficiales (Graphiti, Redis, PostgreSQL, FalkorDB, Neo4j, AgentDB) | inventario, sección 5 |
| I-06.13 | "Token github cuenta Maxbry 123 / abc123 / nombre planeta 123 usa" | S5; alias sí, valores NO guardados |
| I-06.14 | "Realiza una manera de usar mi propio banco secreto de claves … ya estoy cansado de cada rato la vendita clave … crea algo" | S2 Secret Bank |
| I-06.15 | "Necesito un acceso directo al chat busca algo Open soure … cambiar de modelos y agente y … almacenar archivos" | S3 |
| I-06.16 | "Usa tu chat que pasa por router busca un chat open soure para no crearlo" | S3: la UI es OSS; el gateway del Router ya existe |
| I-06.17 | "Parte 1 📌 Adjuntos + memoria … mismo chat + panel lateral permanente 📎 Archivos / 🧠 Memoria" | S4.5-S4.7 |
| I-06.18 | "ese motor de búsqueda lo usas de 2 manera uno dentro del router como imput y dos lo usas tu … no gastas tokens" | S8: workflow del motor HECHO (5 corridas PASS) |
| I-06.19 | "Esto si va LFM2-2.6B" + corrección LFM2 vs LFM2.5 | S7; duda D6 |
| I-06.20 | "Elimina esto de la lista MiroThinker-8B / yasserrmd/Neuro-Orchestrator-8B" | S7: eliminados de `groups.yaml` |
| I-06.21 | "Si necesitas investigar usas los motores y para descargar usas los motores" | regla operativa (sección 4) |
| I-06.22 | "cada paso que das marcas y actulizas tu memoria de contexto en claude notas readme … arquitectura … Craxy wall" | S9 |
| I-06.23 | "haces un plan paso a paso y anotas todo en el Craxy wall bitácora" | este documento |
| I-06.24 | "réplica el método de trabajo Anexo A … Anexo B" | formato de este plan |
| I-06.25 | "Revisa todo y si tienes dudas definimos aclaramos y haces el plan" | sección 6 (dudas) + plan |

## 3. Hallazgos verificados hoy (evidencia)
3.1 HF_TOKEN_1 SÍ es full access sobre tu cuenta: metadatos del token (sin valores), run `35493843251`, check-run `106033244342`: cuenta `COMAND-CENTER-1`, nombre del token `FULL_ACCESO_ HUGGUEFACE`, fine-grained, permisos sobre `user:COMAND-CENTER-1`: `repo.write`, `repo.content.read`, `inference.serverless.write`, `inference.endpoints.write`, `job.write`, colecciones, webhooks, `user.billing.read`. No tiene acceso a organizaciones. No necesito otro token.
   CORRECCIÓN a RIU-0105 y RIU-0107: allí afirmé que HF_TOKEN_1 "no puede crear Spaces ni escribir repos" por leer solo la lista `global`. Era erróneo; el permiso está en el bloque `scoped`. `GAP-CHAT-DEPLOY-001` deja de depender de ti; falta el primer despliegue real para confirmarlo.
3.2 Mi conexión MCP a Hugging Face (`COMAND-CENTER-1`, OAuth) tiene scopes `read-repos`, `contribute-repos`, `jobs`, `inference-api`, pero mi herramienta `hf_fs` es solo lectura. Sí puedo escribir en el Storage Bucket montado por el conector GitHub/HF de respaldo.
3.3 Credenciales pegadas en el chat (1 de Hugging Face, 3 de GitHub): NO se usaron, NO se guardaron en repo/notas/memoria y no se repiten. Están expuestas: rotarlas ya (S0). El Secret Bank (S2) existe precisamente para que no vuelvas a pegarlas.
3.4 Motor de búsqueda del repo ejecutable sin gastar tokens del LLM: `.github/workflows/riu-websearch-run.yml` (commit `bbd76c7d`) corre `websearch_engine.py` de `➡️📂motores…/➡️📂 motor de búsqueda/` en un runner con `ddgs`. Corridas PASS (8 resultados cada una): `ws-35493826829`, `ws-35493831398`, `ws-35493834208`, `ws-35494047636`, `ws-35494051059`, publicadas en `router inteligente universal/websearch-results/`. Brave/Tavily/Serper/Firecrawl: sin secrets → GAP (solo `ddgs`). Se dispara con `POST /actions/workflows/riu-websearch-run.yml/dispatches` (campo `body`, no `params`).
3.5 Chat open source (motor de búsqueda, no LLM): Open WebUI (licencia con cláusula de marca desde v0.6.6; sin restricción hasta 50 usuarios en 30 días según su doc), conexiones OpenAI-compatibles, RAG integrado, API REST; LibreChat (MIT, `librechat.yaml` para endpoints custom OpenAI-compatibles, agentes, MCP, RAG API; requiere MongoDB y opcionalmente Redis); LobeChat (agentes, base de conocimiento; sin verificar licencia). Ambos aceptan la URL del gateway del Router como endpoint.
3.6 Docker Spaces de HF admiten adjuntar Storage Buckets como volúmenes (changelog 2026-03-31; `hf-mount` para montaje lectura/escritura de buckets). El disco del Space es efímero sin bucket.
3.7 Graphiti publica una imagen combinada FalkorDB + servidor MCP de Graphiti (puertos 6379 / 3000 UI / 8000) y configuraciones Docker Compose para FalkorDB o Neo4j. FalkorDB está basado en Redis.
3.8 Modelos: `Mapika/decider-2b-vision` existe (apache-2.0, base `Qwen/Qwen3.5-2B-Base`).

## 4. Principio y regla madre
PRINCIPIO: no se crea un chat ni un router nuevos. El chat es software libre; el Router es el gateway ya probado (`router inteligente universal/integration/huggingface/`: catálogo del selector, executor, auth MAXBRY, 36 tests en runner real). Lo nuevo es el Secret Bank, el almacenamiento y el cableado.
REGLA MADRE: REUSE > PATCH > ADAPT > GENERATE. Investigar = motor de búsqueda; descargar/extraer = motores de `➡️📂motores…`; nada de credenciales en texto plano en ningún archivo, base de datos, log o chat.
PASS por pieza: un test que falla antes y pasa después, en runner real, con evidencia (ruta + SHA + run id + read-back). PARCHE: cada Salida es un commit independiente y revertible. Copiar fuentes no es integrar.

## 5. Inventario de fuentes
- Gateway/UI mínima ya en `main`: `chat_catalog.py`, `chat_executor.py`, `chat_ui.html`, `fastapi_gateway.py`, `keystore_auth.py`, `api_key_auth.py`; workflow `riu-chat-mvp-verify.yml`.
- Motores: búsqueda, `hf_download_extract_engine.py`, `motor_2_queue_download_extract.py`, `motor_1_extract_only.py`, copia y movimiento (`➡️📂motores de descarga extracción copiado movimiento archivos router-universal-router-inteligente-/`).
- Externos (oficiales, según el Director): Graphiti `getzep/graphiti` (`graphiti-core[falkordb]`), FalkorDB `FalkorDB/FalkorDB`, Neo4j (alternativa), Redis `redis/redis`, PostgreSQL, AgentDB `ruvnet/agentdb` (npm `agentdb`), Graphty (NO se instala).
- Chat OSS candidato: Open WebUI o LibreChat (duda D1).

## 6. Dudas a resolver antes de construir (definimos y aclaramos)
D1. Chat: Open WebUI (recomendado: un solo contenedor, encaja en un Space Docker, RAG y Pipelines en Python para encadenar el almacenamiento; ojo a la cláusula de marca) o LibreChat (MIT, agentes y MCP más completos, pero exige MongoDB + servicios extra).
D2. Dónde corren PostgreSQL, Redis, FalkorDB y AgentDB: (A) dentro del Space Docker con bucket como volumen; (B) servicios gratuitos externos + Space; (C) un VPS. Mi criterio de ingeniería (no verificado con fuente): Postgres y FalkorDB sobre un bucket montado (almacenamiento de objetos) son frágiles; con (A) haría volcados periódicos al bucket y guardaría solo los archivos y el vault cifrado allí.
D3. Secret Bank: cifrado AES-256-GCM por valor dentro de SQLite, clave derivada con scrypt de tu contraseña maestra, en vez de SQLCipher (que necesita un binario nativo; para claves API el nivel de seguridad es equivalente y se puede cambiar después). Passkey/WebAuthn en una segunda fase. Copia cifrada en un repo privado de HF (`COMAND-CENTER-1/yaiwes-secret-bank`). ¿Aprobado?
D4. Bootstrap del banco: para desplegar hace falta un token en CI. ¿Puedo dejar `HF_TOKEN_1` como secret de GitHub solo para el despliegue y que todo lo demás viva en el banco?
D5. Cuentas de GitHub: ¿logins exactos? (`Maxbry 123` → ¿`maxbry123-commits`?, `abc123`, `planeta 123`). Por defecto, lectura hasta que actives escritura por cuenta.
D6. LFM2-2.6B (lo pediste) vs LFM2.5-2.6B (nueva generación): ¿registro ambos o solo uno?
D7. Modelos sin proveedor (RIU-0107 decisión 1): ¿locales ≤26 GB en qué máquina, NVIDIA/Cerebras, o Endpoint dedicado?
D8. Pool de agentes: lista (id, rol, grupo, modelo) o plantilla inicial de 6.
D9. Embeddings para Graphiti/AgentDB y LLM que usará Graphiti para extraer entidades (propuesta: el gateway del Router).

## 7. PLAN POR SALIDAS
Destino de todo lo nuevo: carpeta raíz `Chat Mvp/` (sin emoji). PASS/PARCHE en cada una.

### S0 — Seguridad inmediata (sin código del stack)
0.1 Rotar los 4 tokens pegados (Director). 0.2 `.github/workflows/riu-secret-scan.yml`: falla si aparece un patrón de credencial (`hf_`, `ghp_`, `github_pat_`, `sk-`, `nvapi-`, `csk-`) en el repo. PASS: test del patrón + repo limpio en runner. PARCHE: un archivo.

### S1 — Raíz `Chat Mvp/`
README (mapa y estado), `groups.yaml` (grupos 0/1/2 con las listas ACTUALIZADAS: sin MiroThinker-8B ni yasserrmd/Neuro-Orchestrator-8B; runtime por modelo), `accounts.yaml` (solo alias, nunca tokens). PASS: read-back + test de validación YAML.

### S2 — YAIWES Secret Bank (resuelve "cada rato la vendita clave")
2.1 `secret_bank/vault.py`: SQLite + AES-256-GCM/scrypt; campos del documento (provider, account, scope, allowed_agents, allowed_models, allowed_routes, created_at, rotated_at, expires_at, enabled). 2.2 `session.py`: login una vez → sesión con TTL; la clave derivada solo en memoria. 2.3 `broker.py`: `resolve(credential_ref, agent, model, route)`; devuelve el secreto solo al ejecutor interno; audita sin valores. 2.4 `api.py`: `/bank/unlock|lock|credentials|rotate|disable|audit` (nunca devuelve valores). 2.5 gateway: `credential_ref` reemplaza `HF_TOKEN` (fallback a variable de entorno mientras dure la migración). 2.6 página `/bank` (alta una vez; lista sin valores). 2.7 copia cifrada del vault al repo privado de HF con HF_TOKEN_1 (`repo.write` ✔). 2.8 passkey/WebAuthn (fase 2).
PASS: tests de cifrado (el archivo no contiene el valor), contraseña incorrecta falla, permisos por agente/modelo/ruta, auditoría sin valores, rotación, restauración desde la copia. PARCHE: un commit por pieza.

### S3 — Chat open source sobre el Router (acceso directo)
3.1 Elegir D1. 3.2 `deploy/Dockerfile` + `entrypoint.sh`: gateway + UI en un Space Docker, la UI apunta a `http://127.0.0.1:<puerto>/v1`. 3.3 Selector = modelos del Router (`/v1/models` ampliado con las familias del selector) + agentes como presets (D8). 3.4 `.github/workflows/riu-chat-deploy.yml`: `create_repo(space, docker, private)` + `upload_folder` + volumen de bucket, con HF_TOKEN_1. 3.5 verificación en runner: `/health`, `/v1/models`, una completion por Kimi K3 / DeepSeek V4 Flash / V4 Pro / MiniMax M3 a través de la UI o su API. Sin claves en la imagen: las lee del banco (S2) o, mientras tanto, de variables del Space.
PASS: URL del Space + E2E en runner. PARCHE: el Space se puede borrar sin tocar el repo.

### S4 — Almacenamiento (4 sistemas + Redis) y adjuntos
4.0 Cerrar D2. 4.1 PostgreSQL: `storage/postgres/schema.sql` (usuarios, agentes, proyectos, conversaciones, archivos, vínculos de memoria, `credential_ref`, auditoría). 4.2 Redis: `storage/redis_layer.py` (caché, resultados de búsqueda repetidos, sesiones efímeras, locks, rate limits, deduplicación, estado de workers, colas ligeras, TTL). Solo referencias, jamás secretos. 4.3 FalkorDB + Graphiti (`graphiti-core[falkordb]`, imagen combinada oficial). 4.4 AgentDB (Node, MCP). 4.5 Ingestion Router: subida → archivo original al bucket → parser → chunks → Postgres (metadata) + AgentDB (semántica/episodios) + Graphiti (entidades/hechos) + Redis (caché); ids `project_id, conversation_id, memory_id, file_id, file_version, file_hash, chunk_id, source_uri, created_at`. 4.6 Tres niveles de memoria: CHAT / PROJECT / GLOBAL. 4.7 Panel lateral 📎 Archivos / 🧠 Memoria. 4.8 Recuperación → contexto del Router.
PASS: healthcheck de cada servicio + ida y vuelta; E2E: subir un archivo, verlo en el panel, abrir un chat nuevo del mismo `project_id` y recuperarlo; escaneo que demuestre cero credenciales en Postgres/Graphiti/AgentDB/Redis. PARCHE: un servicio por commit.

### S5 — Selector de cuentas de GitHub
`accounts.yaml` (alias) + `credential_ref = github/<alias>` + broker. Por defecto solo lectura; lista blanca de repos por cuenta. PASS: `GET /user` por alias a través del broker sin exponer el token; una escritura sin el permiso activado es rechazada.

### S6 — Con agente / sin agente
`agents.yaml` (D8) + parámetro `agent` en el Router (grupo, modelo, herramientas, `credential_ref`). PASS: mismo prompt con y sin agente sigue rutas distintas y la auditoría registra el `agent_id`. Los 50+ agentes "Seals Team YAIWES" con las keys MAXBRY son del Paso 3.

### S7 — Modelos por grupo en el selector
`groups.yaml` gobierna el selector; solo aparecen modelos con `runtime` verificado (auditoría del catálogo HF del 2026-09-20). Lo que ningún proveedor sirve queda `PENDING` hasta cerrar D7. La cascada del grupo 2 (NVIDIA/Cerebras → API locales → DeepSeek V4 Flash) y el salto de 3 a 7 a 10 procesadores son del Paso 3.

### S8 — Motores
8.1 Búsqueda: HECHO (workflow, 5 corridas PASS). 8.2 Exponerla dentro del Router como entrada (ruta `/research`): Paso 3. 8.3 Descarga/extracción: usar `hf_download_extract_engine.py` en HF Jobs (`job.write` ✔) solo si hace falta traer fuentes; para Graphiti/AgentDB/Open WebUI se prefieren paquetes e imágenes oficiales.

### S9 — Memoria y sincronización
Tras cada Salida: `Claude notas/`, `Readme arquitectura…/`, esta carpeta de bitácora y `STATE/CHECKPOINT/PLAN/Handoff`. La bitácora principal sigue sin este nodo (archivo propio por el límite de reescribir 33 KB); proponer la partición por tramos.

## 8. Orden de ejecución
S0 → S1 → S2.1-2.4 (Secret Bank funcional) → S3 (chat en línea, acceso directo) → S4 (Postgres → Redis → ingestión básica → AgentDB → Graphiti/FalkorDB) → S5 → S6 → S7. S9 en cada paso. Motivo: primero acabar con la fatiga de las claves, después tener el chat en línea, después los adjuntos.

## 9. GAPs
`GAP-SECRET-BANK-001`, `GAP-CHAT-OSS-CHOICE-001` (D1), `GAP-STORAGE-HOSTING-001` (D2), `GAP-STORAGE-MVP-001` (4 sistemas + Redis + adjuntos), `GAP-GH-MULTIACCOUNT-001`, `GAP-AGENT-POOL-001`, `GAP-MODELS-NO-PROVIDER-001`, `GAP-EXPOSED-CREDENTIALS-001` (rotar), `GAP-SEARCH-KEYS-001` (solo ddgs). Cerrado en principio: `GAP-CHAT-DEPLOY-001` (falta despliegue real).
