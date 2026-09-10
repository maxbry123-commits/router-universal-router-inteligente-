# RECOVERY PATCH — ROUTER INTELIGENTE UNIVERSAL

Contrato: `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP`.

## Estado válido RIU-0039
- Plan limitado a 3 pasos; Paso 1 ACTIVE.
- Catálogo público 20: Job `6aa2513d5527934177ebfaad`.
- HF-M01 config/tokenizer/generation: Job `6aa26cc321047bf1b0371f28` COMPLETED.
- HF-M01 inferencia local real: Job `6aa288a521047bf1b0372324` COMPLETED.
- HF adapter + gateway único preservados.
- Nuevo hot-path `integration/huggingface/router_hot_path.py` reutiliza `red/enchufe_gate.py` y `red/red_universal.py`; no crea segundo router.
- Gateway actualizado para delegar a Enchufe Gate → RedUniversal → HF adapter.
- HF Job `6aa297195527934177ec0aed` COMPLETED con read-back desde `main`: `2 passed in 1.25s`, `RIU_HOT_PATH_TEST_RC 0`.
- Auditoría RIU-0039: commit `f08191ec91f0d74850799b38b44298bc77f0cfe9`.
- HF-M01 sigue NO READY: falta dataset/storage y provider hosted autenticado por el hot-path real.

## Boot
1. Leer STATE/CHECKPOINT/PLAN/BITACORA/README/Handoff/PARCHE.
2. Continuar `P01_HF_M01_DATASET_STORAGE_PROVIDER_VALIDATION`.
3. Resolver dataset/storage y provider autenticado sin exponer secretos.
4. Solo tras PASS promover HF-M01 y avanzar HF-M02 1×1.
5. P02 y P03 permanecen pendientes.

Cierre solo con ruta + SHA/diff + read-back + test/log + URL. Estado `ACTIVE_LOOP`.