# RECOVERY PATCH — ROUTER INTELIGENTE UNIVERSAL

Contrato: `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP`.

## Estado válido RIU-0037
- Plan limitado a 3 pasos.
- Paso 1 ACTIVE.
- Catálogo público 20: Job `6aa2513d5527934177ebfaad`.
- HF-M01 config/tokenizer/generation: Job `6aa26cc321047bf1b0371f28` COMPLETED.
- Adapter HF creado: commit `70b2a7d4b5ee419999e3b6f436e219370141d294`, blob `3d89e6e705fb30a55ca5ae72db05538bdabbabb7`.
- Gateway FastAPI único creado: commit `ea0392a58ce6391514471926a315a6ebd9928521`, blob `a7a2c16019adee69de597ec0abd251912a8a11ca`.
- Registry V4 sincronizado: commit `3de1df105276080ae8c94067816d2e190c8b18df`.
- HF-M01 sigue NO READY: faltan inferencia runtime autenticada, Enchufe/Router hot path, dataset/storage y acelerador.

## Boot
1. Leer STATE/CHECKPOINT/PLAN/BITACORA/README/Handoff/PARCHE.
2. Continuar `P01_HF_M01_SERVING_VALIDATION`.
3. Verificar runtime inference + Enchufe/Router + dataset/storage/acelerador.
4. Solo tras PASS promover HF-M01 y avanzar HF-M02 1×1.
5. P02 y P03 permanecen pendientes.

Cierre solo con ruta + SHA/diff + read-back + test/log + URL. Estado `ACTIVE_LOOP`.
