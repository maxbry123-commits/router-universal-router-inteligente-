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
