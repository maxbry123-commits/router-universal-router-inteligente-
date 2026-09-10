# Handoff Router Inteligente Universal

## Estado ejecutivo
`tel.workflow/v3` / `FAIL_CLOSED_LOOP` / `ACTIVE_LOOP`.

## Arquitectura
Router determinista: entrada -> DAG fija -> Enchufe -> Router/RedUniversal -> adapter/conector -> verifier.

## RIU-0039
- HF Jobs compute real operativo.
- Catálogo público 20: Job `6aa2513d5527934177ebfaad`.
- HF-M01 config/tokenizer/generation: Job `6aa26cc321047bf1b0371f28` COMPLETED.
- HF-M01 inferencia material real: Job `6aa288a521047bf1b0372324` COMPLETED.
- `integration/huggingface/router_hot_path.py` creado: commit `86f5f545f070dc3180652e73265f6fc77ba1e514`.
- Gateway FastAPI actualizado para delegar a Enchufe Gate -> RedUniversal -> HF adapter: commit `6da8ecd573986bc4e77a2c749e37d9f34955bd57`.
- Test determinista creado: commit `8509fa25793fec73a1e9ce023787713df5ed4225`.
- HF Job `6aa297195527934177ec0aed` COMPLETED leyendo `main`: `2 passed in 1.25s`, `RIU_HOT_PATH_TEST_RC 0`.
- Auditoría RIU-0039: commit `f08191ec91f0d74850799b38b44298bc77f0cfe9`.

## GAP vigente
HF-M01 sigue NO READY: el hot-path determinista ya atraviesa Enchufe Gate + RedUniversal, pero faltan dataset/storage y ejecución hosted provider autenticada por esa ruta. Catálogo privado continúa como GAP separado.

## Plan único
1. P01 ACTIVE — cerrar dataset/storage + provider auth de HF-M01 y luego HF-M02..HF-M20 1×1.
2. P02 PENDING — C01-C23 con REUSE>PATCH>ADAPT>GENERATE.
3. P03 PENDING — API Key Manager + E2E real.

No declarar PASS por presencia; exigir SHA/read-back/test/log/URL.