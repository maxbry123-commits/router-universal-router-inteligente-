# CHAT 1 | Backend DSL/DAG YAIWES — Contrato frontend
Ruta autenticada existente: `POST /plugins/nct_loop/call/<accion>`.
El servidor devuelve `{"status":"ok","result":{...}}`; errores de contrato en `result.ok=false`.
Sin infraestructura ni puerta adicional. No editar frontend desde este backend.

## Acciones
- `dsl_config`: `contract_validate`, `trigger_upsert`, `trigger_toggle`, `trigger_remove`, `anchor_bind`, `note_update`, `loop_save`, `roles_save`.
- `dsl_control`: `start`, `pause`, `resume`, `cancel`, `run_one`, `approve`, `next_loop`, `retry_safe` (bloqueado hasta reconciliación).
- `dsl_estado`: `health`, `get`, `flags`, `events`, `checkpoint`.

## Ejemplos
`{"project_id":"PROYECTO","loop_id":"LOOP-001","sesion":"web-general","op":"get"}` -> `dsl_estado`.
`{"project_id":"PROYECTO","loop_id":"LOOP-001","sesion":"web-general","op":"trigger_upsert","expected_revision":0,"contract":{...}}` -> `dsl_config`.
`{"project_id":"PROYECTO","loop_id":"LOOP-001","sesion":"web-general","op":"start","expected_revision":1,"duration_minutes":60}` -> `dsl_control`.
`{"project_id":"PROYECTO","loop_id":"LOOP-001","sesion":"web-general","op":"run_one","trigger_id":"T001"}` -> `dsl_control`.

La UI debe registrar antes el proyecto mediante el control `proyecto` del chat; la sesión debe pertenecer al proyecto si este restringe chats. Cada modificación requiere `expected_revision`; conflictos se devuelven como `REVISION_CONFLICT`.

## Seguridad, límites, estados
Hasta 100 triggers por LOOP, verificando DAG, hash del bloque INPUT VERBATIM y anclas existentes.
OFF de T00 no desactiva guard constitucional; sin conexión real al banco HF o proveedor se bloquea.
La cola CIT-50 mantiene modo legado y un modo `dsl` explícito (no corre su worker legado).
El watchdog es observador, no ejecutor. El modelo no puede llamar tools nativas dentro del trigger.
`roles_save` valida los cinco pares modelo/agente con el selector real del backend.
`approve` exige operador verificado con `RIU_SWE_APROBADORES` y coincidencia `RIU_DSL_DIRECTOR`, más `command:"/aprobar"`.
Escrituras N4 de DSL siguen `AUTHORIZED_GITHUB_WRITER_NOT_CONNECTED`: no declarar publicación automática.
`retry_safe` sigue bloqueado hasta reconciliación de efectos; no repetir side-effects inciertos.
Estados del motor: `PASS`, `OFF`, `BLOCKED`, `PARTIAL`, `NEEDS_RECONCILIATION`, `QUEUED`, `NOT_APPLICABLE`.
No envíe `authenticated_by_host`, `host_context` ni `previous` desde navegador.


## Control de seguridad DSL — 2026-11-01 (X-Ray posterior)

La cola DSL reutiliza `cola50` en modo `dsl` (hasta 100 slots sin alterar el máximo histórico 50). El backend limita los claims a **una tarea RUNNING por cola**, bloquea nuevos claims después del vencimiento del watchdog/cola y no reintenta automáticamente operaciones de resultado incierto. Los leases vencidos se marcan `needs_reconciliation`; el operador debe revisar evidencia antes de crear otro trabajo. Una cancelación que ocurre mientras corre el modelo **nunca** debe mostrar un `PASS` del trigger: se contrasta el estado real de la tarea con `succeeded` antes de emitir recibo positivo.

Errores nuevos relevantes para la UI: `QUEUE_BUSY`, `QUEUE_EXPIRED`, `NEEDS_RECONCILIATION` y `QUEUE_COMPLETION_STATE_MISMATCH`. Mostrar `BLOCKED` o el estado real, sin reintentar automáticamente escrituras ni convertir estas condiciones en éxito. La comprobación de entrada es `POST /plugins/nct_loop/call/dsl_estado` con `{\"project_id\":\"...\",\"loop_id\":\"...\",\"op\":\"get\"}` en la puerta autenticada existente.

Pruebas de regresión añadidas dentro de la raíz existente: `chat-router/Loop cola wachdog/Loop/tests/test_trigger_dsl_safety.py`. Son **pruebas a ejecutar en el runner real**, no evidencia de E2E ni de despliegue. Las pruebas DSL anteriores (36/36) se reprodujeron localmente sobre el ZIP aportado; no certifican las nuevas modificaciones del servidor.

**Límites explícitos:** El escritor GitHub N4 continúa `AUTHORIZED_GITHUB_WRITER_NOT_CONNECTED` hasta que el circuito completo /aprobar + autenticación individual + commit + read-back esté probado. El `boot.sh` del Space clona `main` al arrancar, pero leer ese script NO demuestra qué commit está sirviendo ahora; comparar `/health.commit` en producción con el HEAD GitHub antes de declarar `DEPLOY_PASS`.


## V03 backend — Dispatcher y segmentos (2026-11-02)

**Solo las mismas rutas:** `POST /plugins/nct_loop/call/dsl_config`, `/dsl_control` y `/dsl_estado`. El envoltorio HTTP sigue siendo `{"status":"ok","result":{...}}`. Después de `dsl_control {"op":"start","project_id":"P","loop_id":"L","expected_revision":N}`, el plugin programa **un recorrido secuencial** en el `ThreadPoolExecutor` NCT ya existente (no crea otro servicio/daemon). La respuesta indica `result.dispatcher={"scheduled":true,"execution":"EXISTING_NCT_POOL","completed":false}`: programado **no** significa tareas PASS. `resume` reprograma el recorrido cuando la cola vuelve a `running`.

Para continuar explícitamente, `dsl_control {"op":"run_ready","project_id":"P","loop_id":"L","max_steps":100}` usa los mismos permisos y `claim_dsl_for`. Devuelve `processed:[{"id":"T01","status":"PASS","receipt_id":"..."}]` únicamente después del read-back real de CIT; si el DAG no ofrece trigger ejecutable, `{"ok":false,"status":"BLOCKED","error":"NO_ELIGIBLE_TRIGGER",...}`. Una condición `NOT_APPLICABLE` se registra `skipped`, **nunca PASS**. `MAX_STEPS` 1..100; `status=COMPLETED` solo si la cola ya terminó, `LIMIT_REACHED` si todavía quedan tareas. Error/lease incierto: inspección y reconciliación antes de retry, jamás reejecutar escrituras ciegamente.

El `dsl_config {"op":"loop_save","expected_revision":N,"loop_meta":{"name":"...","segments":[{"id":"fase1","name":"Arquitectura","trigger_ids":["T01"]}],"verify_on_end":true,"next_loop_id":"L2"}}` almacena segmentos en la **configuración HF ya existente** (sin nueva DB). Los IDs de segmento son únicos; los triggers deben existir y no repetirse entre segmentos. `dsl_estado {"op":"get","project_id":"P","loop_id":"L"}` añade `phase_index` y `verify_on_end`; conserva `triggers` como **objeto** y `contracts` como **array**. `loop_save` histórico sigue aceptado.

**GAP / BLOQUEO todavía existente:** `next_loop` conserva `dispatched:false` (no hay salto inter-LOOP verificado); `verify_on_end` es configuración, todavía **no** una compuerta automática de revisión final. Writer GitHub N4 sigue `AUTHORIZED_GITHUB_WRITER_NOT_CONNECTED`. No hay prueba E2E de proveedor real; los nuevos `test_trigger_dispatch.py` son MOCK. El ZIP de fuentes originales ECC y del Prompt Maestro 46 secciones indicado por el segundo documento de encargo **no forma parte de los dos adjuntos actuales**, por lo que no se certifica conversión 86 nodos/46 secciones sin esos bytes.


### Mecánico V1 — integración segura (2026-11-02)

La API permanece en `POST /plugins/nct_loop/call/{dsl_config|dsl_control|dsl_estado}`. `dsl_estado`, `op=get`, ahora incluye `mechanico_gaps` (objeto `triggers`, no lista), derivado del recibo real; `NOT_APPLICABLE` con NOTICE no es GAP bloqueante.

Operaciones de consulta (respuesta bajo `{status:'ok',result:{...}}`): `dsl_estado:op=gaps` devuelve el ledger por proyecto, `dsl_estado:op=gap_sources` devuelve referencias. `dsl_control:op=gap_collect` fusiona observaciones entre LOOPs en el HF existente con revisión monotónica y readback. `dsl_control:op=gap_research` ofrece investigación **sin autorización de ejecución**; sus fuentes externas son no confiables.

Flujo de aprobación: `dsl_control:gap_propose` exige `project_id`, `loop_id`, `gap_id`, `expected_revision`, `solutions` y referencias de investigación realmente recuperadas (`source_id,title,url,excerpt,retrieved_ref`) normalizadas. `dsl_control:gap_select_solution` exige además `solution_id`, `bundle_revision_sha256`, `target_loop_id`, cabeceras `x-operador` y `x-operator-token` de Director verificadas por el servidor. La salida es solo `TRIGGER_DRAFT_NOT_EXECUTABLE`, con recibo de selección servidor y readback. Nunca ejecutar una propuesta como trigger sin `validate_contract`, `validate_loop` y autorización de escritura N4 específica.

El escritor GitHub N4 hace `ricardo_plan_guard.inspect_plan()` inmediatamente antes de publicar; mantiene aprobación por contenido SHA, rutas de proyecto, HEAD y readback. `loop_continuity.build_handoff()` produce CRAZY WALL y hash, almacenado/confirmado antes del salto automático si `verify_on_end=false` y todos los recibos están verificados. No añadir nuevas rutas de API ni frontend desde este chat.

**GAP explícito:** la búsqueda existente aún usa el adaptador seguro del backend; no hay prueba de Tool Selector de búsqueda del Harness con las diez fuentes del JSON, por lo que resultados no se pueden certificar como búsqueda Harness. Las pruebas de los motores: 17/17 originales y 18/18 tras la corrección NOTICE en fixtures locales; falta E2E en servidor y verificar `/health.commit` contra `main`. No declarar 100% ni DEPLOY PASS hasta esos recibos.


### X-Ray final de rutas y búsqueda Harness

**Raíz confirmada:** el ejecutable `router-mvp/mvp` es un symlink a `chat-router/chat/backend/mvp`. Por tanto `Path(__file__).resolve().parents[2]` es `chat-router/`, no la raíz del repositorio. `loop_puente._RAIZ` y ambos contextos de `mvp/app.py` usan ahora `parents[2]`. Los symlinks existentes `chat-router/plugins/{nct_loop,cola50,watchdog48}` apuntan a los motores ya creados; el archivo de Constitución permanece en `chat-router/plugins/puente_chat/constitucion/`. Agregada regresión `test_existing_pluginhost_symlinks_resolve_inside_chat_router`.

**Investigación MECÁNICO:** `trigger_host.research` usa exclusivamente `mvp.harness_client._enviar("invoke",{"tool":"mechanico_buscar", ...})` con token del banco y el mismo endpoint autenticado `/plugins/deepseek_harness/invoke`. El Harness registra una herramienta de lectura con diez dominios de `investigation_sources.json`, DNS público, HTTPS, sin redirección y respuesta limitada. La salida se normaliza a `source_id,title,url,excerpt,retrieved_ref` para `gap_propose`, con evidencia SHA; páginas bloqueadas o vacías no autorizan propuestas ni PASS. No se ejecuta código descargado.

**GAPs al cierre:** el dispatcher registra `dsl_control:gap_collect` antes de ofrecer `handoff`, con readback y bloqueo si la persistencia falla. `gap_prepare_trigger` acepta un contrato `yaiwes.trigger.v1` suministrado por el operador, lo valida contra bytes reales de ancla, constitución, revisión de destino y `validate_loop`; entrega `VALIDATED_DRAFT_NOT_EXECUTABLE` y exige aprobación antes de `trigger_upsert` y posterior ejecución. No convierte sugerencias directamente en instrucciones ejecutables.

**No certificado en producción:** X-Ray de código y commits está verificado mediante GitHub, pero el `boot.sh` del Space solo clona `main` al iniciar. Se requiere comprobar que `/health.commit` corresponda al HEAD y ejecutar el endpoint real con autenticación; no hay evidencia suficiente para declarar `E2E_PASS`. No tocar Vercel ni crear infraestructura.
