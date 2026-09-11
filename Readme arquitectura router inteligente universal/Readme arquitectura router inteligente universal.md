# Router Inteligente Universal — Arquitectura / ADN / X-Ray

Contrato: `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP` · rama `main`.

## Estado ejecutivo
- **CORE ejecutable:** `VERIFIED_CLOSED` / 100% según RIU-0058.
- **Nueva exigencia del Director:** certificación individual de **HF_M01..HF_M20** + regresión/E2E global final antes de pasar a la siguiente tarea.
- **Estado global ampliado:** `ACTIVE_LOOP_MODEL_CERTIFICATION`.
- Regla: `CATALOG_OBSERVED != TESTED != READY`.

## Cómo funciona el Router
`AGENTE -> API key -> FastAPI -> Auth/APIKeyGuard -> Enchufe Gate -> RedUniversal -> registry -> adapter -> destino/modelo -> verifier -> response`.
El Router selecciona rutas y ejecuta contratos deterministas; las LLM no pueden modificar la estructura autorizada del DAG. El núcleo conserva separación entre contracts/adapters/plugins/registry/loader/guards/tests.

## Tres pasos del core ya cerrados
1. Hugging Face ejecutable: conjunto verificable cerrado con PASS + FLAGS externos explícitos.
2. GitHub/C01-C23 hot-path: `C01 REST -> C20 Auth -> C15 Gate -> C17 RedUniversal -> C16 adapter -> verifier` verificado.
3. API Key Manager + E2E: 100 slots, hash-only, rotate/revoke, slot 101 fail-closed y E2E real.

## Evidencia core
GitHub Actions `RIU FAST-CLOSE` run `34582284615`, job `103208408709`: `success`, `2 passed in 6.79s`.
Commit hot-path `af469152fd0306d706c67b8cf6548512fdc4f1c0`; gateway blob `e970b5de2281d236b916ea41492ee52df8454153`; E2E test blob `23473c2a33cb9e5a451ad5a19ce5c4e5a58fc2c7`.

## Certificación HF 20 modelos — estado actual
- PASS/ejecución previamente verificada: M01, M02, M03, M05, M06, M07, M10, M11, M12, M20.
- FLAG/GAP con evidencia previa: M04, M08, M09, M13, M14, M15, M16, M17, M18, M19.
- M18 no cuenta aún como test individual: quedó `NOT_REACHED_DUE_M17_TIMEOUT` y debe ejecutarse por separado.
- Todos los FLAGS deben conservar causa exacta; ningún bloqueo de hardware/provider/token puede convertirse en PASS.

## Pruebas/Jobs relevantes
- Catálogo 20 modelos: Job `6aa2513d5527934177ebfaad`.
- M03 GPU + hot-path: `6aa2f8e921047bf1b03732b7` HTTP 200 / CUDA.
- M05 GPU compute: `6aa3781121047bf1b0374a5c`; integración previa `6aa3977e21047bf1b0374e94`.
- M20: `6aa3a3cd5527934177ec4e7e` COMPLETED / response OK.
- M09: `6aa3a3dd5527934177ec4e80` COMPLETED pero `content=null` -> FLAG response-contract.
- M17/M18 lote: `6aa3a24f5527934177ec4e3c` cancelado por timeout; M18 debe repetirse individualmente.
- Intento batch M06/M10/M07 `6aa3943f21047bf1b0374dc8` reveló GAP de entorno `ModuleNotFoundError: transformers`; no es PASS y la evidencia previa verificada de esos modelos no se invalida.

## Pendiente obligatorio antes de nueva tarea
1. Test individual/contable de M01..M20: cada slot debe terminar `PASS` o `FLAG/GAP` con job/log/model_id/flavor/resultado.
2. Reejecutar por separado slots que no tuvieron test individual concluyente, priorizando M18 y cualquier FLAG sin ejecución directa suficiente.
3. Ejecutar regresión final del Router y E2E global después de la certificación.
4. Sincronizar Arquitectura, Handoff, Crazy Wall, STATE, CHECKPOINT, PLAN, RECOVERY, índice HF, API keys y parche maestro.

## Criterio de cierre ampliado
`CORE_VERIFIED_CLOSED + MODEL_CERTIFICATION_20_OF_20_ACCOUNTED + FINAL_REGRESSION_E2E_PASS`.
Hasta entonces el core sigue cerrado, pero la tarea ampliada permanece `ACTIVE_LOOP`.