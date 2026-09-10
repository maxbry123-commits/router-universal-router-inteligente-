# PARCHE DE RECUPERACIÓN — ROUTER INTELIGENTE UNIVERSAL

Estado actual: `ACTIVE_LOOP` · contrato `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP`.

## Hecho y verificado
- HF Jobs como cómputo real y catálogo público 20 certificado.
- HF-M01 compute local real PASS.
- FastAPI -> Enchufe Gate -> RedUniversal -> adapter determinista PASS en Job `6aa297195527934177ec0aed` (`2 passed`).
- Dataset/storage RO binding PASS: `HuggingFaceH4/ultrachat_200k` montado en Job `6aa2983921047bf1b03725eb`; manifest SHA256 `241f6f1a9ac692d9bb2c1556e2be369c15d6a53401256749d34f3e1a6fc0b640`.
- Provider auth intentado mediante secret runtime redactado: Job `6aa2985921047bf1b03725ed` devolvió 403 por permiso insuficiente.
- Auditoría RIU-0040: commit `dbcd504acc500e31d36abcddaf103434d87866e9`.

## GAP/FLAG
- `GAP-HF-CATALOG-001`: catálogo privado.
- `FLAG-HF-PROVIDER-AUTH-001`: token/método actual sin permiso Inference Providers.
- Storage Bucket RW persistente no certificado.
- GAP P02 contractuales continúan fail-closed.

## Lista única
- [ ] P01.1 resolver provider auth HF-M01 sin exponer secreto.
- [ ] P01.2 validar HF-M02..HF-M20 1×1.
- [ ] P01.3 consolidar gateway/registry.
- [ ] P02 C01-C23.
- [ ] P03 API Key Manager + E2E.

Cierre solo con ruta+SHA/diff+read-back+test/log+URL.