# HANDOFF — CHAT YAIWES (leer primero si continúas este trabajo)
Actualizado: 2026-09-27 05:45 UTC por Opus. Director: Max.

## Orden de lectura
0. `../01-PLAN/PLAN-DSL-DAG-UI.yaml` (plan T-01..T-10 del panel/chat, consolidado desde el documento subido; revisar `source_fidelity`)
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
Revisión: 26
Proyecto/tarea: `chat-yaiwes` / `UI-T-10`
Estado: **RUNNING**
Fase: `T10_GLOBAL_READBACK`

### Último checkpoint
T-05 contradiction closed by decision B. Remaining GAPs unchanged: T-06 browser API key and INACTIVE Fables panels, T-07 prescribed RDC workflow absent from main, no browser test or screenshots, CI job blocked by account billing lock, Vercel automatic deployment stays disabled. No global PASS declared.

### Siguiente
T-06 HttpOnly session, Fables activation, T-07 RDC workflow
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
