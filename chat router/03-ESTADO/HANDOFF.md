# HANDOFF — CHAT YAIWES (leer primero si continúas este trabajo)
Actualizado: 2026-09-27 05:45 UTC por Opus. Director: Max.

## Recepción del nuevo plan — 2026-10-01
El Director anunció un plan original de 100 pasos y nuevas mejoras, pero **aún no ha subido el archivo**. Leer primero `CHECKPOINT.json`, `../01-PLAN/PLAN.json` y luego este handoff. El plan de 100 pasos NO está validado ni en ejecución; no inventar pasos. T-06 quedó pausada por la recepción: se encontró overflow horizontal móvil, falta la prueba UI completa, capturas finales, comparación FROMTED y segunda pasada. No declarar PASS ni entregar HTML antes de completar la validación.

Protocolo de reanudación: recibir el enlace del Director; descargar y leer el archivo original completo sin modificarlo; validar sus 100 IDs y dependencias; registrar ruta y SHA-256 en `PLAN.json` y marcarlo `VALIDATED`. Solo entonces ejecutar `python "chat router/03-ESTADO/checkpoint_guard.py" start`. Consultar `status` antes de cada paso y `tick --completed ID` después de cada paso verificado; consultar `status` también durante trabajos largos. El guardia sale con código 75 y graba un evento en Bitácora más las proyecciones STATE, Crazy Wall y HANDOFF cuando llega primero a 3 h 45 min desde `start` o a 95 de 100 pasos. El límite de cuatro horas es absoluto: parar antes de él, hacer read-back, guardar pruebas/archivos/errores/decisiones/estado de motores en `CHECKPOINT.json`, commit y push a la rama del PR. No seguir ejecutando al recibir 75. El guardia no se ejecuta por sí solo fuera de una sesión o proceso que lo invoque.

Estado previo al nuevo plan: T-01..T-04 y T-08..T-09 completos según State Hub; T-05, T-06 y T-10 parciales; T-07 bloqueado. La auditoría de GET sigue la decisión B. El PR existente es https://github.com/maxbry123-commits/router-universal-router-inteligente-/pull/6; no crear otro. Vercel permanece apagado. La siguiente acción exacta es recibir el enlace, validar el original y recién entonces iniciar el reloj.

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
Revisión: 27
Proyecto/tarea: `chat-yaiwes` / `PLAN-RECEPCION`
Estado: **BLOCKED**
Fase: `AWAITING_PLAN`

### Último checkpoint
Modo recepcion: plan de 100 pasos sin subir; T-06 pausada; sin PASS visual. Reloj sin iniciar.

### Siguiente
Recibir plan original
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
