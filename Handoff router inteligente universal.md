# Handoff Router Inteligente Universal

## Estado ejecutivo
`tel.workflow/v3` / `FAIL_CLOSED_LOOP` / `ACTIVE_LOOP`.

## Arquitectura
Router determinista: entrada -> DAG fija -> Enchufe -> Router/RedUniversal -> adapter/conector -> verifier.

## RIU-0037
- HF Jobs compute real operativo.
- Catálogo público 20: Job `6aa2513d5527934177ebfaad`.
- HF-M01 `Qwen/Qwen3-0.6B`: Job `6aa26cc321047bf1b0371f28` COMPLETED; config/tokenizer/generation verificados.
- Adapter HF: `router inteligente universal/integration/huggingface/huggingface_openai_chat.py`; commit `70b2a7d4b5ee419999e3b6f436e219370141d294`; blob `3d89e6e705fb30a55ca5ae72db05538bdabbabb7`.
- Gateway FastAPI único: `router inteligente universal/integration/huggingface/fastapi_gateway.py`; commit `ea0392a58ce6391514471926a315a6ebd9928521`; blob `a7a2c16019adee69de597ec0abd251912a8a11ca`.
- Registry V4: commit `3de1df105276080ae8c94067816d2e190c8b18df`.

## GAP vigente
HF-M01 sigue NO READY: faltan inferencia runtime autenticada, Enchufe/Router hot path, dataset/storage y acelerador. Catálogo privado continúa como GAP separado de credencial.

## Plan único
1. P01 ACTIVE — cerrar HF-M01 y luego HF-M02..HF-M20 1×1.
2. P02 PENDING — C01-C23 con REUSE>PATCH>ADAPT>GENERATE.
3. P03 PENDING — API Key Manager + E2E real.

No declarar PASS por presencia; exigir SHA/read-back/test/log/URL.
