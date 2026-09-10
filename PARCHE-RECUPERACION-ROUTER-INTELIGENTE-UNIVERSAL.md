# PARCHE DE RECUPERACIÓN — ROUTER INTELIGENTE UNIVERSAL

Estado actual: `ACTIVE_LOOP` · contrato `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP`.

## Hecho y verificado
- HF Jobs como cómputo real; catálogo público 20 certificado.
- HF-M01 compute/hot-path/dataset RO PASS; provider auth continúa 403 por permisos insuficientes; `FLAG-HF-PROVIDER-AUTH-001`; NO READY.
- HF-M02 compute real PASS: Job `6aa2a4f25527934177ec0e01`.
- HF-M02 integración real PASS: Job `6aa2cf4f21047bf1b0372e67` COMPLETED; dataset mount True/16 files; HTTP 200; `FASTAPI_ENCHUFE_ROUTER_M02_OK=True`; GPT2LMHeadModel; 124439808 params; repo ZIP SHA256 `033a19f379e56f3a23bcad488af9089bc6f9a2e1fae25df6dd17a06bee8412df`.
- HF-M02 storage RW sigue NO PASS: Job `6aa2ebc15527934177ec1eb6` ERROR 403 al crear bucket con secreto protegido; credencial actual sin permiso bucket create/write; secreto no expuesto.

## GAP/FLAG
- `GAP-HF-CATALOG-001`: catálogo privado.
- `FLAG-HF-PROVIDER-AUTH-001`: permiso Inference Providers insuficiente.
- `GAP-HF-M02-RW-STORAGE-001`: Storage Bucket/output RW persistente no certificado.
- `FLAG-HF-M02-RW-STORAGE-AUTH-001`: boundary de permiso bucket create/write confirmado.
- GAP P02 contractuales continúan fail-closed.

## Lista única
- [ ] P01.1 mantener provider auth HF-M01 como FLAG; NO READY.
- [ ] P01.2 mantener storage RW HF-M02 como FLAG/GAP; NO READY.
- [ ] P01.3 cola 1×1 HF-M03 real compute; después HF-M04..HF-M20.
- [ ] P02 C01-C23.
- [ ] P03 API Key Manager + E2E.

Cierre sólo con ruta+SHA/diff+read-back+test/log+URL.