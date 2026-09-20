# ADENDA A LA ARQUITECTURA — RIU-0108 — Chat MVP, Secret Bank y stack de almacenamiento — 2026-09-20

Anclas: `../Claude notas/INPUT-BLOCK-06-VERBATIM.md` (instrucciones textuales, credenciales pegadas redactadas) · `../bitácora stated JSON Craxy wall plan checkpoint router inteligente universal/RIU-0108-PLAN-MAESTRO-CHAT-MVP.md` (plan por Salidas, trazabilidad 1 a 1, dudas).
No modifica `README.md` (arquitectura consolidada hasta RIU-0094); se añade aparte por el límite de reescribir archivos grandes. Estado: DISEÑO APROBADO POR EL DIRECTOR EN LO ESCRITO (stack y Secret Bank), CONSTRUCCIÓN NO INICIADA; dudas D1-D9 abiertas.

## Capas (todas detrás del Router; el chat solo guarda referencias)
```
USUARIO → LOGIN YAIWES (contraseña ahora; passkey después) → SESIÓN
        → SECRET BANK (vault cifrado) → SECRET BROKER (credential_ref)
CHAT OPEN SOURCE  →  GATEWAY DEL ROUTER (/v1, keys MAXBRY)  →  Enchufe → RedUniversal → proveedor
                              │
                     INGESTION ROUTER (adjuntos)
        ┌────────────┬────────┴─────────┬───────────────┐
   archivo original  PostgreSQL         AgentDB         Graphiti → FalkorDB
   (Storage Bucket)  verdad/IDs/refs    episodios,      entidades, hechos,
                                        skills, vector  relaciones, tiempo
                              │
                           Redis (caché, sesiones, locks, límites, TTL; solo referencias)
```
Graphty (visualización) NO se instala. Kuzu descartado por el Director; FalkorDB (Neo4j como alternativa).

## Reglas de arquitectura del Secret Bank
- El agente y el chat jamás reciben una API key; el Router pide `credential_ref` (`proveedor/cuenta`) y el broker usa el secreto internamente.
- PostgreSQL, AgentDB, Graphiti y Redis guardan solo `credential_ref`, nunca valores. El único lugar con valores es `vault.db`, cifrado.
- Login una vez por sesión; la clave de descifrado vive en memoria y caduca con la sesión.
- Persistencia física: copia cifrada del vault en un repo privado de Hugging Face; Hugging Face aporta almacenamiento, no gestión de claves (como pidió el Director).
- Propuesta técnica pendiente de aprobación (D3): AES-256-GCM por valor + scrypt sobre SQLite, en lugar de SQLCipher; passkey/WebAuthn en segunda fase.

## Memoria: tres niveles y anclas (del documento "Parte 1 · Adjuntos + memoria")
CHAT MEMORY (solo esa conversación) · PROJECT MEMORY (todos los chats del proyecto) · GLOBAL MEMORY (agentes autorizados). Cada archivo se ancla con `project_id, conversation_id, memory_id, file_id, file_version, file_hash, chunk_id, source_uri, created_at`.

## Carpeta de construcción
`Chat Mvp/` en la raíz de `main` (sin emoji en el nombre real). Reutiliza el gateway ya probado de `router inteligente universal/integration/huggingface/`.

## Evidencia usada por este diseño
Metadatos de HF_TOKEN_1 (full access sobre `COMAND-CENTER-1`): run `35493843251`. Búsquedas del motor propio sin tokens de LLM: `router inteligente universal/websearch-results/ws-35493826829`, `-35493831398`, `-35493834208`, `-35494047636`, `-35494051059`. Docker Spaces con Storage Buckets como volumen: changelog HF 2026-03-31. Imagen combinada FalkorDB + Graphiti MCP: `getzep/graphiti/mcp_server/docker`.
