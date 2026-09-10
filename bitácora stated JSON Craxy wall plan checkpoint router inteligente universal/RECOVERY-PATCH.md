# RECOVERY PATCH — ROUTER INTELIGENTE UNIVERSAL

Contrato: `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP`.

## Estado válido RIU-0043
- P01 ACTIVE; P02/P03 PENDING.
- HF-M01 compute/hot-path/dataset RO PASS; provider auth 403 sigue `FLAG-HF-PROVIDER-AUTH-001`; NO READY.
- HF-M02 compute real PASS en `6aa2a4f25527934177ec0e01`.
- HF-M02 integración real PASS en Job `6aa2cf4f21047bf1b0372e67`: repo ZIP SHA256 `033a19f379e56f3a23bcad488af9089bc6f9a2e1fae25df6dd17a06bee8412df`; dataset mount=True, 16 files; HTTP 200; `FASTAPI_ENCHUFE_ROUTER_M02_OK=True`; GPT2LMHeadModel; 124439808 params.
- Persistencia RW Storage Bucket/output HF-M02 sigue NO certificada. StrategyDelta Job `6aa2ebc15527934177ec1eb6` terminó ERROR 403: la credencial autorizada tiene lectura pero carece de permiso bucket create/write; secreto no expuesto. `FLAG-HF-M02-RW-STORAGE-AUTH-001`; HF-M02 NO READY.

## Boot
1. Releer fuentes de verdad.
2. Cola 1×1: validar HF-M03 compute real en HF Jobs; mantener FLAGs HF-M01/HF-M02.
3. Continuar sólo P01 independiente seguro mientras boundaries externos permanezcan abiertos.
4. Tras P01, P02 y luego P03; no agregar fases.

Cierre solo con ruta+SHA/diff+read-back+test/log+URL. Estado `ACTIVE_LOOP`.