# Handoff Router Inteligente Universal

## Estado ejecutivo
`tel.workflow/v3` / `FAIL_CLOSED_LOOP` / `ACTIVE_LOOP`.

## Arquitectura
Entrada -> DAG fija -> Enchufe Gate -> RedUniversal -> adapter/conector -> verifier.

## RIU-0046
- HF-M01 compute/hot-path/dataset RO PASS; provider auth 403 sigue FLAG; NO READY.
- HF-M02 compute + integración real PASS; storage RW create/write 403 sigue FLAG; NO READY.
- HF-M03 compute + integración FastAPI→Enchufe→Router→adapter + dataset RO PASS; storage RW persistente PENDING; NO READY.
- HF-M04 `unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF`: intento `6aa316585527934177ec29ee` cancelado por anomalía timeout-state; retry `6aa34d825527934177ec3d2c` lanzado con `timeout_seconds=7200`, llama.cpp CUDA/a10g-small; estado inicial SCHEDULING; NO PASS.

## Plan único
1. P01 ACTIVE — cola 1×1 HF-M04 compute real; mantener FLAGs/GAP existentes.
2. P02 PENDING — C01-C23.
3. P03 PENDING — API Key Manager + E2E.

Exigir ruta+SHA/read-back+test/log+URL; SCHEDULING/RUNNING no equivale PASS.