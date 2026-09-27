# Chat Mvp

Raíz de construcción del chat MVP del Router Inteligente Universal (plan: `bitácora stated JSON Craxy wall plan checkpoint router inteligente universal/RIU-0108-PLAN-MAESTRO-CHAT-MVP.md`; decisiones: `RIU-0109-...`; avance: `RIU-0110-...`).
Regla del Director: aquí solo va lo del chat. El gateway del Router ya probado sigue en `router inteligente universal/integration/huggingface/` y se reutiliza, no se copia.

## Qué hay aquí y en qué estado está (2026-09-20)
| Carpeta / archivo | Salida del plan | Estado |
|---|---|---|
| `groups.yaml` | S1, S7 | HECHO y validado en runner (20 modelos, 0 problemas); gobierna el selector |
| `accounts.yaml` | S1, S5 | HECHO; solo alias, nunca tokens; faltan los logins de `abc123` y `planeta 123` |
| `secret_bank/vault.py`, `session.py`, `broker.py` | S2.1-2.3 | HECHO: 9 tests pasan en runner real |
| `secret_bank/` API, integración con el gateway, página `/bank`, copia cifrada a HF, passkey | S2.4-2.8 | PENDIENTE |
| `deploy/` | S3 | PENDIENTE (Space Docker con Open WebUI + gateway) |
| `storage/` | S4 | PENDIENTE (PostgreSQL, Redis, FalkorDB + Graphiti, AgentDB, ingestión) |
| `tests/` | — | `test_secret_bank.py` |

## Decisiones vigentes
Chat: Open WebUI (conectado al gateway del Router; MCP para intervenir en la conversación). Almacenamiento: Hugging Face (Space Docker + Storage Bucket). Secret Bank: AES-256-GCM + contraseña maestra (passkey/WebAuthn después). Graph DB: FalkorDB (no Kuzu). Graphty no se instala. HF Jobs como fallback de modelos sin proveedor (con enmienda de contrato pendiente).

## Reglas
- Ninguna credencial en texto plano en este repo, en bases de datos, en logs ni en el chat. `riu-secret-scan.yml` lo vigila (383 archivos, 0 hallazgos el 2026-09-20).
- Nada se declara integrado por existir la carpeta: cada pieza necesita un test que falle antes y pase después, en runner real (`riu-chat-mvp-core-verify.yml`).
- Los modelos sin proveedor serverless quedan `hf_job_fallback` hasta cerrar la enmienda del contrato (`HF_JOB_EPHEMERAL_SERVING`) y la prueba S7.3.
