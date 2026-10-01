# HANDOFF — CHAT YAIWES (leer primero si continúas este trabajo)
Actualizado: 2026-09-27 05:45 UTC por Opus. Director: Max.

## Recepción del nuevo plan — 2026-10-01
El Director anunció un plan original de 100 pasos y nuevas mejoras, pero **aún no ha subido el archivo**. Leer primero `CHECKPOINT.json`, `../01-PLAN/PLAN.json` y luego este handoff. El plan de 100 pasos NO está validado ni en ejecución; no inventar pasos. T-06 quedó pausada por la recepción: se encontró overflow horizontal móvil, falta la prueba UI completa, capturas finales, comparación FROMTED y segunda pasada. No declarar PASS ni entregar HTML antes de completar la validación.

Protocolo de reanudación: recibir el enlace del Director; descargar y leer el archivo original completo sin modificarlo; validar sus 100 IDs y dependencias; registrar ruta y SHA-256 en `PLAN.json` y marcarlo `VALIDATED`. Solo entonces ejecutar `python "chat router/03-ESTADO/checkpoint_guard.py" start`. Consultar `status` antes de cada paso y `tick --completed ID` después de cada paso verificado; consultar `status` también durante trabajos largos. El guardia sale con código 75 y graba un evento en Bitácora más las proyecciones STATE, Crazy Wall y HANDOFF cuando llega primero a 3 h 45 min desde `start` o a 95 de 100 pasos. El límite de cuatro horas es absoluto: parar antes de él, hacer read-back, guardar pruebas/archivos/errores/decisiones/estado de motores en `CHECKPOINT.json`, commit y push a la rama del PR. No seguir ejecutando al recibir 75. El guardia no se ejecuta por sí solo fuera de una sesión o proceso que lo invoque.

Estado previo al nuevo plan: T-01..T-04 y T-08..T-09 completos según State Hub; T-05, T-06 y T-10 parciales; T-07 bloqueado. La auditoría de GET sigue la decisión B. El PR existente es https://github.com/maxbry123-commits/router-universal-router-inteligente-/pull/6; no crear otro. Vercel permanece apagado. La siguiente acción exacta es recibir el enlace, validar el original y recién entonces iniciar el reloj. Durante trabajo activo, invocar `python "chat router/03-ESTADO/checkpoint_guard.py" heartbeat` al menos cada 15 minutos: registra el evento append-only y verifica las proyecciones, incluso si el plan continúa en recepción. No existe temporizador independiente cuando el agente deja de trabajar.

### Auditoría Manus y organización T-01 — 2026-10-01
Código localizado: `../04-MEMORIA/memoria_yaiwes/__init__.py` y `../../router inteligente universal/integration/chat_mvp/memoria_loader.py`. Se comprobaron SQLite y grafo SQLite de respaldo con 8/8 pruebas focalizadas (`PYTHONPATH` del Router y de `04-MEMORIA`); `/memoria/*` está montado. `/chat/send` persiste mensajes en `Store` pero no llama a `memoria_yaiwes.save`, por lo que el microflujo completo del DSL sigue abierto. Graphiti y Graphify son código fuente descargado, sin servicio operativo demostrado; FalkorDB y AgentDB están `EXTRACTED_VERIFIED` en `RDC_ADDITIONAL_COMPONENTS_EVIDENCE.json`, pero tampoco están conectados. El inventario `MEMORIA-INVENTARIO.json` es un snapshot del 27-sep: conserva `GAP_ABSENT` previo a esa descarga; interpretar con la evidencia posterior y no como afirmación actual. Memanto, PostgreSQL, Redis y restauración HF H-1 siguen sin read-back funcional.

Una segunda pasada de T-01 consolidó 38 archivos sueltos de referencias visuales, skills, manifiestos, scripts y laboratorio FROMTED en `../../📂 Skills Maxbry UI fromtend/diseno/` y `componentes/`. Git reconoce 37 renames 100 %; el README Rare UI original se conserva como copia con SHA-256 idéntico y el README raíz es ahora un índice del proyecto. Las imágenes de arquitectura permanecen junto a los diagramas del Router. Esto solo cierra la consolidación de archivos, no la validación visual de T-06; el laboratorio visual movido no se declara funcional. La próxima acción autorizada, mientras no llegue el nuevo plan, es documentar/verificar esta auditoría y registrar checkpoint; al llegar el enlace, validar el original antes de iniciar el reloj.

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
Revisión: 32
Proyecto/tarea: `chat-yaiwes` / `PLAN-RECEPCION`
Estado: **BLOCKED**
Fase: `AWAITING_PLAN`

### Último checkpoint
Read-back T-01: 37 renames 100% y README Rare UI original conservado con SHA-256 identico; 38 archivos consolidados. Auditoria Manus: SQLite/grafo fallback 8/8; Graphiti/Graphify fuente, FalkorDB/AgentDB fuente RDC sin runtime; /chat/send no invoca memoria. Borrador separa 7 etapas reales de programación de 12 goals, 12 ASK, 4 simulaciones y 3 refutaciones propuestas; reglas sin activar. T-06 sin PASS; plan nuevo sin recibir; reloj sin iniciar.

### Siguiente
Recibir plan original
<!-- YAIWES STATE HUB END -->

## Checkpoints DSL memoria/almacenamiento — RIU-0121
M-0 ✅ PASS histórico — inventario de 13 componentes de 27-sep; FalkorDB y AgentDB figuran ausentes en aquel snapshot, pero el RDC posterior verifica su fuente descargada.
M-1 ✅ PASS — `chat router/04-MEMORIA/memoria_yaiwes/` y único loader `memoria_loader.py`; rutas `/memoria/*` fail-safe.
M-2 ✅ PASS — SQLite existente reutilizado como fuente principal; memoria sobrevive reinicio.
M-3 ✅ PASS — State Hub append-only y proyecciones regeneradas desde `BITACORA.jsonl`.
M-4 ⚠️ PASS parcial — grafo SQLite fallback probado; Graphiti sin servicio y FalkorDB con fuente descargada, sin runtime conectado.
M-5 ⚠️ GAP controlado — Memanto descargado sin contrato runtime verificable; Graphify solo fuente read-only.
M-6 ⚠️ GAP controlado — PostgreSQL y Redis sin servicio, AgentDB descargado sin runtime verificable; SQLite cubre fallback.
M-7 ✅ PASS local — reinicio, búsqueda por relación y evento State Hub; 30 pruebas PASS.
H-1 ⏸️ OPUS — puente HF/Bucket fuera del alcance de Manus; no ejecutado.
