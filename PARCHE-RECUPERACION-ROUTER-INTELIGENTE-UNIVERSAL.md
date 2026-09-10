# PARCHE DE RECUPERACIÓN — ROUTER INTELIGENTE UNIVERSAL

Estado actual: `ACTIVE_LOOP` · contrato `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP`.

## Hecho y verificado
- HF Jobs como cómputo real; catálogo público 20 certificado.
- HF-M01 compute/hot-path/dataset RO PASS; provider auth 403; `FLAG-HF-PROVIDER-AUTH-001`; NO READY.
- HF-M02 compute + integración real PASS; Storage Bucket RW create/write 403; `FLAG-HF-M02-RW-STORAGE-AUTH-001`; NO READY.
- HF-M03 `Qwen/Qwen3-8B` compute real PASS: Job `6aa2ecbb21047bf1b037318e` COMPLETED; `Qwen3ForCausalLM`; 8190735360 params; respuesta `RIU_HF_M03_OK`; `MAX_MEMORY_ALLOCATED=16396255232`; adapter/dataset/storage/FastAPI siguen PENDING; NO READY.
- Registry HF reconciliado a V8.

## GAP/FLAG
- `GAP-HF-CATALOG-001`: catálogo privado.
- `FLAG-HF-PROVIDER-AUTH-001`: permiso Inference Providers insuficiente.
- `GAP-HF-M02-RW-STORAGE-001` + `FLAG-HF-M02-RW-STORAGE-AUTH-001`: persistencia RW no certificada por boundary de permiso bucket write/create.
- GAP P02 contractuales continúan fail-closed.

## Lista única
- [ ] P01.1 mantener provider auth HF-M01 como FLAG; NO READY.
- [ ] P01.2 mantener storage RW HF-M02 como FLAG/GAP; NO READY.
- [ ] P01.3 cola 1×1 HF-M03 adapter + dataset/storage + FastAPI/Enchufe real; después HF-M04..HF-M20.
- [ ] P02 C01-C23.
- [ ] P03 API Key Manager + E2E.

Cierre sólo con ruta+SHA/diff+read-back+test/log+URL.