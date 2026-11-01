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
