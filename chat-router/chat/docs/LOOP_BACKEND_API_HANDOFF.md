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
