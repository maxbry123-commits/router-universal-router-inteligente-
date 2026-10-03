# Trazabilidad - componentes de memoria y almacenamiento

Verificado: 2026-10-03 20:53 UTC. Metodo: lista completa del arbol git (ls-tree -r) en main (5425d1252) y en la rama devin/1790824641-chat-agent-plan (0a515b8b5).

| Componente | Ruta | Archivos main | Archivos rama | Archivo clave | Origen |
|---|---|---|---|---|---|
| graphiti | .../Componente open soure .../graphiti/ | 385 | 385 | si | DOWNLOAD_EXTRACT_MANIFEST: claves: bundle_bytes,bundle_sha256,extracted_tree,extraction_verified,max_github_blob_bytes,no_lfs,part_size_limit_bytes |
| memanto | .../Componente open soure .../memanto/ | 766 | 766 | si | DOWNLOAD_EXTRACT_MANIFEST: claves: bundle_bytes,bundle_sha256,extracted_tree,extraction_verified,max_github_blob_bytes,no_lfs,part_size_limit_bytes |
| graphify | .../Componente open soure .../graphify/ | 99 | 99 | si | DOWNLOAD_EXTRACT_MANIFEST: claves: bundle_bytes,bundle_sha256,extracted_tree,extraction_verified,max_github_blob_bytes,no_lfs,part_size_limit_bytes |
| agentdb | .../Componentes del Router/router inteligente software/componentes todos/componentes descargados/AgentDB/ | 1460 | 1460 | si | SOURCE_URL: https://github.com/ruvnet/agentdb | SOURCE_COMMIT: 6cdefe451f6afe7395bc88d3587a0225d161089b |
| falkordb | .../Componentes del Router/router inteligente software/componentes todos/componentes descargados/FalkorDB/ | 929 | 929 | si | SOURCE_URL: https://github.com/FalkorDB/FalkorDB | SOURCE_COMMIT: 55204c94bb6c8bc1684ada3d712a61f73f324067 |
| postgresql | .../Componente open soure .../postgres/ | 7703 | 7703 | si | AC_INIT([PostgreSQL], [20devel], [pgsql-bugs@lists.postgresql.org], [], [https://www.postg |

## Discrepancia detectada (causa del error de la sesion anterior)
MEMORIA-INVENTARIO.json (chat router/03-ESTADO) declara: {"falkordb": ["GAP_ABSENT", "GAP"], "agentdb": ["GAP_ABSENT", "GAP"]}.
Es falso: AgentDB y FalkorDB SI estan descargados en .../componentes descargados/. El inventario no mira esa carpeta. Pendiente: corregirlo con watchdog_checkpoint.py, no a mano.

## Estado de runtime (ultima prueba en sandbox, 2026-10-03, rama devin/1790824641-chat-agent-plan)
- graphiti: CONNECTED (servicio sin LLM, base Kuzu) - commit 54617f62b
- graphify: CONNECTED solo lectura (el guardado se rechaza por contrato) - commit 54617f62b
- agentdb: CONNECTED (guardar/leer/buscar; la busqueda vectorial devolvio vacio, respaldo por texto) - commit 58f36bbfc
- memanto: GAP probable (pide Docker+Ollama o clave de su nube; no hay) - sin verificar formalmente
- falkordb: pendiente (codigo Rust; requiere compilador y Redis)
- postgresql: pendiente (compilar fuente; requiere compilador)
- Pruebas: Router 31/31 sin motores conectados, 30/31 con motores conectados (falla test_chat_turn_memory_readback_and_owner_isolation); 04-MEMORIA 7/7.

## Como se integra un componente nuevo (preparado)
1. Ubicar el codigo bajado: ruta, commit y sha256 (manifest). Anotarlo en la tabla de arriba.
2. Definir su runtime: servicio HTTP con el contrato de ComponentAdapter (GET /, POST /save, GET /load, GET /search) o TCP/psycopg (falkordb, redis, postgresql).
3. Exportar RIU_<MOTOR>_URL y probar: /memoria/health CONNECTED + memoria_save con replicas + tests Router (31) y 04-MEMORIA (7).
4. Si necesita LLM, embeddings o un servicio que no existe: GAP con el motivo, sin inventar.
5. Registrar con watchdog_checkpoint.py; commit y push a la rama.
