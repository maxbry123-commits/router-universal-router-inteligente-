# HANDOFF — CHAT YAIWES (leer primero si continúas este trabajo)
Actualizado: 2026-09-27 05:45 UTC por Opus. Director: Max.

## Orden de lectura
1. `../01-PLAN/PLAN-DSL-DAG-00-CONTRATO.yaml` (reglas, fuente de verdad, gobernanza, 12 goals, flags)
2. `../01-PLAN/PLAN-DSL-DAG-01-NODOS.yaml` (DAGs 0, A, B, C, D, E; pasos por nodo; orden; estado)
3. `../01-PLAN/DSL-DAG-MEMORIA-ALMACENAMIENTO.yaml` (MEMORIA: MANUS nodos M-0..M-7; OPUS nodo H-1 puente HF; código en `../04-MEMORIA/`)
4. `../02-ARQUITECTURA/📂readme chat Arquitectura.md`
5. `../00-INSTRUCCIONES/` (verbatim del Director)
NO EJECUTAR: `PLAN-MAESTRO-CHAT.yaml`, `PLAN-DSL-DAG-CHAT-AGENTES-INFRA.yaml`, `ORQUESTADOR-DE-TRABAJO.yaml` (integrados en los nodos).

## Quién hace qué
- **MANUS:** memoria y almacenamiento (M-0..M-7). Solo cablear componentes ya descargados; faltantes = GAP. Su estado lo escribe el State Hub en el bloque de abajo (no editar a mano).
- **OPUS:** A-1 OmniRoute 100 % → H-1 puente HF → C-1.. equipo de agentes.
- **Vercel:** despliegue automático APAGADO desde 27-sep (ignora commits). Solo 1 despliegue final ordenado por el Director.

## Checkpoint Opus
- V-1 verbatim: paso 1 ✅ (docs 22-26 y M40 literales); paso 2 parcial ✅ `INPUT-BLOCK-VERBATIM-PARTE-2-A.md`; ⏳ PARTE-2-B (docs HF 2-4 + M10, docs 5-7, doc 9, doc 8, doc 10, M12-M14); paso 3 auditoría pendiente.
- A-1 OmniRoute: prueba relanzada 27-sep 02:40; leer resultado de `prueba-omniroute-router.yml`.

## Flags
FLAG-1 `ui_bridge.py` DATA → `chat router/03-ESTADO/data` · FLAG-2 enlace chat de Manus · FLAG-3 Groq sin clave · FLAG-4 PARTE-2-B pendiente.

## CRAZY WALL (1 chat = 1 nodo)
```json
{"schema":"yaiwes.crazy-wall/v1","nodos":{"A-1":{"status":"CLAIMED","agente":"opus"},"V-1":{"status":"CLAIMED","agente":"opus","fase":"PASO_2B"},"M-*":{"status":"CLAIMED","agente":"manus","fase":"B2_MEMORY_WIRED"}}}
```

<!-- YAIWES STATE HUB START -->
## Estado operativo generado por State Hub
Revisión: 13
Proyecto/tarea: `chat-yaiwes` / `RIU-0121`
Estado: **COMPLETED**
Fase: `M7_RDC_VERIFIED`

### Último checkpoint
M-0..M-7 COMPLETADOS: 13 componentes auditados; SQLite, State Hub y grafo fallback cableados; FalkorDB (927 archivos) y AgentDB (1456 archivos) descargados y read-back EXTRACTED_VERIFIED en GitHub. Action memoria PASS 31 tests. Secret Scan: 217 hallazgos baseline preexistentes; escaneo dirigido de memoria PASS. H-1 sigue reservado a Opus.

### Siguiente
H-1 reservado a Opus; no ejecutar HF RW ni despliegue Vercel
<!-- YAIWES STATE HUB END -->

## Checkpoints DSL memoria/almacenamiento — RIU-0121
M-0 ✅ PASS — inventario real de 13 componentes con ruta y object ID; FalkorDB y AgentDB ausentes.
M-1 ✅ PASS — `chat router/04-MEMORIA/memoria_yaiwes/` y único loader `memoria_loader.py`; rutas `/memoria/*` fail-safe.
M-2 ✅ PASS — SQLite existente reutilizado como fuente principal; memoria sobrevive reinicio.
M-3 ✅ PASS — State Hub append-only y proyecciones regeneradas desde `BITACORA.jsonl`.
M-4 ⚠️ PASS parcial — grafo SQLite fallback probado; Graphiti sin servicio y FalkorDB GAP.
M-5 ⚠️ GAP controlado — Memanto descargado sin contrato runtime verificable; Graphify solo fuente read-only.
M-6 ⚠️ GAP controlado — PostgreSQL, Redis y AgentDB sin servicio/runtime verificable; SQLite cubre fallback.
M-7 ✅ PASS local — reinicio, búsqueda por relación y evento State Hub; 30 pruebas PASS.
H-1 ⏸️ OPUS — puente HF/Bucket fuera del alcance de Manus; no ejecutado.

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
