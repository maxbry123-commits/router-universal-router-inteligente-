# HANDOFF — MAPA DE UBICACIÓN WORKFLOW WORDFLOW LOOP CODE YAIWES (corte 2026-10-07)

## Raíz del código wordflow en esta rama (`devin/1790824641-chat-agent-plan`, PR #6)
- CANÓNICA / vigente: `chat router/📂 workflow Loops code Yaiwes/` — 494 archivos; último toque 2026-10-04 (`49fa83ae57`). Contiene `runtime/`, `wordflow_loop/`, `backend/`, `minimax_mcp/`, `skills_schema/`, `workspace/`, `Crazy Wall Orquestador/`, `HANDOFF.md` interno, `GUIA-MAESTRA-EJECUCION-LOOP-V4-WORDFLOW-YAIWES.md`, `PLAN-4-OBJETIVOS/`, `PLAN-PROGRAMACION-11-OBJETIVOS-Y-AGENTES.md`, `README-ARQUITECTURA-BACKEND.md`.
- Copia anterior (1-oct, 450 archivos): `chat router/wordflow loop code Yaiwes/` — copia vía motor_3 (`b214f9fe96`, 397 VERIFIED_CLOSED; excluye `wordflow_loop/agent_sources` y `frontend/Orca` por orden del Director). Último toque `b384864666` (S-07A motores como Native Toolset).
- Sólo motores (7 archivos): `chat router/➡️📂 Wordflow LOOP Yaiwes/` y `chat router/➡️📂motores de descarga extracción copiado movimiento archivos agentes/`.

## Origen de la copia (repo `maxbry123-commits/agentes`)
- Raíz real: `➡️📂 wordflow loop code Yaiwes/` (~154k files). Las raíces homónimas `wordflow loop code Yaiwes/` (vacía) y `➡️📂 Wordflow LOOP Yaiwes/` (remanente, sólo `wordflow_loop/agent_sources`) NO contienen el código.

## Estado y continuidad (esta rama, `chat router/`)
- `03-ESTADO/` — `STATE.json` (rev 71, 2026-10-04, proyecto activo `router-inteligente-universal`), `CRAZY_WALL.json`, `BITACORA.jsonl`, `CHECKPOINT.json`, `memoria.md`, `checkpoint_guard.py`, `watchdog_checkpoint.py`, `OPUS-PENDIENTE.md`.
- `01-PLAN/` — `INDICE.md`, `PLAN-ACCION-XRAY.md`, `ROOT-MAP-T11.yaml`, `DM-METODO-DAG.json`, contratos DSL-DAG (`PLAN-DSL-DAG-00-CONTRATO.yaml`, `-01-NODOS.yaml`, `-UI.yaml`, `DSL-DAG-MEMORIA-ALMACENAMIENTO.yaml`), INPUT-BLOCK verbatim (3 partes), `PLAN-MAESTRO-CHAT.yaml`, `ORQUESTADOR-DE-TRABAJO.yaml`, `SKILLS-MAXBRY-UI/`, `REFERENCIAS-UI/`.
- `02-ARQUITECTURA/`, `04-MEMORIA/` (memoria_yaiwes), `05-AGENTES/` (gobierno), `06-ESPEJOS/`, `07-SENTINELAS/`, `09-CLAUDE-CODE/`, `10-CHAT-FUNCIONES/`, `11-EVIDENCIA/` (puerta, auditoría de método, motor2), `12-FABRICA-MOTORES/`, `13-CHAT-UI-SUITE/`, `harness plugins/`, `deepseek-harness-chat/` (harness base), `chat_orders/`, `space/`.
- Frontend movido a `main`: `chat router/chat frontend/` (commit `d269acf982`); el Router ya no depende de la carpeta de interfaz de esta rama.

## Commits clave de copiado/integración (todos en PR #6)
`f4bd367c9c` crear raíz router Wordflow LOOP → `b214f9fe96` copia vía motor_3 → `0e36940f6d` wiring tests+motores+ROOT-MAP 11 → `ba5c9668c4` task_runtime loop core → `f54ae17b06` watchdog → `590eb73303` INPUT-BLOCK + delta N-2.x → `b384864666` S-07A motores toolset → `fd4e9646d1`/`49fa83ae57` estado evento 71 + alinear pruebas (4-oct).

## Cómo correr
- venv `~/.venv-riu`; tests: `cd "chat router/📂 workflow Loops code Yaiwes" && pytest runtime/tests -q` (conftest fija PYTHONPATH; suite propia 267+ pass, stale upstream marcado como flag).
- Checkpoint: `python "chat router/03-ESTADO/watchdog_checkpoint.py" --summary "..."` / heartbeat `checkpoint_guard.py` cada 15 min durante trabajo activo.
- NO está en `main`: el wordflow vive sólo en la rama del PR #6.

---

# HANDOFF — CORTE 2026-10-01 (para el próximo Devin, retoma en ~3 días)

## Leer primero, en este orden
1. `chat router/03-ESTADO/memoria.md` — contexto COMPLETO: reglas del Director, estado técnico verificado, pendientes como DSL-DAG (P1..P8), gotchas de VM.
2. `chat router/01-PLAN/PLAN-ACCION-XRAY.md` — mapa nodo→estado de los 4 objetivos + INPUT-BLOCK verbatim (incluye la orden de base: deepseek-harness=base que conecta todo, Hermes+OpenClaw=base permanente del chat, NO eliminar).
3. `chat router/01-PLAN/ROOT-MAP-T11.yaml` — raíces canónicas.
4. STATE.json / CRAZY_WALL.json / BITACORA.jsonl en esta misma carpeta.

## Dónde quedó
- Backend ~70%: wordflow copiado (397 archivos VERIFIED_CLOSED), recovery tipado, agent_router FAIL_CLOSED, LayerRunner+governance, ThinkingSystem, dedup canónico, SealsWorker+agent-45, orchestrator contracts+adapters+ledger+oracle gate, O4-19 E2E, skills_schema 24, seals_motors toolset, 6 descargas motor_2 VERIFIED_CLOSED publicadas en esta rama.
- Pendiente siguiente sesión: P1 invocación real adapters O4-07..14 (configurar command_env), P2 cablear las 4 capabilities descargadas, P3 S-11/S-12, P4 O4-17/O4-20, P5-P7 flags (frontend gate no tocar hasta backend cerrado).

## Cómo correr
- venv `~/.venv-riu`; tests loop: `cd "chat router/wordflow loop code Yaiwes" && pytest runtime/tests -q` (conftest fija PYTHONPATH). 267 pass / 3 stale upstream.
- Checkpoint: `python "chat router/03-ESTADO/watchdog_checkpoint.py" --summary "..."`.

---

# HANDOFF — CHAT YAIWES (leer primero si continúas este trabajo)
Actualizado: 2026-09-27 05:45 UTC por Opus. Director: Max.

## Aclaración del plan y checkpoint — 2026-10-01
El Director dibujó «PLAN ORIGINAL — 100 tareas/pasos» como ejemplo del método de parada y recuperación en su mensaje de modo recepción. Devin interpretó erróneamente que habría otro archivo con exactamente 100 pasos por subir y lo pidió repetidamente. **No hay evidencia de ese archivo adicional ni obligación de entregarlo.** Los contratos y DAG T-01..T-12 ya están en `../01-PLAN/`; continuar esas tareas según su estado. Leer primero `CHECKPOINT.json`, el índice del plan y luego este handoff. T-06 requiere prueba UI completa, capturas finales, comparación FROMTED y segunda pasada; no declarar PASS ni entregar HTML antes de completar la validación.

Guardia de tiempo: `checkpoint_guard.py` exige hoy 100 IDs, fuente y SHA-256 antes de `start`; es una implementación condicionada por aquella interpretación, no una condición para ejecutar los DAG existentes. Mantener su reloj en cero; para aplicarlo a T-01..T-12 hay que mapear pasos y dependencias reales, acordar la unidad de avance y probar la parada al 95 %. Durante trabajo activo invocar `heartbeat` cada 15 minutos, con read-back de Bitácora, STATE, Crazy Wall y HANDOFF. El guardia no es un temporizador autónomo cuando no se invoca. Una ejecución válida debe parar limpiamente a las 3 h 45 min o al 95 % de su plan validado y guardar pruebas, cambios, errores, decisiones, motores y siguiente acción antes del límite absoluto de cuatro horas.

Actualización más reciente: el inventario del plan conserva 30 documentos y 82 skills con procedencia comprobada, 65 referencias principales, 5 diagramas y 12 capturas (82 imágenes con hash físico comprobado). La pasada post-código cubre 19 archivos; 68 pruebas focalizadas pasan, una prueba de proveedores se excluye por divergencia conocida y Ruff pasa. En la suite ampliada del Router/memoria hay 371 passed, 5 failed y 1 deselected tras instalar la dependencia declarada del vault (`cryptography==48.0.0`) y el plugin de tests asíncronos; las 23 pruebas aisladas de conectores/banco pasan. Fallan E2E GitHub con 502 y cuatro expectativas de configuración/modelos que no coinciden con archivos vigentes; ver PLAN-ACCION-XRAY. El test simulado T-11 se ejecuta separado por la bandera de import. El chat ya guarda cada turno normal vía fachada SQLite con read-back y scope por propietario; los párrafos históricos de abajo que lo describen como pendiente reflejan un estado anterior. T-11-B rechaza claims inválidos y hash falso, y exige actor coherente en receipts; T-11-C añadió compilación tipada, checksum de paquete y observaciones tipadas por adaptador. Un fallo GitHub deja resultados locales y obliga `INCOMPLETE`. La Puerta comprueba la suma de control sobre hechos, fuentes, parser, consultas y observaciones; cada hecho requiere una fuente presente. Esto no autentica revisores. T-11-D inició event replay: eventos nuevos llevan ID y hash validado, se recupera un snapshot ausente localmente y la escritura de Bitácora exige read-back. El historial anterior aún no está autenticado. La búsqueda local comprueba un plazo entre archivos, sin cancelación dura de E/S. 🚩 PENDIENTE: identidad independiente, timeout duro de búsqueda local, integridad remota del historial, lease/recovery, adapters externos, HF restore, OpenAI real y T-06 visual. Siguiente acción exacta: cerrar T-11-C con cancelación local segura y procedencia de hechos; luego terminar integridad/convergencia remota del event replay. GitHub Actions no se usa como evidencia.

Estado del DAG existente: T-01..T-04 y T-08..T-09 completos según State Hub; T-05, T-06 y T-10 parciales; T-07 bloqueado. La auditoría de GET sigue la decisión B. El PR existente es https://github.com/maxbry123-commits/router-universal-router-inteligente-/pull/6; no crear otro. Vercel permanece apagado. Siguiente acción: continuar pendientes del DAG sin esperar un archivo hipotético. Durante trabajo activo, invocar `python "chat router/03-ESTADO/checkpoint_guard.py" heartbeat` al menos cada 15 minutos; registra el evento append-only y verifica las proyecciones.

### Auditoría Manus y organización T-01 — 2026-10-01
Código localizado: `../04-MEMORIA/memoria_yaiwes/__init__.py` y `../../router inteligente universal/integration/chat_mvp/memoria_loader.py`. Se comprobaron SQLite y grafo SQLite de respaldo con 8/8 pruebas focalizadas (`PYTHONPATH` del Router y de `04-MEMORIA`); `/memoria/*` está montado. `/chat/send` persiste mensajes en `Store` pero no llama a `memoria_yaiwes.save`, por lo que el microflujo completo del DSL sigue abierto. Graphiti y Graphify son código fuente descargado, sin servicio operativo demostrado; FalkorDB y AgentDB están `EXTRACTED_VERIFIED` en `RDC_ADDITIONAL_COMPONENTS_EVIDENCE.json`, pero tampoco están conectados. El inventario `MEMORIA-INVENTARIO.json` es un snapshot del 27-sep: conserva `GAP_ABSENT` previo a esa descarga; interpretar con la evidencia posterior y no como afirmación actual. Memanto, PostgreSQL, Redis y restauración HF H-1 siguen sin read-back funcional.

Una pasada anterior de T-01 consolidó 38 archivos de referencias visuales, skills, manifiestos, scripts y laboratorio FROMTED en una carpeta de skills separada. La corrección posterior la movió íntegra bajo `../01-PLAN/SKILLS-MAXBRY-UI/`; las 65 referencias UI están en `../01-PLAN/REFERENCIAS-UI/`, los 5 diagramas del Router en `ARQUITECTURA-ROUTER/` y los 11 adjuntos del chat en `ADJUNTOS-CHAT/`. Los tres documentos sueltos no canónicos del plan fueron agrupados en `ANEXOS/`. Los catálogos cuentan las 81 imágenes sin declarar conexión runtime. El movimiento de archivos no demuestra T-06 ni runtime.

### Continuación T-06 y método aprobado — 2026-10-01
P01–P08 se formalizaron en `../01-PLAN/DM-METODO-DAG.json` y se verifican mediante `../11-EVIDENCIA/auditoria_metodo.py`; la presencia del contrato no acredita Sentinel, Hermes ni OpenClaw conectados. 65 imágenes se trasladaron a `../01-PLAN/REFERENCIAS-UI/` y se catalogaron individualmente, aún sin vincularse a componentes vivos ni revisión completa de secretos. Se agruparon T-11/T-12 y seis anexos originales; el índice del plan documenta el cotejo de 30 archivos en el enlace del Director. En `../01-PLAN/T-06-INVENTARIO.md` se enumeran controles, estados y dependencias; todos están pendientes de prueba real. El frontend ya no contiene campo ni variable de clave. `integration/chat_mvp/app.py` añade desafío Basic del navegador para assets UI con `RIU_ROUTER_API_KEY` y adapta las solicitudes al backend actual; la prueba local verifica 401/200 pero falta comprobar credenciales, consola, red, storage y responsive en navegador. No entregar al Director la prueba sin segunda pasada completa y matriz final.

Reanudación exacta: el PR #6 ya contiene el commit `9751dda766`. La selección focalizada tuvo 35 PASS y un FAIL: un test antiguo espera ocho proveedores y el API devuelve también `openai`; no se cambió la prueba ni el proveedor. El agente de prueba UI se intentó dos veces tras actualizar el PR; ambos intentos terminaron con `You've reached your ChatGPT subscription usage limit` sin ejecutar acciones, grabación, capturas ni segunda pasada. Reanudar el testing_agent cuando haya cupo disponible, revisar toda la matriz T-06 y reparar los fallos que encuentre. No inferir PASS ni entregar HTML al Director. GitHub Actions `verify` tampoco arrancó: su anotación de GitHub dice que la cuenta está bloqueada por un problema de facturación; el resultado no representa ejecución de tests.

Orden posterior del Director: utilizar Hugging Face con `cpu-basic` (16 GB de RAM) para el cómputo de validación; no utilizar GitHub Actions. La dirección del Router permanente se lee de `router inteligente universal/agents-yaiwes/ROUTER_JOB_PAUSE.flag` en cada intento. El Director autorizó relanzarlo solo si está inactivo. Historial verificado: `cd735423ae` cambió LIVE_URL al Job `6abdc1b4404719ba376155b0` y `5e52e64d5d` amplió los secretos/env del guardian. Con token HF temporal entregado por canal seguro, `HfApi.inspect_job` confirmó `RUNNING`, flavor `cpu-basic`, y `GET /health` devolvió 200 el 2026-10-01; `/chat/providers` y `/v1/models` devolvieron 200. **No se reinició el Router permanente.** No almacenar ni copiar el token a estos archivos. `origin/main` aún no contiene `chat router/ui/shell.html`: esa ruta devuelve 404 en el Router permanente y T-06 permanece solo en el PR.

Verificación temporal en Hugging Face Jobs, sin secretos inyectados al Job: `6abe68d3404719ba3761892f` ejecutó en `cpu-basic` una copia dispersa de la rama del PR con `SIMULADO=1`; terminaron 30/30 pruebas focalizadas en `COMPLETED` (org API, checkpoint, auditoría de método y Puerta). Dos Jobs preparatorios fallaron por excluir directorios requeridos en la copia dispersa, no por un fallo demostrado en el checkout completo. El agente de pruebas de navegador volvió a terminar por límite de uso antes de abrir la UI (tercer intento total). No existen capturas ni segunda pasada: T-06 sigue `PARTIAL` y no se entrega HTML/URL como interfaz validada. Próxima acción T-06: recuperar capacidad de prueba en navegador, desplegar o servir la revisión del PR, ejecutar la matriz de controles/estados/responsive y repetir la pasada completa antes de declarar PASS.

Vercel no se utilizó: la página del proyecto redirige a login y no hay integración Vercel conectada a esta sesión. La integración de GitHub respondió 403 al solicitar los nombres de secretos Actions, por lo que no se confirmó ningún token Vercel. El comentario del PR sobre cuota diaria es histórico; no se verificó el límite actual. El backend sigue parcial: faltan el guardado normal de chat en memoria, read-back y restauración HF, y evidencia de Graphiti/Graphify activos. El reloj auxiliar de 100 pasos está inactivo, sin bloquear el trabajo existente.

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
Revisión: 71
Proyecto/tarea: `router-inteligente-universal` / `ROUTER-UNIVERSAL`
Estado: **COMPLETED**
Fase: `VERIFIED_IN_PRODUCTION`

### Último checkpoint
Router relanzado con validar/probar fichas; 1000 conexiones simultaneas 1000/1000; memoria 1000/1000 aislada por token; candado del Director OK; banco con 42 claves (tokens GitHub/HF del Director guardados); tokens de prueba borrados. Docs: router inteligente universal/MANUAL-AGENTES.md, HANDOFF-FICHA.md, Banco de claves/HANDOFF-BANCO.md, HANDOFF-ROUTER-UNIVERSAL-OPUS.md (commit fdbb67f).

### Siguiente
Director: orden final del repo y primera ficha (HANDOFF-FICHA.md)
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
