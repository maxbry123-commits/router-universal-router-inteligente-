# Handoff Router Inteligente Universal

## Estado ejecutivo
`tel.workflow/v3` / `FAIL_CLOSED_LOOP` / `ACTIVE_LOOP`.

## Arquitectura
Entrada -> DAG fija -> Enchufe Gate -> RedUniversal -> adapter/conector -> verifier.

## RIU-0045
- HF-M01 compute/hot-path/dataset RO PASS; provider auth 403 sigue FLAG; NO READY.
- HF-M02 compute + integración real PASS; storage RW create/write 403 sigue FLAG; NO READY.
- HF-M03 `Qwen/Qwen3-8B` compute + integración FastAPI→Enchufe→Router→adapter + dataset RO PASS: Job `6aa2f8e921047bf1b03732b7` COMPLETED; HTTP 200; `RIU_HF_M03_ROUTE_OK`; `Qwen3ForCausalLM`; 8190735360 params; CUDA True; max GPU memory 16396255232. Storage RW persistente PENDING; NO READY.

## Plan único
1. P01 ACTIVE — cola 1×1 HF-M04 compute real; mantener FLAGs HF-M01/HF-M02 y GAP storage HF-M03.
2. P02 PENDING — C01-C23.
3. P03 PENDING — API Key Manager + E2E.

Exigir ruta+SHA/read-back+test/log+URL.