# Memoria y almacenamiento: integracion (Paso 2)

Todo vive dentro de la raiz del Harness. El Harness (`puente_chat`) es el unico punto de acceso: `_memoria()` -> `memoria_loader._memory()` -> fachada `memoria_yaiwes`.

```
CHAT -> Router -> ficha (fichas_qwen) -> Harness puente_chat -> fachada memoria_yaiwes
                                                                 |- SQLite ............. LA VERDAD (historial, checkpoints, snapshot de anclas, registro constitucional)
                                                                 |- grafo SQLite ....... apoyo; si falla NO invalida el guardado (replica_gaps)
                                                                 |- Qdrant local ....... indice DERIVADO y reconstruible (rebuild_index)
                                                                 |- Graphiti/Graphify/Memanto/Chroma/... endpoints opcionales (RIU_*_URL); sin servicio = GAP
```

## Estado real (no se declara nada que no este probado)

| Componente | Estado | Nota |
|---|---|---|
| SQLite | CONNECTED | probado con Store real, reinicio y los 4 tipos de puente_chat (test_memoria_real.py) |
| Grafo SQLite | CONNECTED (apoyo) | su fallo ya no pierde el dato |
| Qdrant local | DERIVED_LOCAL_INDEX_UNVERIFIED_IN_ROUTER | `qdrant-client` descargado con el motor (556dc92a87). API contrastada con el codigo fuente descargado; probado con un cliente simulado, NO ejecutado con la libreria real (faltan numpy/pydantic/grpcio/portalocker en el Router). Sin cliente instalado: GAP_CLIENT_NOT_INSTALLED, la memoria sigue con SQLite |
| Embedding de Qdrant | LEXICAL_HASH_256 | determinista; busca por palabras en comun. NO es busqueda semantica (`semantic: false` en health) |
| Graphiti | GAP_NO_SERVICE | necesita una base de grafos; Kuzu no se pudo obtener con el motor |
| Graphify | GAP_READ_ONLY_SOURCE | fuente de solo lectura; no hay servicio |
| FalkorDB / AgentDB | GAP_ABSENT | no existen en main |

## Variables
- `RIU_QDRANT_LOCAL=0` apaga el indice local. `RIU_QDRANT_PATH` cambia su carpeta (por defecto `chat router/04-MEMORIA/indices/qdrant_local`, ignorada por git).
- `RIU_GRAPHITI_URL`, `RIU_GRAPHIFY_URL`, `RIU_MEMANTO_URL`, `RIU_AGENTDB_URL`: contrato generico `/save`, `/load`, `/search`.

## Pruebas
`python "chat router/04-MEMORIA/tests/test_memoria_real.py"` (10 pruebas, sin red ni pytest).

## Pendiente de decision
- Embeddings semanticos reales (hoy no hay fuente verificada).
- Usar la busqueda de Qdrant para traer memoria relacionada al prompt del chat (no cableado a proposito).
- Probar `qdrant-client` real dentro del Router.

## Integracion Graphiti / Graphify / Memanto / Lifecycle (2026-10-11)

Codigo en `chat router/04-MEMORIA/memoria_yaiwes/runtime_adapters.py` y `integration/chat_mvp/storage_lifecycle.py`.
SQLite sigue siendo la verdad; todo lo demas es indice/replica derivada. `GET /memoria/health` muestra el estado real de cada uno.

| Componente | Que hace | Estado hoy | Para activarlo |
|---|---|---|---|
| Embedding e5-small (384) | un modelo compartido | GAP_EMBEDDING_MODEL_NOT_AVAILABLE | carpeta del modelo en `RIU_EMBED_MODEL_DIR` + `sentence-transformers` |
| Graphiti | grafo temporal sobre FalkorDBLite embebido; LLM = el de la ficha (`set_llm_client`) | GAP segun dependencia que falte | `RIU_GRAPHITI_ENABLE=1`, `graphiti-core`, `redislite`, modelo de embeddings |
| Graphify | grafo del CODIGO (busqueda en graph.json), no entra en save | GAP_GRAPH_NOT_BUILT | `RIU_GRAPHIFY_ROOT` y correr `graphify <root>` |
| Memanto | agente `yaiwes-router`, token solo en RAM | GAP_SERVICE_UNREACHABLE | `RIU_MEMANTO_URL` con `memanto serve` |
| Qdrant local | indice derivado, vector lexical (NO semantico) | GAP si falta qdrant-client | instalar qdrant-client |
| Restore al arrancar | si no hay base local, baja el snapshot del bucket HF; valida integridad; nunca pisa datos locales | implementado | `HF_BUCKET_ID` + `HF_WRITE_TOKEN`/`HF_TOKEN` |
| Autosync | sube snapshot cada `RIU_AUTOSYNC_SECONDS` (300 por defecto) | implementado | mismas variables |

Pruebas: `python test_memoria_real.py` (10) y `python test_runtime_lifecycle.py` (9), sin red ni descargas. Los adaptadores de Graphiti y Memanto NO se han probado contra los servicios reales (no instalados, sin autorizacion de descarga); ninguno se declara CONNECTED sin que `health()` lo compruebe.
