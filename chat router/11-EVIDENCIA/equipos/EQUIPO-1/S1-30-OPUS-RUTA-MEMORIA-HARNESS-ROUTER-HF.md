# S1-30 (Opus, autorizado por Hy a tocar el Router): ruta completa memoria/almacenamiento
Ruta cerrada y probada: DeepSeek Harness -> plugin MCP `memoria` -> Router (/memoria/*, /chat/storage*) -> SQLite -> HF Storage Bucket privado `COMAND-CENTER-1/yaiwes-memoria-storage` (permanente) -> Router nuevo y vacio restaura del bucket.

## Revision (4 pasadas)
1. Router: ya tenia /memoria/{health,save,load,search} (memoria_loader.py) y sync_to_bucket + /chat/storage + /chat/storage/sync (router.py). Faltaba: restaurar al arrancar, sync automatico.
2. HF: solo existe 1 Space (`claude-github-mcp-backup`, cpu-upgrade pago, RUNNING, bucket propio en /data). NO hay Space del Router. Buckets: claude-github-mcp-backup-storage, yaiwes-v54. Dataset yaiwes-hf-memoria. `owner_HF_1` no existe para el token.
3. Harness: dsh 0.2.0-rc.2 carga plugins MCP por overlay `dsh --patch`.
4. Dependencias reales del Router para arrancar: integration, security, red, enchufe (Fables), chat router/ui.

## Cambios
- Router `integration/chat_mvp/router.py`: `restore_from_bucket()` (inverso de sync_to_bucket), get_store() restaura si no hay SQLite y hay HF_BUCKET_ID+token; `start_bucket_autosync()` (hilo, cada RIU_AUTOSYNC_SECONDS=60 por defecto, solo si hubo cambios).
- Router `integration/chat_mvp/app.py`: startup llama start_bucket_autosync().
- Bucket nuevo privado `COMAND-CENTER-1/yaiwes-memoria-storage`.
- `chat router/04-MEMORIA/plugin/memoria_mcp_server.py`: 6 tools (memoria_health/save/load/search, almacenamiento_estado, almacenamiento_sync), todo via Router.
- `chat router/04-MEMORIA/plugin/harness-memoria.cordis.yml`: overlay del harness (reemplaza harness-memoria.yaml).
- Tests: `04-MEMORIA/tests/test_bucket_bridge.py` (2, fake fs) + `e2e_harness_router_bucket.py` (e2e real).

## Pruebas
- E2E real (cliente MCP stdio = protocolo del harness): 6 tools; restore previo OK; save e2e-d460a2e1; autosync -> fila presente en el bucket HF (69632 B); Router nuevo con carpeta vacia -> memoria_load devuelve el dato; sync manual OK.
- dsh real: `dsh headless --patch harness-memoria.cordis.yml` compone mcp-memoria y ARRANCA el proceso memoria_mcp_server.py; el turno se detiene solo por falta de credencial LLM (MISSING_CREDENTIAL DEEPSEEK_API_KEY), no por la memoria.
- Regresion Router: tests/test_chat_mvp*.py 31/31 antes y despues. 04-MEMORIA/tests 7/7.

## PENDIENTE (para Sonnet / Hy)
1. Router corriendo 24/7 en HF: no existe Space del Router. Requiere decision de Hy (Space nuevo pago = costo; o dentro del Space pago existente = redeploy, prohibido en horario de trabajo). Variables: HF_BUCKET_ID=COMAND-CENTER-1/yaiwes-memoria-storage, RIU_AUTOSYNC_SECONDS=60; secretos: HF_WRITE_TOKEN (o HF_TOKEN), RIU_AGENT_API_KEYS (JSON clave->agente).
2. Credencial LLM del harness (DEEPSEEK_API_KEY o ruta de proveedor apuntando al Router /v1). Sin eso el harness carga la memoria pero no conversa.
3. Motores de memoria (Graphiti, Graphify, Memanto, AgentDB, FalkorDB, PostgreSQL): codigo bajado, runtime no. ComponentAdapter (04-MEMORIA/memoria_yaiwes/__init__.py) los usa como replicas si existe RIU_GRAPHITI_URL / RIU_MEMANTO_URL / RIU_GRAPHIFY_URL / RIU_AGENTDB_URL.
4. hf_bridge.py (dataset yaiwes-hf-memoria) queda como respaldo opcional; la ruta oficial es el bucket del Router.
