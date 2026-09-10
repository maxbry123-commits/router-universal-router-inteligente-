# Handoff Router Inteligente Universal

## Estado ejecutivo
`tel.workflow/v3` / `FAIL_CLOSED_LOOP` / `ACTIVE_LOOP`.

## Arquitectura
Router determinista: entrada -> DAG fija -> Enchufe -> Router/RedUniversal -> adapter/conector -> verifier.

## RIU-0038
- HF Jobs compute real operativo.
- Catálogo público 20: Job `6aa2513d5527934177ebfaad`.
- HF-M01 `Qwen/Qwen3-0.6B`: config/tokenizer/generation Job `6aa26cc321047bf1b0371f28` COMPLETED.
- HF-M01 inferencia material real: Job `6aa288a521047bf1b0372324` COMPLETED en `cpu-upgrade`; `RIU_HF_M01_OK`; 596049920 parámetros runtime; CPU; 7.108s.
- Auditoría RIU-0038: `router inteligente universal/integration/huggingface/RIU-0038-HF-M01-REAL-COMPUTE.md`; commit `d798b6b878d3876ce866584647fd41b9cf8c6c23`.
- Adapter HF: `router inteligente universal/integration/huggingface/huggingface_openai_chat.py`; commit `70b2a7d4b5ee419999e3b6f436e219370141d294`; blob `3d89e6e705fb30a55ca5ae72db05538bdabbabb7`.
- Gateway FastAPI único: `router inteligente universal/integration/huggingface/fastapi_gateway.py`; commit `ea0392a58ce6391514471926a315a6ebd9928521`; blob `a7a2c16019adee69de597ec0abd251912a8a11ca`.
- Registry V4: commit `3de1df105276080ae8c94067816d2e190c8b18df`.

## GAP vigente
HF-M01 sigue NO READY: compute local HF Jobs ya está verificado; faltan FastAPI→Enchufe→Router hot path y dataset/storage. Hosted provider auth permanece frontera separada de credencial. Catálogo privado continúa como GAP separado.

## Plan único
1. P01 ACTIVE — cerrar HF-M01 y luego HF-M02..HF-M20 1×1.
2. P02 PENDING — C01-C23 con REUSE>PATCH>ADAPT>GENERATE.
3. P03 PENDING — API Key Manager + E2E real.

No declarar PASS por presencia; exigir SHA/read-back/test/log/URL.
