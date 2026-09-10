# Handoff Router Inteligente Universal

## Estado ejecutivo
`tel.workflow/v3` / `FAIL_CLOSED_LOOP` / `ACTIVE_LOOP`.

## Arquitectura
Entrada -> DAG fija -> Enchufe Gate -> RedUniversal -> adapter/conector -> verifier.

## RIU-0044
- HF-M01 compute/hot-path/dataset RO PASS; provider auth 403 sigue FLAG; NO READY.
- HF-M02 compute + integración real PASS; storage RW create/write 403 sigue FLAG; NO READY.
- HF-M03 `Qwen/Qwen3-8B` compute real PASS: Job `6aa2ecbb21047bf1b037318e` COMPLETED; `Qwen3ForCausalLM`; 8190735360 params; `RIU_HF_M03_OK`; max GPU memory 16396255232. Adapter/dataset/storage/FastAPI PENDING; NO READY.
- Registry HF reconciliado a V8.

## Plan único
1. P01 ACTIVE — cola 1×1 HF-M03 adapter + dataset/storage + FastAPI/Enchufe; mantener FLAGs HF-M01/HF-M02.
2. P02 PENDING — C01-C23.
3. P03 PENDING — API Key Manager + E2E.

Exigir ruta+SHA/read-back+test/log+URL.