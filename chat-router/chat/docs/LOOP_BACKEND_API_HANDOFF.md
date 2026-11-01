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
