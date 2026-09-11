# PARCHE DE RECUPERACIÓN — ROUTER INTELIGENTE UNIVERSAL

Contrato: `tel.workflow/v3` · `FAIL_CLOSED_LOOP`.

## Estado del core
RIU-0058 permanece `VERIFIED_CLOSED`: P01/P02/P03 cerrados; API Key Manager 100 slots + E2E base verificados.
Evidencia base: GitHub Actions run `34582284615`, job `103208408709`, `2 passed in 6.79s`; commit `af469152fd0306d706c67b8cf6548512fdc4f1c0`.

## Nuevo gate solicitado por el Director
Antes de iniciar la siguiente tarea Ask Council/Mini Workflow:
1. testear/certificar cada uno de los 20 modelos HF;
2. dejar cada slot como PASS o FLAG/GAP con evidencia;
3. ejecutar regresión/E2E global final;
4. sincronizar todo el ADN/X-Ray documental.

## Estado de slots al abrir el gate
- Evidencia previa válida: M01, M02, M03, M05, M06, M07, M10, M11, M12, M20.
- FLAGS/GAP: M04, M08, M09, M13, M14, M15, M16, M17, M18, M19.
- M18 requiere test individual: el job anterior no llegó a ejecutarlo.
- M09 tiene compute completado pero response `content=null`.
- M04/M17 mantienen timeout flags.

## Evidencia Jobs a preservar
Catálogo `6aa2513d5527934177ebfaad`; M03 `6aa2f8e921047bf1b03732b7`; M05 compute `6aa3781121047bf1b0374a5c`; M05 integration `6aa3977e21047bf1b0374e94`; M20 `6aa3a3cd5527934177ebfa5c`; M09 `6aa3a3dd5527934177ec4e80`; M17/M18 `6aa3a24f5527934177ec4e3c`.

## Último intento y GAP
Job `6aa3943f21047bf1b0374dc8` para M06/M10/M07 expuso `ModuleNotFoundError: transformers`. Clasificación: `GAP_ENVIRONMENT_DEPENDENCY`; no PASS y no invalida evidencia anterior.

## Recuperación 1×1
`read truth files -> unresolved model slot -> research -> execute -> verify/refute -> persist -> next slot -> 20/20 accounted -> final E2E -> final ADN sync -> next task`.

## Gate final
`CORE_VERIFIED_CLOSED + MODEL_CERTIFICATION_20_OF_20_ACCOUNTED + FINAL_REGRESSION_E2E_PASS`.
Estado operativo actual: `ACTIVE_LOOP_MODEL_CERTIFICATION`.