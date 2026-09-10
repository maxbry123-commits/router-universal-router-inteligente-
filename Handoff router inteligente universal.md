# Handoff Router Inteligente Universal

## Estado ejecutivo
`tel.workflow/v3` / `FAIL_CLOSED_LOOP` / `ACTIVE_LOOP`.

## Arquitectura
Entrada -> DAG fija -> Enchufe Gate -> RedUniversal -> adapter/conector -> verifier.

## RIU-0043
- HF-M01 compute/hot-path/dataset RO PASS; provider auth 403 sigue FLAG; NO READY.
- HF-M02 compute real PASS: Job `6aa2a4f25527934177ec0e01`.
- HF-M02 integración real PASS: Job `6aa2cf4f21047bf1b0372e67` COMPLETED; repo SHA256 `033a19f379e56f3a23bcad488af9089bc6f9a2e1fae25df6dd17a06bee8412df`; dataset mount True/16 files; HTTP 200; `FASTAPI_ENCHUFE_ROUTER_M02_OK=True`; GPT2LMHeadModel; 124439808 params.
- HF-M02 storage RW/output persistente NO PASS. Job `6aa2ebc15527934177ec1eb6` ERROR 403: credencial autorizada con lectura pero sin permiso bucket create/write; secreto no expuesto. `FLAG-HF-M02-RW-STORAGE-AUTH-001`.

## Plan único
1. P01 ACTIVE — cola 1×1 HF-M03 real compute; mantener FLAGs HF-M01/HF-M02.
2. P02 PENDING — C01-C23.
3. P03 PENDING — API Key Manager + E2E.

Exigir ruta+SHA/read-back+test/log+URL.