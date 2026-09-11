# RECOVERY PATCH — ROUTER INTELIGENTE UNIVERSAL
Contrato: `tel.workflow/v3` · `FAIL_CLOSED_LOOP`.

## Estado recuperable final
Core RIU-0058=`VERIFIED_CLOSED`; P01/P02/P03 cerrados.
Certificación HF ampliada=`MODEL_CERTIFICATION_20_OF_20_ACCOUNTED`.
Regresión global final=`FINAL_REGRESSION_E2E_PASS`.

## Evidencia M18
Attempt `6aa475605527934177eca1cb` ERROR; diagnostic `6aa475e721047bf1b0378e13` => `no GGUF files found` con selector Q3_K_S / `--model is required`; StrategyDelta oficial Q4_K_M `6aa4769b5527934177eca24b` llegó a RUNNING pero no cerró en ventana corta 240s y fue cancelado. Final=`FLAG-HF-M18-RUNTIME-TIMEOUT-001`; nunca PASS.

## Evidencia regresión
GitHub Actions workflow `RIU FAST-CLOSE`, run `34582284615`, rerun job `103434377312`, conclusion `success`; test `router inteligente universal/tests/test_fast_close_global_e2e.py`: `2 passed, 2 warnings in 6.75s` sobre commit de código `af469152fd0306d706c67b8cf6548512fdc4f1c0`.

## Recuperación futura
No repetir P01-P03 ni certificación 20/20 salvo evidencia nueva contradictoria. Mantener FLAGS/GAP externos/runtime como tales; no promover catálogo a READY.

## Gate final
`CORE_VERIFIED_CLOSED + MODEL_CERTIFICATION_20_OF_20_ACCOUNTED + FINAL_REGRESSION_E2E_PASS` = SATISFECHO.
Estado=`VERIFIED_CLOSED`.