# ADENDA A LA ARQUITECTURA — RIU-0108 — Chat MVP: banco de claves, stack de datos y chat open source

Anclas: `../Claude notas/PLAN-MAESTRO-CHAT-MVP.md` · `../Claude notas/PLAN-ANEXO-A-SECRET-BANK.md` · `../Claude notas/PLAN-ANEXO-B-STORAGE-Y-CHAT-OPEN-SOURCE.md` · `../Claude notas/INPUT-BLOCK-06-secret-bank-stack-plan-VERBATIM.md` (textual, con tokens redactados) · `../bitácora stated JSON Craxy wall plan checkpoint router inteligente universal/RIU-0108-PLAN-CHAT-MVP-VALIDACION-INPUTS.md`.
No modifica `README.md` (arquitectura consolidada hasta RIU-0094); se fusionará cuando el Director autorice la partición de archivos grandes.

## Decisiones de arquitectura fijadas por el Director (INPUT BLOCK 06)
| Capa | Decisión | Nota |
|---|---|---|
| Base principal / verdad | PostgreSQL | IDs, tareas, auditoría, referencias de credenciales |
| Caché y estado rápido | Redis | sesiones efímeras, locks, rate limits, colas ligeras, TTL, deduplicación; nunca secretos |
| Memoria de agentes | AgentDB (`ruvnet/agentdb`) | episodios, skills, patrones, memoria vectorial |
| Conocimiento temporal | Graphiti sobre FalkorDB (o Neo4j) | `graphiti-core[falkordb]`; NO Kuzu |
| Visualización de grafo | Graphty: NO se instala (backend-only) | opcional en el futuro |
| Banco de claves | YAIWES Secret Bank: SQLCipher + Secret Broker + `credential_ref` | fuera de git (repo público); Hugging Face solo como almacenamiento |
| Chat | Chat open source apuntando al Router (recomendado Open WebUI); no crear otro | mismo chat + panel "Archivos / Memoria" |
| Raíz en `main` para el chat | `Chat Mvp/` (sin emojis) | aún no creada |
| Modelos eliminados de las listas | MiroThinker-8B, yasserrmd/Neuro-Orchestrator-8B | |
| LFM2 | LFM2-2.6B y LFM2.5-2.6B son checkpoints distintos; LFM2.5 es la generación nueva | pendiente elegir (D4) |

## Flujo del Router con el banco (regla principal del adjunto)
LOGIN una vez → banco desbloqueado → sesión activa → el Router pide `credential_ref` → el Broker resuelve y llama al proveedor → el agente recibe la respuesta, nunca la clave.

## Ingestión de adjuntos
Archivo → router de ingestión → original en almacenamiento de objetos + parser → chunks → Postgres (metadatos), AgentDB (memoria semántica), Graphiti/FalkorDB (entidades y hechos) → Redis (caché) → recuperación → Router → LLM/agentes. Anclas: `project_id, conversation_id, memory_id, file_id, file_version, file_hash, chunk_id, source_uri, created_at`. Niveles: chat / proyecto / global.

## Estado (2026-09-20)
Chat sobre el Router con Kimi K3, DeepSeek V4 Flash/Pro y MiniMax M3: probado en runner real (RIU-0105). Todo lo demás de esta adenda: DISEÑO, sin código. Decisiones abiertas D1-D6 en el plan maestro.
