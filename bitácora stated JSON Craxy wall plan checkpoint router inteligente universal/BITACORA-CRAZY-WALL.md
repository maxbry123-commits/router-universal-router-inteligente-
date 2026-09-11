# BITÁCORA CRAZY WALL — ROUTER INTELIGENTE UNIVERSAL

**Contrato:** `tel.workflow/v3` · **Modo:** `FAIL_CLOSED_LOOP`.

## RIU-0001..0058 — CORE
Core ejecutable cerrado y preservado: P01=`CLOSED_EXECUTABLE_SET`; P02=`CLOSED_HOT_PATH_EXECUTABLE_SET`; P03=`VERIFIED_CLOSED`. GitHub Actions run `34582284615`, job `103208408709`: success, `2 passed in 6.79s`. Commit hot-path `af469152fd0306d706c67b8cf6548512fdc4f1c0`.

## RIU-0059 — NUEVO INPUT LITERAL DEL DIRECTOR
Antes de cualquier tarea siguiente:
1. testear todos y cada uno de los modelos HF registrados;
2. revisar/actualizar Arquitectura, Handoff y Crazy Wall/STATE como X-Ray/ADN completo;
3. mantener auditables hechos, pendientes, cableado, Jobs, API keys, GAP/FLAGS y tests;
4. sólo después hacer regresión global y pasar a tarea siguiente.

Decisión: el core no se reabre ni se degrada; se abre `ACTIVE_LOOP_MODEL_CERTIFICATION` como gate adicional explícitamente solicitado.

## Estado certificación 20 modelos al abrir RIU-0059
- PASS/ejecución previa válida: M01, M02, M03, M05, M06, M07, M10, M11, M12, M20.
- FLAG/GAP previo con causa preservada: M04, M08, M09, M13, M14, M15, M16, M17, M18, M19.
- M18: no fue alcanzado por el job secuencial anterior y debe tener ejecución individual.
- M09: compute completado pero `content=null`; sigue FLAG response-contract.
- M04/M17: timeouts previos; no PASS.

## Evidencia Jobs relevante
`6aa2513d5527934177ebfaad` catálogo 20; `6aa2f8e921047bf1b03732b7` M03 GPU/hot-path; `6aa3781121047bf1b0374a5c` M05 compute; `6aa3977e21047bf1b0374e94` M05 integración; `6aa3a3cd5527934177ec4e7e` M20 PASS; `6aa3a3dd5527934177ec4e80` M09 FLAG; `6aa3a24f5527934177ec4e3c` M17/M18 timeout/cancel.

## RIU-0060 — intento batch reciente
Job `6aa3943f21047bf1b0374dc8` fue lanzado para M06/M10/M07 y reveló `ModuleNotFoundError: transformers`. Resultado: `GAP_ENVIRONMENT_DEPENDENCY`; no se usa como PASS y no invalida las evidencias anteriores ya verificadas de esos slots.

## Cola actual
`sync_docs -> individual_model_certification -> 20/20 accounted -> final regression/E2E -> update ADN -> next task`.

## Reglas
`CATALOG_OBSERVED != TESTED != READY`; presencia no es integración; COMPLETED no es inferencia; timeout no es PASS; FLAG externo no se maquilla como cierre.

Estado: `ACTIVE_LOOP_MODEL_CERTIFICATION`.