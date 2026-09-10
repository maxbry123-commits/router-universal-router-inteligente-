# PARCHE DE RECUPERACIÓN — ROUTER INTELIGENTE UNIVERSAL

Estado actual: `ACTIVE_LOOP` · contrato `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP`.

## Hecho y verificado
- HF Jobs como cómputo real.
- Catálogo público 20 por Job `6aa2513d5527934177ebfaad`.
- HF-M01 config/tokenizer/generation por Job `6aa26cc321047bf1b0371f28`.
- Adapter HF creado/read-back: commit `70b2a7d4b5ee419999e3b6f436e219370141d294`, blob `3d89e6e705fb30a55ca5ae72db05538bdabbabb7`.
- Gateway FastAPI único creado/read-back: commit `ea0392a58ce6391514471926a315a6ebd9928521`, blob `a7a2c16019adee69de597ec0abd251912a8a11ca`.
- Registry V4 sincronizado: commit `3de1df105276080ae8c94067816d2e190c8b18df`.

## GAP
- `GAP-HF-CATALOG-001`: catálogo privado requiere ruta segura de credencial.
- `GAP-HF-M01-SERVING-001`: código presente pero faltan inferencia autenticada, Enchufe/Router hot path, dataset/storage y acelerador.
- GAP P02 contractuales continúan fail-closed.

## Lista única
- [ ] P01.1 cerrar HF-M01 runtime real.
- [ ] P01.2 validar HF-M02..HF-M20 1×1.
- [ ] P01.3 consolidar gateway/registry completo.
- [ ] P02 C01-C23.
- [ ] P03 API Key Manager + E2E.

Cierre: `ruta + SHA/diff + read-back + test/log + URL`; sólo `VERIFIED_CLOSED` tras E2E real.
