# PARCHE DE RECUPERACIÓN — ROUTER INTELIGENTE UNIVERSAL

Estado actual: `ACTIVE_LOOP` · contrato `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP` · FAST-CLOSE.

## Hecho y verificado
- HF Jobs como cómputo real; catálogo público 20 certificado.
- HF-M01/M02/M03 conservan PASS internos ya evidenciados; auth/provider/RW-storage externos quedan como FLAGS/GAP explícitos.
- HF-M04: dos Jobs cancelados por anomalía timeout-state; `FLAG-HF-M04-COMPUTE-001`; no repetir ventana larga.
- HF-M05 `Qwen/Qwen2.5-7B-Instruct`: compute PASS + integración real PASS. Job `6aa3977e21047bf1b0374e94` COMPLETED; HTTP 200; dataset RO `/data` True/10 files; CUDA True; response `RIU_HF_M05_ROUTE_OK`; evidence path `/tmp/riu_hf_m05_integration_evidence.json`; SHA256 `d3352d066152f07379352c94eaae94dd415be1adcda68b43791f8736c9653e79`; read-back True; `FASTAPI_ENCHUFE_ROUTER_M05_OK=True`.

## GAP/FLAG
- `GAP-HF-CATALOG-001`: catálogo privado.
- `FLAG-HF-PROVIDER-AUTH-001`: permiso Inference Providers insuficiente.
- `GAP/FLAG` storage RW HF-M02/HF-M03 + `GAP-HF-M05-RW-STORAGE-001`: boundary externo no certificado; no inventar bucket/secret.
- `GAP-HF-M04-TIMEOUT-001` + `FLAG-HF-M04-COMPUTE-001`.
- GAP P02 contractuales permanecen documentados y sólo bloquean si afectan E2E.

## Lista única
- [x] HF-M05 integración FastAPI→Enchufe→Router→adapter + dataset RO + SHA/read-back.
- [ ] Lote M06/M07/M10/M11/M12 en una corrida compatible; persistir resultado individual.
- [ ] M08/M09/M13-M20 por flavor/tamaño/scope compatible; si no ejecutable, FLAG exacto y continuar.
- [ ] P02 sólo GAPs C01-C23 bloqueantes del hot-path.
- [ ] P03 API Key Manager hasta 100 slots + E2E real.

Cierre: 100% PASS de lo ejecutable + lista explícita de FLAGS externos; no quedarse en 98% por un proveedor externo probado.