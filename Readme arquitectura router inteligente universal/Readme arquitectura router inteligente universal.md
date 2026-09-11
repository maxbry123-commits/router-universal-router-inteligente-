# Router Inteligente Universal — Arquitectura / ADN / X-Ray

Contrato: `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP` · rama `main`.

## Estado ejecutivo
- CORE P01-P03: `VERIFIED_CLOSED`.
- Certificación individual HF_M01..HF_M20: `MODEL_CERTIFICATION_20_OF_20_ACCOUNTED`.
- Regresión/E2E global final: `PASS`.
- Estado global: `VERIFIED_CLOSED`.
- Regla preservada: `CATALOG_OBSERVED != TESTED != READY`.

## Arquitectura
`AGENTE -> API key -> FastAPI -> Auth/APIKeyGuard -> Enchufe Gate -> RedUniversal -> registry -> adapter -> destino/modelo -> verifier -> response`.
Separación: contracts/adapters/plugins/registry/loader/guards/tests.

## Core
P01 conjunto ejecutable HF cerrado; P02 hot-path `C01 REST -> C20 Auth -> C15 Gate -> C17 RedUniversal -> C16 adapter -> verifier`; P03 API Key Manager 100 slots hash-only rotate/revoke + E2E real.

## Certificación 20 modelos
PASS/ejecución verificada: M01, M02, M03, M05, M06, M07, M10, M11, M12, M20.
FLAG/GAP explícitos: M04, M08, M09, M13, M14, M15, M16, M17, M18, M19.
M18 final=`FLAG-HF-M18-RUNTIME-TIMEOUT-001`: Jobs `6aa475605527934177eca1cb` ERROR, `6aa475e721047bf1b0378e13` diagnóstico selector Q3_K_S, `6aa4769b5527934177eca24b` Q4_K_M RUNNING→CANCELED por ventana corta sin terminal inference.

## Regresión final
GitHub Actions `RIU FAST-CLOSE`, run `34582284615`, job `103434377312`: success; `pytest -q router inteligente universal/tests/test_fast_close_global_e2e.py` => `2 passed, 2 warnings in 6.75s`.
Commit de código probado `af469152fd0306d706c67b8cf6548512fdc4f1c0`; gateway blob `e970b5de2281d236b916ea41492ee52df8454153`; E2E blob `23473c2a33cb9e5a451ad5a19ce5c4e5a58fc2c7`.

## Cierre
`CORE_VERIFIED_CLOSED + MODEL_CERTIFICATION_20_OF_20_ACCOUNTED + FINAL_REGRESSION_E2E_PASS` = SATISFECHO.