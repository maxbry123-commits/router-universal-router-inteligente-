# HANDOFF — CHAT YAIWES (leer primero si continúas este trabajo)
Actualizado: 2026-09-27 05:45 UTC por Opus. Director: Max.

## Recepción del nuevo plan — 2026-10-01
El Director anunció un plan original de 100 pasos y nuevas mejoras, pero **aún no ha subido el archivo**. Leer primero `CHECKPOINT.json`, `../01-PLAN/PLAN.json` y luego este handoff. El plan de 100 pasos NO está validado ni en ejecución; no inventar pasos. T-06 quedó pausada por la recepción: se encontró overflow horizontal móvil, falta la prueba UI completa, capturas finales, comparación FROMTED y segunda pasada. No declarar PASS ni entregar HTML antes de completar la validación.

Protocolo de reanudación: recibir el enlace del Director; descargar y leer el archivo original completo sin modificarlo; validar sus 100 IDs y dependencias; registrar ruta y SHA-256 en `PLAN.json` y marcarlo `VALIDATED`. Solo entonces ejecutar `python "chat router/03-ESTADO/checkpoint_guard.py" start`. Consultar `status` antes de cada paso y `tick --completed ID` después de cada paso verificado; consultar `status` también durante trabajos largos. El guardia sale con código 75 y graba un evento en Bitácora más las proyecciones STATE, Crazy Wall y HANDOFF cuando llega primero a 3 h 45 min desde `start` o a 95 de 100 pasos. El límite de cuatro horas es absoluto: parar antes de él, hacer read-back, guardar pruebas/archivos/errores/decisiones/estado de motores en `CHECKPOINT.json`, commit y push a la rama del PR. No seguir ejecutando al recibir 75. El guardia no se ejecuta por sí solo fuera de una sesión o proceso que lo invoque.

Estado previo al nuevo plan: T-01..T-04 y T-08..T-09 completos según State Hub; T-05, T-06 y T-10 parciales; T-07 bloqueado. La auditoría de GET sigue la decisión B. El PR existente es https://github.com/maxbry123-commits/router-universal-router-inteligente-/pull/6; no crear otro. Vercel permanece apagado. La siguiente acción exacta es recibir el enlace, validar el original y recién entonces iniciar el reloj. Durante trabajo activo, invocar `python "chat router/03-ESTADO/checkpoint_guard.py" heartbeat` al menos cada 15 minutos: registra el evento append-only y verifica las proyecciones, incluso si el plan continúa en recepción. No existe temporizador independiente cuando el agente deja de trabajar.

### Auditoría Manus y organización T-01 — 2026-10-01
Código localizado: `../04-MEMORIA/memoria_yaiwes/__init__.py` y `../../router inteligente universal/integration/chat_mvp/memoria_loader.py`. Se comprobaron SQLite y grafo SQLite de respaldo con 8/8 pruebas focalizadas (`PYTHONPATH` del Router y de `04-MEMORIA`); `/memoria/*` está montado. `/chat/send` persiste mensajes en `Store` pero no llama a `memoria_yaiwes.save`, por lo que el microflujo completo del DSL sigue abierto. Graphiti y Graphify son código fuente descargado, sin servicio operativo demostrado; FalkorDB y AgentDB están `EXTRACTED_VERIFIED` en `RDC_ADDITIONAL_COMPONENTS_EVIDENCE.json`, pero tampoco están conectados. El inventario `MEMORIA-INVENTARIO.json` es un snapshot del 27-sep: conserva `GAP_ABSENT` previo a esa descarga; interpretar con la evidencia posterior y no como afirmación actual. Memanto, PostgreSQL, Redis y restauración HF H-1 siguen sin read-back funcional.

Una segunda pasada de T-01 consolidó 38 archivos sueltos de referencias visuales, skills, manifiestos, scripts y laboratorio FROMTED en `../../📂 Skills Maxbry UI fromtend/diseno/` y `componentes/`. Git reconoce 37 renames 100 %; el README Rare UI original se conserva como copia con SHA-256 idéntico y el README raíz es ahora un índice del proyecto. Las imágenes de arquitectura permanecen junto a los diagramas del Router. Esto solo cierra la consolidación de archivos, no la validación visual de T-06; el laboratorio visual movido no se declara funcional. La próxima acción autorizada, mientras no llegue el nuevo plan, es documentar/verificar esta auditoría y registrar checkpoint; al llegar el enlace, validar el original antes de iniciar el reloj.

### Continuación T-06 y método aprobado — 2026-10-01
P01–P08 se formalizaron en `../01-PLAN/DM-METODO-DAG.json` y se verifican mediante `../11-EVIDENCIA/auditoria_metodo.py`; la presencia del contrato no acredita Sentinel, Hermes ni OpenClaw conectados. 65 imágenes se trasladaron a `../01-PLAN/REFERENCIAS-UI/` y se catalogaron individualmente, aún sin vincularse a componentes vivos ni revisión completa de secretos. Se agruparon T-11/T-12 y seis anexos originales. En `../01-PLAN/T-06-INVENTARIO.md` se enumeran controles, estados y dependencias; todos están pendientes de prueba real. El frontend ya no contiene campo ni variable de clave. `integration/chat_mvp/app.py` añade desafío Basic del navegador para assets UI con `RIU_ROUTER_API_KEY` y adapta las solicitudes al backend actual; la prueba local verifica 401/200 pero falta comprobar credenciales, consola, red, storage y responsive en navegador. No entregar al Director la prueba sin segunda pasada completa y matriz final. El plan nuevo continúa sin 100 pasos validados y reloj detenido.

Reanudación exacta: el PR #6 ya contiene el commit `9751dda766`. La selección focalizada tuvo 35 PASS y un FAIL: un test antiguo espera ocho proveedores y el API devuelve también `openai`; no se cambió la prueba ni el proveedor. El agente de prueba UI se intentó dos veces tras actualizar el PR; ambos intentos terminaron con `You've reached your ChatGPT subscription usage limit` sin ejecutar acciones, grabación, capturas ni segunda pasada. Reanudar el testing_agent cuando haya cupo disponible, revisar toda la matriz T-06 y reparar los fallos que encuentre. No inferir PASS ni entregar HTML al Director. GitHub Actions `verify` tampoco arrancó: su anotación de GitHub dice que la cuenta está bloqueada por un problema de facturación; el resultado no representa ejecución de tests.

Orden posterior del Director: utilizar Hugging Face con `cpu-basic` (16 GB de RAM) para el cómputo de validación; no utilizar GitHub Actions. La dirección del Router permanente se lee de `router inteligente universal/agents-yaiwes/ROUTER_JOB_PAUSE.flag` en cada intento. El Director autorizó relanzarlo solo si está inactivo. Historial verificado: `cd735423ae` cambió LIVE_URL al Job `6abdc1b4404719ba376155b0` y `5e52e64d5d` amplió los secretos/env del guardian. Con token HF temporal entregado por canal seguro, `HfApi.inspect_job` confirmó `RUNNING`, flavor `cpu-basic`, y `GET /health` devolvió 200 el 2026-10-01; `/chat/providers` y `/v1/models` devolvieron 200. **No se reinició el Router permanente.** No almacenar ni copiar el token a estos archivos. `origin/main` aún no contiene `chat router/ui/shell.html`: esa ruta devuelve 404 en el Router permanente y T-06 permanece solo en el PR.

Verificación temporal en Hugging Face Jobs, sin secretos inyectados al Job: `6abe68d3404719ba3761892f` ejecutó en `cpu-basic` una copia dispersa de la rama del PR con `SIMULADO=1`; terminaron 30/30 pruebas focalizadas en `COMPLETED` (org API, checkpoint, auditoría de método y Puerta). Dos Jobs preparatorios fallaron por excluir directorios requeridos en la copia dispersa, no por un fallo demostrado en el checkout completo. El agente de pruebas de navegador volvió a terminar por límite de uso antes de abrir la UI (tercer intento total). No existen capturas ni segunda pasada: T-06 sigue `PARTIAL` y no se entrega HTML/URL como interfaz validada. Próxima acción T-06: recuperar capacidad de prueba en navegador, desplegar o servir la revisión del PR, ejecutar la matriz de controles/estados/responsive y repetir la pasada completa antes de declarar PASS.

Vercel no se utilizó: la página del proyecto redirige a login y no hay integración Vercel conectada a esta sesión. La integración de GitHub respondió 403 al solicitar los nombres de secretos Actions, por lo que no se confirmó ningún token Vercel. El comentario del PR sobre cuota diaria es histórico; no se verificó el límite actual. El backend sigue parcial: faltan el guardado normal de chat en memoria, read-back y restauración HF, y evidencia de Graphiti/Graphify activos. El plan original de 100 pasos continúa sin recibir/validar, con el reloj detenido.

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
Revisión: 40
Proyecto/tarea: `chat-yaiwes` / `PLAN-RECEPCION`
Estado: **BLOCKED**
Fase: `AWAITING_PLAN`

### Último checkpoint
Router HF 6abdc1b4404719ba376155b0 autenticado RUNNING cpu-basic, health 200; sin reinicio. Job temporal 6abe68d3404719ba3761892f completo con 30/30 pruebas focalizadas. T-06 UI bloqueada por limite del agente de pruebas; plan 100 pasos en recepcion.

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
