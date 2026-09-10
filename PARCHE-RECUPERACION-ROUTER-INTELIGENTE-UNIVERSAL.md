# PARCHE DE RECUPERACIÓN — ROUTER INTELIGENTE UNIVERSAL

Estado actual: `ACTIVE_LOOP` · contrato `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP`.

## Hecho y verificado
- HF Jobs como cómputo real.
- Catálogo público 20 por Job `6aa2513d5527934177ebfaad`.
- HF-M01 config/tokenizer/generation por Job `6aa26cc321047bf1b0371f28`.
- HF-M01 inferencia local real por Job `6aa288a521047bf1b0372324` COMPLETED: `RIU_HF_M01_OK`, `HF_M01_REAL_COMPUTE_OK=True`, 596049920 parámetros runtime, CPU, 7.108s.
- Evidencia RIU-0038: commit `d798b6b878d3876ce866584647fd41b9cf8c6c23`.
- Adapter HF creado/read-back: commit `70b2a7d4b5ee419999e3b6f436e219370141d294`, blob `3d89e6e705fb30a55ca5ae72db05538bdabbabb7`.
- Gateway FastAPI único creado/read-back: commit `ea0392a58ce6391514471926a315a6ebd9928521`, blob `a7a2c16019adee69de597ec0abd251912a8a11ca`.
- Registry V4 sincronizado: commit `3de1df105276080ae8c94067816d2e190c8b18df`.

## GAP
- `GAP-HF-CATALOG-001`: catálogo privado requiere ruta segura de credencial.
- `GAP-HF-M01-SERVING-001`: compute real PASS; faltan FastAPI→Enchufe→Router hot path y dataset/storage; hosted provider auth sigue sin certificarse.
- GAP P02 contractuales continúan fail-closed.

## Lista única
- [ ] P01.1 cerrar HF-M01 FastAPI→Enchufe→Router + dataset/storage.
- [ ] P01.2 validar HF-M02..HF-M20 1×1.
- [ ] P01.3 consolidar gateway/registry completo.
- [ ] P02 C01-C23.
- [ ] P03 API Key Manager + E2E.

Cierre: `ruta + SHA/diff + read-back + test/log + URL`; sólo `VERIFIED_CLOSED` tras E2E real.
