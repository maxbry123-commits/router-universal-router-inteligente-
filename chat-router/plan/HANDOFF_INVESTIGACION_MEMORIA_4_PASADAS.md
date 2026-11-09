# HANDOFF — Investigación forense: almacenamiento y memoria conectados al Harness DeepSeek

Estado: INVESTIGACIÓN en solo lectura, 4 pasadas. No se cambió código. Pendiente de decisiones del owner.
Fecha: 2026-11-09. Ramas revisadas: main, ccr-f01c3de9-bmry0s, ccr-42f0e753-ni96xs (y lista de ramas remotas).

## Pasada 1 — Inventario

Componentes de memoria vendorizados en `chat-router/memoria/componentes/`: memanto, graphiti, graphify, chroma, qdrant, qdrant-client, redis, redis-py, postgres, asyncpg, aiomysql, llama_index, Sentence-Transformers, phoenix, prometheus, PyGithub.

Implementaciones propias:
- [chat-router/chat/backend/mvp/memoria.py](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/chat-router/chat/backend/mvp/memoria.py) — memoria del chat: un JSON por scope en el bucket HF.
- [chat-router/memoria/memoria-yaiwes/memoria_yaiwes/__init__.py](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/chat-router/memoria/memoria-yaiwes/memoria_yaiwes/__init__.py) — motor multi-backend (SQLite como verdad, Qdrant como índice derivado, adaptadores Graphiti, Memanto, Graphify).
- [chat-router/memoria/hf_datasets/plugin.py](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/chat-router/memoria/hf_datasets/plugin.py) — storage de datasets de Hugging Face.
- [chat-router/plugins/memoria](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/chat-router/plugins/memoria) y [chat-router/plugins/hf_storage](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/chat-router/plugins/hf_storage) — plugins de harness.

## Pasada 2 — Conexión con el Harness DeepSeek (referencias)

- Harness: [chat-router/chat/backend/deepseek_harness/server.py](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/chat-router/chat/backend/deepseek_harness/server.py) expone tools `memoria`, `almacen`, `yaiwes_md`, `pendientes`, `sala`. Se conectan al Router por HTTP.
- Router: [chat-router/chat/backend/mvp/app.py](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/chat-router/chat/backend/mvp/app.py) llama a `memoria` y a `hf_store` directamente. Verificado en main.
- Ningún archivo del Harness ni del backend importa `memoria_yaiwes`, Graphiti, Memanto, Graphify, Qdrant, Chroma ni Redis. Verificado con búsqueda en `chat-router/chat/backend`, `chat-router/harness`, `chat-router/plugins` y `chat-router/memoria`.
- Única importación: pruebas en `chat-router/workflow-loop-code-yaiwes/workflow-loop-yaiwes/code/memoria/tests/` y una prueba en `router-mvp/router/tests/test_puentes_plugins.py`.
- `prompt_rules.yaml` menciona `_cablear_graphiti` y `memoria_yaiwes` como texto de instrucciones. No es código ejecutable.

## Pasada 3 — Verificación de cableado

| Pieza | Estado real | Evidencia |
|---|---|---|
| Memoria en uso (bucket HF, JSON por scope) | ACTIVA en el Router | `mvp/memoria.py` + `mvp/hf_store` |
| `memoria_yaiwes` (SQLite + Qdrant + adaptadores) | NO CONECTADA al runtime; solo en pruebas | sin imports fuera de su carpeta y de tests |
| Graphiti / Memanto / Graphify | NO CONECTADOS | adaptadores leen `RIU_GRAPHITI_URL`, `RIU_MEMANTO_URL`, `RIU_GRAPHIFY_URL`; no hay entradas en `connections/endpoints.yaml` |
| Qdrant local | NO CONECTADO y con ruta rota | la ruta apunta a `ROOT/"chat router"/"04-MEMORIA"/…`, carpeta antigua |
| SQLite de memoria | Existe en `memoria_yaiwes`; no en el runtime | `SQLiteAdapter` con `sqlite3` |
| `sqlite_memory.py` (rama Router 1) | SIN USO | ningún módulo lo importa |
| `search` del Router | Devuelve clave `"sqlite"` pero hace slicing de lista | `mvp/memoria.py` línea 79: el nombre engaña |

## Pasada 4 — Registros centrales

- `SYSTEM_WIRING_REGISTRY.yaml`: entradas `memoria` (línea 177) y `storage` (línea 186), con `consumidor: [chat_router, agentes, loop_cola_watchdog]`, `transporte: harness_plugin`, estado `DISCOVERED`. Pruebas pendientes: J09, J10 y J11. Ninguna activa.
- `SYSTEM_WIRING_REGISTRY.yaml` línea 291: C-008 `chat_router → memoria`, estado `DISCOVERED`.
- `connections/registry.yaml`: no contiene entradas de memoria.
- `connections/endpoints.yaml` y `connections/healthchecks.yaml`: no contienen endpoints de Graphiti, Memanto, Graphify, Qdrant ni Redis.

## Conclusión de la investigación

1. El sistema de memoria que SÍ corre es el del Router: JSON por scope en el bucket de Hugging Face, expuesto a los modelos a través del Harness.
2. El sistema completo (SQLite como verdad, Qdrant como índice, Graphiti/Memanto/Graphify como grafos y memoria semántica) existe como código y componentes vendorizados, pero NO está conectado. Ningún modelo lo usa hoy.
3. Hay dos fuentes de verdad posibles: el bucket HF y el SQLite de `memoria_yaiwes`. Hay que elegir una.
4. Las pruebas de integración de la memoria (J09, J10, J11) no se han ejecutado.

## Flags

- 🚩 M-1 Dos sistemas de memoria sin una fuente de verdad única.
- 🚩 M-2 Graphiti, Memanto, Graphify y Qdrant sin endpoints registrados. Requieren servicios externos que no hay en el repo.
- 🚩 M-3 Ruta rota en Qdrant local (`04-MEMORIA`).
- 🚩 M-4 El `search` del Router llama `sqlite` a algo que no es SQLite.
- 🚩 M-5 `sqlite_memory.py` sin consumidores: cuarentena o conexión.
- 🚩 M-6 Pruebas J09, J10 y J11 pendientes.

## Pendientes de decisión del owner

- Qué sistema de memoria es la fuente de verdad: bucket HF, SQLite de `memoria_yaiwes`, o ambos con uno como índice.
- Qué componentes (Graphiti, Memanto, Graphify, Qdrant) se activan y con qué servicios.
- Si `memoria_yaiwes` se conecta al Router o queda como cuarentena.
