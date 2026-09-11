# PARCHE DE RECUPERACIÓN — ROUTER INTELIGENTE UNIVERSAL

Estado actual: `ACTIVE_LOOP` · contrato `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP`.

## Hecho y verificado
- HF Jobs como cómputo real; catálogo público 20 certificado.
- HF-M01 compute/hot-path/dataset RO PASS; provider auth 403; NO READY.
- HF-M02 compute + integración real PASS; Storage Bucket RW create/write 403; NO READY.
- HF-M03 compute + integración FastAPI→Enchufe→Router→adapter + dataset RO PASS; storage RW persistente PENDING; NO READY.
- HF-M04: Jobs `6aa316585527934177ec29ee` y `6aa34d825527934177ec3d2c` cancelados tras anomalía timeout-state repetida sin output final; `FLAG-HF-M04-COMPUTE-001`; NO PASS.
- HF-M05 `Qwen/Qwen2.5-7B-Instruct`: metadata Hub verificada; Job `6aa3781121047bf1b0374a5c` lanzado en a10g-small/Transformers, timeout 30m; SCHEDULING inicial; NO PASS.

## GAP/FLAG
- `GAP-HF-CATALOG-001`: catálogo privado.
- `FLAG-HF-PROVIDER-AUTH-001`: permiso Inference Providers insuficiente.
- `GAP-HF-M02-RW-STORAGE-001` + `FLAG-HF-M02-RW-STORAGE-AUTH-001`: persistencia RW no certificada.
- `GAP-HF-M03-RW-STORAGE-001`: storage RW persistente no certificado.
- `GAP-HF-M04-TIMEOUT-001` + `FLAG-HF-M04-COMPUTE-001`: dos ejecuciones sin inferencia final y anomalía de timeout-state.
- GAP P02 contractuales continúan fail-closed.

## Lista única
- [ ] P01.1 mantener provider auth HF-M01 como FLAG; NO READY.
- [ ] P01.2 mantener storage RW HF-M02 como FLAG/GAP; NO READY.
- [ ] P01.3 mantener storage RW HF-M03 como GAP; NO READY.
- [ ] P01.4 mantener HF-M04 FLAG; NO PASS hasta nueva evidencia materialmente distinta.
- [ ] P01.5 cola 1×1 HF-M05 Job `6aa3781121047bf1b0374a5c`; después HF-M06..HF-M20.
- [ ] P02 C01-C23.
- [ ] P03 API Key Manager + E2E.

Cierre sólo con ruta+SHA/diff+read-back+test/log+URL.