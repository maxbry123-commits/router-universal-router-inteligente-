# ANEXO B — ALMACENAMIENTO (4 SISTEMAS) + CHAT OPEN SOURCE — v1 — 2026-09-20
Anexo de `PLAN-MAESTRO-CHAT-MVP.md`. Fuentes: `INPUT-BLOCK-06-…-VERBATIM.md`, metadatos de GitHub (run `35493036087`? no: run del job `RIU_REPOS`, check-run `106030864774`) y búsquedas con el motor del Router (run `35493077904`).

INSTRUCCIONES DEL DIRECTOR (verbatim, INPUT-06): "Usa tu chat que pasa por router busca un chat open soure para no crearlo" · "No necesitas crear otro chat. Mantendría el mismo chat, pero añadiría una ventana/panel persistente de Archivos / Memoria." · "No kuzu ❌ Para proyectos nuevos recomienda Neo4j o FalkorDB" · "GRAPHTY → NO necesario si vas backend-only"

REGLA MADRE: no crear otro chat. Se adopta uno de código abierto y se apunta al Router.

## B1. Elección del chat (evidencia)
| Candidato | Estrellas | Licencia (GitHub) | Último push | Encaje |
|---|---|---|---|---|
| Open WebUI `open-webui/open-webui` | 152,590 | NOASSERTION (licencia propia con cláusula de marca; leer texto) | 2026-09-19 | Conecta a cualquier endpoint OpenAI Chat Completions con URL + API key (docs); cambio de modelo; subida de archivos y bases de conocimiento (`/api/v1`); modelos personalizados (preset con prompt/herramientas) |
| LibreChat `danny-avila/LibreChat` | 44,424 | MIT | 2026-09-20 | Endpoints propios por `librechat.yaml`; Agents con cualquier proveedor; MCP; subida de archivos; RAG; requiere MongoDB |
| LobeHub `lobehub/lobehub` | 82,668 | NOASSERTION | 2026-09-20 | No evaluado a fondo |
| AnythingLLM `Mintplex-Labs/anything-llm` | 66,234 | MIT | 2026-09-19 | No evaluado a fondo |
| Onyx `onyx-dot-app/onyx` | 32,175 | NOASSERTION | 2026-09-19 | No evaluado a fondo |
RECOMENDACIÓN: Open WebUI. Motivo: un solo contenedor (encaja en un Space Docker) y soporta PostgreSQL y Redis como respaldo (a verificar en su documentación), que es el stack pedido; LibreChat obligaría a MongoDB y contradice "PostgreSQL = verdad". Riesgo declarado: licencia propia; alternativa MIT = LibreChat (D3).

## B2. Contrato de integración chat ↔ Router
- Chat → `POST {router}/v1/chat/completions` con `Authorization: Bearer riu_MAXBRY-NNN_…` (gateway existente, RIU-0105).
- Router → `GET /v1/models` debe listar los modelos del selector. HOY lista solo los 3 "certificados"; el catálogo con estados está en `/chat/models`. PARCHE: `/v1/models` devuelve también los seleccionables cuando `RIU_CHAT_ALLOW_PROVIDER_LIVE=1`.
- "Agente" = modelo personalizado del chat (prompt + herramientas + conocimiento) que llama al modelo real por el Router; "sin agente" = modelo crudo. La identidad del agente viaja en la key MAXBRY.
- Fallback: `/chat` del gateway (ya construido) queda como chat mínimo.

## B3. Los 4 sistemas de almacenamiento (reuso, no construir)
| Sistema | Función (del Director) | Reuso | Nota |
|---|---|---|---|
| PostgreSQL | Verdad / estado / IDs / tareas / auditoría / referencias | `DATABASE_URL` de Open WebUI + tablas propias (files, projects, memory_refs, credential_refs) | |
| Redis | Caché, TTL, sesiones, locks, colas, rate limits, deduplicación | `REDIS_URL` de Open WebUI + claves propias | Sin secretos en Redis (Anexo A) |
| Graphiti + FalkorDB | Entidades, hechos, relaciones, evolución temporal | `getzep/graphiti` (Apache-2.0, 31,021★) con `graphiti-core[falkordb]`; servidor MCP oficial con Docker Compose y FalkorDB (docs FalkorDB); `docker run … falkordb` para arrancar | FalkorDB: GitHub marca licencia NOASSERTION (verificar términos); NO Kuzu; Graphty NO se instala |
| AgentDB | Episodios, skills, patrones, memoria vectorial | `ruvnet/agentdb` (npm) con integración MCP | Poca adopción (89★, push 2026-07-30): D6 |

## B4. Ingestión de adjuntos (flujo del Director)
Adjunto → ROUTER DE INGESTIÓN → (original a almacenamiento de objetos) + parser → chunks → {Postgres: metadatos, AgentDB: memoria semántica, Graphiti: entidades/hechos → FalkorDB} → Redis (caché) → recuperación → Router → LLM/agentes.
Anclas por archivo: `project_id, conversation_id, memory_id, file_id, file_version, file_hash, chunk_id, source_uri, created_at`. El chat solo guarda referencias, no es la base de datos.
Tres niveles en la interfaz: CHAT MEMORY (esta conversación), PROJECT MEMORY (todos los chats del proyecto), GLOBAL MEMORY (agentes autorizados). Panel lateral permanente "Archivos / Memoria".
Mecanismo de enganche en el chat: función/filtro del propio chat sobre la subida de archivos (a confirmar en la doc del chat elegido).

## B5. Hospedaje (decisión D1)
Un Space Docker = 1 contenedor en el puerto 7860; su disco no persiste sin almacenamiento de pago; GitHub Actions no sirve como host (efímero). Opciones: (a) todo en el Space con `supervisord` + almacenamiento persistente de HF; (b) Neon (Postgres) + Upstash (Redis) gratuitos + FalkorDB en (a); (c) VPS propio. Recomendación de costo cero: (b).

## B6. PASS por sistema (runner real)
- Chat: modelo elegido en la UI responde vía Router; con y sin agente.
- Postgres: el chat guarda conversación y metadatos de archivo; sobrevive a un reinicio.
- Redis: sesión y límite de tasa observables; TTL cumple.
- Graphiti/FalkorDB: un documento produce entidades y hechos consultables.
- AgentDB: un episodio se guarda y se recupera por similitud.
- E2E: archivo adjunto en un chat, chat nuevo del mismo proyecto lo recupera.

## B7. Pendiente de verificar (marcado, no asumido)
Licencia exacta de Open WebUI; soporte Postgres/Redis y MCP del chat; términos de FalkorDB; madurez de AgentDB; persistencia y volúmenes de Spaces; wheel `sqlcipher3-binary` en py3.12.
