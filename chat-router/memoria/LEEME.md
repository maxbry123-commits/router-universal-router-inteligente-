# Memoria y almacenamiento
Cableado y probado hoy (NO se mueve): `chat/backend/mvp/{memoria.py,hf_store.py,trabajos.py}` y la herramienta `almacen`.
Destino de lo no cableado: `plugins/memoria` (memoria_yaiwes: SQLite, grafo, adaptadores), `plugins/hf_storage`, `plugins/hf_datasets`; grafos (memanto, graphiti, graphify);
motor de cascada (Prometheus, PyGithub, Phoenix); candidatas (chroma, qdrant, Sentence-Transformers, llama_index, redis, postgres…).
Cableado pendiente: herramientas `memoria_guardar` y `memoria_buscar` en MCP, permisos y Harness (fase 6).

## Movido (rama org/memoria-otros)
- `plugins/memoria` -> `memoria-yaiwes/` (enlace `plugins/memoria`; `router/integration/chat_mvp/memoria_loader.py` sigue cargando por esa ruta). Constantes `parents[3]` -> `parents[4]` en `memoria_yaiwes/{__init__,runtime_adapters}.py` y 4 pruebas.
- `plugins/hf_datasets` -> `hf_datasets/` (enlace `plugins/hf_datasets`, tiene ficha.json). `plugins/hf_storage` NO se movió.
- Las pruebas de `memoria-yaiwes/tests` ya fallaban antes (3 errores de colección por carpetas heredadas "router inteligente universal"/"chat router" inexistentes).

- Arquitectura (README + input literal de Antonio): `arquitectura/`.
