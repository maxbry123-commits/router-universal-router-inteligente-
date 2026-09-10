# RECOVERY PATCH — ROUTER INTELIGENTE UNIVERSAL

Contrato: `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP`.

## Estado válido RIU-0038
- Plan limitado a 3 pasos.
- Paso 1 ACTIVE.
- Catálogo público 20: Job `6aa2513d5527934177ebfaad`.
- HF-M01 config/tokenizer/generation: Job `6aa26cc321047bf1b0371f28` COMPLETED.
- HF-M01 inferencia local real: Job `6aa288a521047bf1b0372324` COMPLETED en `cpu-upgrade`; `REPLY=RIU_HF_M01_OK`; `HF_M01_REAL_COMPUTE_OK=True`; 596049920 parámetros runtime; CPU; 7.108s.
- Adapter HF: commit `70b2a7d4b5ee419999e3b6f436e219370141d294`, blob `3d89e6e705fb30a55ca5ae72db05538bdabbabb7`.
- Gateway FastAPI único: commit `ea0392a58ce6391514471926a315a6ebd9928521`, blob `a7a2c16019adee69de597ec0abd251912a8a11ca`.
- Registry V4 sincronizado: commit `3de1df105276080ae8c94067816d2e190c8b18df`.
- HF-M01 sigue NO READY: compute real ya PASS; faltan FastAPI→Enchufe→Router hot path y dataset/storage. Hosted provider auth permanece separado.

## Boot
1. Leer STATE/CHECKPOINT/PLAN/BITACORA/README/Handoff/PARCHE.
2. Continuar `P01_HF_M01_SERVING_VALIDATION`.
3. Verificar FastAPI→Enchufe→Router→HF-M01 + dataset/storage.
4. Solo tras PASS promover HF-M01 y avanzar HF-M02 1×1.
5. P02 y P03 permanecen pendientes.

Cierre solo con ruta + SHA/diff + read-back + test/log + URL. Estado `ACTIVE_LOOP`.
