# Handoff Router Inteligente Universal

## Estado ejecutivo
`tel.workflow/v3` / `FAIL_CLOSED_LOOP` / `ACTIVE_LOOP`.

## Arquitectura
Entrada -> DAG fija -> Enchufe Gate -> RedUniversal -> adapter/conector -> verifier.

## RIU-0048
- HF-M01 compute/hot-path/dataset RO PASS; provider auth 403 sigue FLAG; NO READY.
- HF-M02 compute + integración real PASS; storage RW create/write 403 sigue FLAG; NO READY.
- HF-M03 compute + integración FastAPI→Enchufe→Router→adapter + dataset RO PASS; storage RW persistente PENDING; NO READY.
- HF-M04: dos Jobs cancelados tras anomalía timeout-state repetida sin inferencia final; `FLAG-HF-M04-COMPUTE-001`; NO PASS.
- HF-M05 `Qwen/Qwen2.5-7B-Instruct`: Job `6aa3781121047bf1b0374a5c` COMPLETED; `Qwen2ForCausalLM`; `7615616512` params; CUDA=True; `RIU_HF_M05_OK=True`; compute PASS únicamente, NO READY.

## Plan único
1. P01 ACTIVE — cola 1×1 HF-M05 adapter+dataset/storage+FastAPI→Enchufe→Router; mantener FLAGs/GAP existentes.
2. P02 PENDING — C01-C23.
3. P03 PENDING — API Key Manager + E2E.

Exigir ruta+SHA/read-back+test/log+URL; compute PASS no equivale READY.