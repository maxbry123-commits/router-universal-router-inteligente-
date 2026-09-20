# Chat Mvp

Raíz de construcción del chat MVP del Router Inteligente Universal (plan: `bitácora stated JSON Craxy wall plan checkpoint router inteligente universal/RIU-0108-PLAN-MAESTRO-CHAT-MVP.md`, decisiones: `RIU-0109-...`).
Regla del Director: aquí solo va lo del chat. El gateway del Router ya probado sigue en `router inteligente universal/integration/huggingface/` y se reutiliza, no se copia.

## Qué hay aquí y en qué estado está
| Carpeta / archivo | Salida del plan | Estado |
|---|---|---|
| `groups.yaml` | S1, S7 | escrito; gobierna qué modelos ofrece el selector |
| `accounts.yaml` | S1, S5 | escrito; solo alias, nunca tokens; faltan 2 logins |
| `secret_bank/` | S2 | en construcción (vault cifrado, sesión, broker) |
| `deploy/` | S3 | pendiente (Space Docker con Open WebUI + gateway) |
| `storage/` | S4 | pendiente (PostgreSQL, Redis, FalkorDB + Graphiti, AgentDB, ingestión) |

## Decisiones vigentes
Chat: Open WebUI (conectado al gateway del Router; MCP para intervenir en la conversación). Almacenamiento: Hugging Face (Space Docker + Storage Bucket). Secret Bank: AES-256-GCM + contraseña maestra (passkey/WebAuthn después). Graph DB: FalkorDB (no Kuzu). Graphty no se instala.

## Reglas
- Ninguna credencial en texto plano en este repo, en bases de datos, en logs ni en el chat. El workflow `riu-secret-scan.yml` lo vigila.
- Nada se declara integrado por existir la carpeta: cada pieza necesita un test que falle antes y pase después, en runner real.
- Los modelos sin proveedor serverless quedan `PENDING` hasta cerrar la enmienda del contrato (`HF_JOB_EPHEMERAL_SERVING`) y la prueba S7.3.
