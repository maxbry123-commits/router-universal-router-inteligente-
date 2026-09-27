# Chat Mvp

Raíz de construcción del chat MVP del Router Inteligente Universal (plan: `bitácora stated JSON Craxy wall plan checkpoint router inteligente universal/RIU-0108-PLAN-MAESTRO-CHAT-MVP.md`; decisiones: `RIU-0109-...`; avance: `RIU-0110-...`).
Regla del Director: aquí solo va lo del chat. El gateway del Router ya probado sigue en `router inteligente universal/integration/huggingface/` y se reutiliza, no se copia.

## Qué hay aquí y en qué estado está (checkpoint RIU-0119, 2026-09-27)
| Carpeta / archivo | Salida del plan | Estado |
|---|---|---|
| `groups.yaml` | S1, S7 | HECHO y validado en runner (20 modelos, 0 problemas); gobierna el selector |
| `accounts.yaml` | S1, S5 | HECHO; solo alias, nunca tokens; faltan los logins de `abc123` y `planeta 123` |
| `secret_bank/vault.py`, `session.py`, `broker.py` | S2.1-2.3 | HECHO: 9 tests pasan en runner real |
| `secret_bank/` API, integración con el gateway, página `/bank`, copia cifrada a HF, passkey | S2.4-2.8 | PENDIENTE |
| `deploy/` | S3 | PENDIENTE (Space Docker con Open WebUI + gateway) |
| Persistencia activa | S4 | SQLite de `router inteligente universal/integration/chat_mvp/store.py`: conversaciones, mensajes, agentes, adjuntos, caché y grafo de procedencia. Prueba local de cierre/reapertura añadida; no es Graphiti ni búsqueda semántica. |
| Bucket HF | S4, B-3 | `/chat/storage/sync` ya sincroniza snapshot SQLite y adjuntos; la prueba usa un filesystem simulado. El endpoint ahora rechaza falta de bucket/token sin llamar al SDK. Read-back real del bucket: PENDIENTE. |
| State Hub | B-1 | DATA apunta a `chat router/03-ESTADO/data`; `/state/events` append-only y `/state/rebuild` reconstruyen `STATE.json`, `CRAZY_WALL.json` y la sección de State Hub del `HANDOFF.md`. 3 eventos + recuperación local probados. Los endpoints mutables requieren `RIU_ROUTER_API_KEY`. Read-back tras publicar el branch pendiente. |
| Dataset HF `COMAND-CENTER-1/yaiwes-hf-memoria` | S4 | No se encontró un escritor/adaptador de memoria conversacional en el runtime del chat; las referencias de dataset existentes son distintas y no certifican ese puente. |
| Graphiti / FalkorDB / Memanto / Graphify | S4, B-2 | Fuentes presentes bajo `router inteligente universal/Componente open soure router inteligente universal/{graphiti,memanto,graphify}`; no conectadas al runtime. FalkorDB no se encontró allí. Graphify es grafo de código, no memoria de conversación. |
| AgentDB / PostgreSQL / Redis | S4, B-2 | AgentDB no se encontró en el pool; PostgreSQL, Redis y `redis-py` aparecen como árboles de código, no servicios conectados/configurados. |
| Pruebas | S4 | `router inteligente universal/tests/test_chat_mvp_{pure,app}.py`; 17 pasaron localmente (2 warnings deprecación FastAPI), incluido State Hub, sync simulado y persistencia SQLite tras reabrir. |

## Checkpoint de cableado (RIU-0119)
- Base auditada: `main` en `98916ad3c33d9c487cf783c340d5c50e3142562f`.
- Cambios de código locales: State Hub mínimo, ruta DATA de estado del puente UI, rechazo fail-closed de sync HF sin token, cierre de SQLite para prueba y verificaciones de persistencia/sync.
- No se usaron credenciales ni se escribió en Hugging Face; no hubo despliegue.
- Pendiente: read-back de los archivos de estado al publicar el branch; confirmar acceso/read-back real del bucket dentro del alcance autorizado; integrar los servicios B-2 solo cuando exista el servicio operativo y su contrato de conexión.

## Decisiones vigentes
Chat: Open WebUI (conectado al gateway del Router; MCP para intervenir en la conversación). Almacenamiento: Hugging Face (Space Docker + Storage Bucket). Secret Bank: AES-256-GCM + contraseña maestra (passkey/WebAuthn después). Graph DB: FalkorDB (no Kuzu). Graphty no se instala. HF Jobs como fallback de modelos sin proveedor (con enmienda de contrato pendiente).

## Reglas
- Ninguna credencial en texto plano en este repo, en bases de datos, en logs ni en el chat. `riu-secret-scan.yml` lo vigila (383 archivos, 0 hallazgos el 2026-09-20).
- Nada se declara integrado por existir la carpeta: cada pieza necesita un test que falle antes y pase después, en runner real (`riu-chat-mvp-core-verify.yml`).
- Los modelos sin proveedor serverless quedan `hf_job_fallback` hasta cerrar la enmienda del contrato (`HF_JOB_EPHEMERAL_SERVING`) y la prueba S7.3.
