# PARCHE DE RECUPERACIÓN — ROUTER INTELIGENTE UNIVERSAL

Estado actual: `ACTIVE_LOOP` · contrato `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP` · FAST-CLOSE · 99%.

## Hecho y verificado
- HF Jobs como cómputo real; catálogo público 20 certificado.
- HF-M01/M02/M03 conservan PASS internos; auth/provider/RW-storage externos quedan FLAGS/GAP explícitos.
- HF-M04: `FLAG-HF-M04-COMPUTE-001` tras dos anomalías timeout-state; no otra ventana larga.
- HF-M05 integración real PASS.
- HF-M06/M07/M10/M11/M12: Job `6aa398fe5527934177ec4cd0` COMPLETED; verifier individual PASS para cada slot detrás de FastAPI→Enchufe→Router→HFAdapter; dataset RO `/data` True/10 files; summary `/tmp/riu_hf_batch_m06_m12_summary.json`; SHA256 `c3b38014bdd5423cd85b42f14d54fc13c95247a0aa29e3729eb3ac84264dd6a5`; read-back True; `RIU_HF_BATCH_M06_M12_OK=True`.

## GAP/FLAG
- `GAP-HF-CATALOG-001`: catálogo privado.
- `FLAG-HF-PROVIDER-AUTH-001`: permiso Inference Providers insuficiente.
- storage RW HF-M02/HF-M03/HF-M05: boundary externo no certificado; no inventar bucket/secret.
- `GAP-HF-M04-TIMEOUT-001` + `FLAG-HF-M04-COMPUTE-001`.
- GAP P02 contractuales sólo bloquean si afectan E2E real.

## Lista única
- [x] HF-M05 integración real.
- [x] HF-M06/M07/M10/M11/M12 batch compatible con persistencia individual lógica y summary SHA/read-back.
- [ ] M08/M09/M13-M20 por flavor/tamaño/scope; ejecutar compatibles, FLAG exacto los no ejecutables.
- [ ] P02 sólo GAPs C01-C23 bloqueantes del hot-path.
- [ ] P03 API Key Manager hasta 100 slots + E2E real.

Cierre: 100% PASS de lo ejecutable + lista explícita de FLAGS externos; no quedarse en 98% por proveedor externo probado.