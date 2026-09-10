# PARCHE DE RECUPERACIÓN — ROUTER INTELIGENTE UNIVERSAL

Estado actual: `ACTIVE_LOOP` · contrato `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP`.

## Hecho y verificado
- HF Jobs como cómputo real y catálogo público 20 certificado.
- HF-M01 compute local real PASS.
- FastAPI -> Enchufe Gate -> RedUniversal -> adapter determinista PASS en Job `6aa297195527934177ec0aed` (`2 passed`).
- Dataset/storage RO binding HF-M01 PASS: `HuggingFaceH4/ultrachat_200k` montado en Job `6aa2983921047bf1b03725eb`; manifest SHA256 `241f6f1a9ac692d9bb2c1556e2be369c15d6a53401256749d34f3e1a6fc0b640`.
- Provider auth HF-M01 mediante secret runtime redactado: Job `6aa2985921047bf1b03725ed` devolvió 403 por permiso insuficiente; `FLAG-HF-PROVIDER-AUTH-001` sigue abierto.
- HF-M02 `openai-community/gpt2` compute local real PASS: Job `6aa2a4f25527934177ec0e01` COMPLETED, GPT2LMHeadModel, CPU, 124439808 parámetros runtime, generación real; adapter/dataset-storage/FastAPI siguen pendientes y HF-M02 NO READY.

## GAP/FLAG
- `GAP-HF-CATALOG-001`: catálogo privado.
- `FLAG-HF-PROVIDER-AUTH-001`: token/método actual sin permiso Inference Providers.
- Storage Bucket RW persistente no certificado.
- GAP P02 contractuales continúan fail-closed.

## Lista única
- [ ] P01.1 mantener provider auth HF-M01 como FLAG hasta credencial autorizada suficiente; NO READY.
- [ ] P01.2 cola 1×1 HF-M02 dataset/storage + adapter/FastAPI; después HF-M03..HF-M20.
- [ ] P01.3 consolidar gateway/registry al completar criterios.
- [ ] P02 C01-C23.
- [ ] P03 API Key Manager + E2E.

Cierre solo con ruta+SHA/diff+read-back+test/log+URL.