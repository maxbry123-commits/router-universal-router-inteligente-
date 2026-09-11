# PARCHE DE RECUPERACIÓN — ROUTER INTELIGENTE UNIVERSAL
Estado: `VERIFIED_CLOSED` · `tel.workflow/v3` · `FAIL_CLOSED_LOOP` · FAST-CLOSE · **100%**.

## RIU-0058 — sólo 3 pasos
- [x] Paso 1 — Hugging Face: `CLOSED_EXECUTABLE_SET`; PASS reales preservados y FLAGS externos exactos mantenidos.
- [x] Paso 2 — GitHub/C01-C23: `CLOSED_HOT_PATH_EXECUTABLE_SET`; sólo bloqueantes reales del hot-path fueron cerrados.
- [x] Paso 3 — API Key Manager + E2E: `VERIFIED_CLOSED`; 100 slots, hash-only, rotate/revoke, overflow fail-closed y E2E real.

## Evidencia final
GitHub Actions `RIU FAST-CLOSE` run `34582284615`, job `103208408709`: `success`; `2 passed in 6.79s`.
El fallo previo `active_requiere_hash_real` demostró el gate fail-closed; RIU-0057 añadió el SHA-256 del adapter físico y el rerun pasó. Commit `af469152fd0306d706c67b8cf6548512fdc4f1c0`; gateway blob `e970b5de2281d236b916ea41492ee52df8454153`; test blob `23473c2a33cb9e5a451ad5a19ce5c4e5a58fc2c7`.

Los FLAGS HF/provider/storage/runtime no controlables permanecen explícitos y no invalidan el core verificado. `verify_final=PASS_GLOBAL_EXECUTABLE_CORE_100_PERCENT`.