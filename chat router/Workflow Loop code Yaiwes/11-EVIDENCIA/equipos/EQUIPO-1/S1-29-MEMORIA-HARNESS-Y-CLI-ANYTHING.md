# S1-29 (salida 1 cont.): memoria como plugin del harness + CLI-Anything
CORRECCION a S1-28: el Router SI monta la memoria: integration/chat_mvp/app.py:98 -> /memoria/{health,save,load,search} (memoria_loader.py, memory_runtime.py carga 04-MEMORIA/memoria_yaiwes). Ademas el Router ya tiene sync_to_bucket (router.py: copia SQLite + docs a HF Storage Bucket, env HF_BUCKET_ID + HF_WRITE_TOKEN/HF_TOKEN). Puntos 1 y 3 de S1-28 quedan asi: (1) conexion Router-memoria = EXISTE; (3) harness = ahora si enchufado (abajo).
HECHO:
- Motores: existen y probados (motor 3 VERIFIED_CLOSED, E-09). En los archivos NO consta que Manus los hiciera. Faltaba CLI-Anything: descargado con hf_download_extract_engine (HKUDS/CLI-Anything, HEAD, 1872 archivos, 63 MB, veredicto VERIFIED_CLOSED) a `router inteligente universal/Componente open soure router inteligente universal/CLI-Anything`. MCP-Python-SDK/python-sdk ya estaban. (1er intento READBACK_TREE_HASH_GAP, reintento OK.)
- Plugin memoria para el DeepSeek Harness (separado del workflow): `chat router/04-MEMORIA/plugin/memoria_mcp_server.py` (servidor MCP stdio, 7 tools: memoria_health/save/load/search -> Router /memoria/*; hf_memoria_health/snapshot/restore_if_empty -> hf_bridge) + `harness-memoria.yaml` (entrada para @deepseek-ai/dsh-mcp-client, serverName memoria). Prueba: list_tools=7; hf_memoria_health=OK(private); memoria_health=GAP ConnectError (no habia Router corriendo).
PENDIENTE:
1. Probar memoria_save/load de punta a punta con Router corriendo y RIU_API_KEY (no probado).
2. Cargar harness-memoria.yaml en la config del harness y ver las tools en dsh (no probado).
3. MCP de almacenamiento HF en el Router: no hay servidor MCP; hay sync_to_bucket (API). Hf_bridge.py cubre dataset.
4. Runtimes Graphiti/Graphify/Memanto/FalkorDB/AgentDB/PostgreSQL = GAP.
5. CLI-Anything: descargado; sin cablear (registro como Tool/Pool del harness = salida 2/5).
6. Fables universal plug (3 archivos de 01-PLAN/ANEXOS): no hizo falta para esta conexion.
