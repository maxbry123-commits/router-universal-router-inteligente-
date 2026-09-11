# Handoff Router Inteligente Universal

## Estado ejecutivo
`tel.workflow/v3` / `FAIL_CLOSED_LOOP` / `ACTIVE_LOOP` / FAST-CLOSE / 99%.

## Arquitectura
Entrada -> DAG fija -> Enchufe Gate -> RedUniversal -> adapter/conector -> verifier.

## RIU-0050
- HF-M01/M02/M03 conservan PASS internos; auth/provider/RW storage externos permanecen FLAGS/GAP.
- HF-M04 mantiene `FLAG-HF-M04-COMPUTE-001`; no otra ventana larga.
- HF-M05 integración real PASS.
- HF-M06/M07/M10/M11/M12: Job `6aa398fe5527934177ec4cd0` COMPLETED; cada modelo pasó el verifier individual detrás del hot-path FastAPI→Enchufe→Router→HFAdapter; dataset RO `/data` True/10 files; summary SHA256 `c3b38014bdd5423cd85b42f14d54fc13c95247a0aa29e3729eb3ac84264dd6a5`; summary read-back True; `RIU_HF_BATCH_M06_M12_OK=True`.

## Plan único
1. P01 ACTIVE — M08/M09/M13-M20 por compatibilidad/tamaño/scope; ejecutar compatibles y FLAG exacto los no ejecutables/external-only.
2. P02 PENDING — cerrar únicamente GAPs C01-C23 que bloqueen el hot-path real.
3. P03 PENDING — API Key Manager hasta 100 slots + E2E real.

Cierre global = 100% PASS de lo ejecutable + FLAGS externos explícitos; exigir ruta+SHA/read-back+test/log+URL.