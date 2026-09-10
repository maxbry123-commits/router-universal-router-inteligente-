# RECOVERY PATCH — ROUTER INTELIGENTE UNIVERSAL

Contrato: `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP`.

## Estado válido RIU-0042
- P01 ACTIVE; P02/P03 PENDING.
- HF-M01 compute/hot-path/dataset RO PASS; provider auth 403 sigue `FLAG-HF-PROVIDER-AUTH-001`; NO READY.
- HF-M02 compute real PASS en `6aa2a4f25527934177ec0e01`.
- HF-M02 integración real PASS en Job `6aa2cf4f21047bf1b0372e67`: repo ZIP SHA256 `033a19f379e56f3a23bcad488af9089bc6f9a2e1fae25df6dd17a06bee8412df`; dataset mount=True, 16 files; HTTP 200; `FASTAPI_ENCHUFE_ROUTER_M02_OK=True`; GPT2LMHeadModel; 124439808 params.
- Persistencia RW Storage Bucket/output HF-M02 NO certificada; `GAP-HF-M02-RW-STORAGE-001` abierto; HF-M02 NO READY.

## Boot
1. Releer fuentes de verdad.
2. Cola 1×1: certificar storage RW persistente HF-M02; mantener FLAG HF-M01.
3. Si storage queda bloqueado por boundary externo, continuar sólo P01 independiente seguro HF-M03..20 sin falsificar READY.
4. Tras P01, P02 y luego P03; no agregar fases.

Cierre solo con ruta+SHA/diff+read-back+test/log+URL. Estado `ACTIVE_LOOP`.