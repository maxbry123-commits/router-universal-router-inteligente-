# PARCHE DE RECUPERACIÓN — ROUTER INTELIGENTE UNIVERSAL

Estado actual: `ACTIVE_LOOP` · contrato `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP`.

## Hecho y verificado
- HF Jobs como cómputo real.
- Catálogo público 20 por Job `6aa2513d5527934177ebfaad`.
- HF-M01 config/tokenizer/generation por Job `6aa26cc321047bf1b0371f28`.
- HF-M01 inferencia local real por Job `6aa288a521047bf1b0372324` COMPLETED.
- HF adapter y gateway FastAPI único preservados.
- `router_hot_path.py` creado sobre Enchufe Gate + RedUniversal, commit `86f5f545f070dc3180652e73265f6fc77ba1e514`.
- gateway actualizado, commit `6da8ecd573986bc4e77a2c749e37d9f34955bd57`.
- test hot-path, commit `8509fa25793fec73a1e9ce023787713df5ed4225`.
- HF Job `6aa297195527934177ec0aed` COMPLETED: read-back desde main + `2 passed in 1.25s`, RC=0.
- auditoría RIU-0039: commit `f08191ec91f0d74850799b38b44298bc77f0cfe9`.

## GAP
- `GAP-HF-CATALOG-001`: catálogo privado requiere ruta segura de credencial.
- `GAP-HF-M01-SERVING-001`: Enchufe/RedUniversal determinista PASS; dataset/storage + hosted provider autenticado siguen pendientes.
- GAP P02 contractuales continúan fail-closed.

## Lista única
- [ ] P01.1 cerrar HF-M01 dataset/storage + provider autenticado.
- [ ] P01.2 validar HF-M02..HF-M20 1×1.
- [ ] P01.3 consolidar gateway/registry completo.
- [ ] P02 C01-C23.
- [ ] P03 API Key Manager + E2E.

Cierre: `ruta + SHA/diff + read-back + test/log + URL`; sólo `VERIFIED_CLOSED` tras E2E real.