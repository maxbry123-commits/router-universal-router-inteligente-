# S1-28 Paso 1 (salida 1): memoria + puente HF
HECHO (probado):
- `chat router/04-MEMORIA/memoria_yaiwes/hf_bridge.py`: snapshot SQLite -> dataset privado COMAND-CENTER-1/yaiwes-hf-memoria (snapshots/memoria.sqlite) y restore si SQLite vacia. Token solo por env HF_TOKEN.
- Prueba real 2026-10-03: health OK (private=True); snapshot sha256 9d0c42f1… (8192 B); restore en archivo nuevo mismo sha256 -> ROUNDTRIP OK. Nota: dejo un snapshot de prueba en el dataset.
- Ya existente (EQUIPO-6): SQLite + grafo SQLite + persistencia PASS; MemoryFacade con adaptadores por endpoint (state-hub, dataset-yaiwes, graphiti, falkordb, memanto, graphify).
PENDIENTE (no se toco el Router):
1. Conectar memoria al Router: el Router no referencia memoria_yaiwes; el plugin host del Router lee plugins/<id>/ficha.json dentro del Router (prohibido tocarlo). Montaje = tarea del Router, por Director.
2. Puente MCP Router<->HF-almacenamiento: el Router tiene integration/huggingface (jobs, dataset mounts, RIU-0040) pero NO se encontro un servidor MCP de almacenamiento HF; hf_bridge.py es el puente por API directa. PENDIENTE MCP.
3. Harness DeepSeek: sin plugin de memoria montado; pendiente enchufar hf_bridge/MemoryFacade como plugin del harness.
4. Runtimes Graphiti, Graphify, Memanto, FalkorDB, AgentDB, PostgreSQL: GAP (ver HANDOFF-MEMORIA-GAPS.json).
5. Llamar restore_if_empty al arranque y snapshot periodico: requiere enganche en Router/harness.
