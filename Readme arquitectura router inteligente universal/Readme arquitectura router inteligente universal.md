# Router Inteligente Universal — Arquitectura y estado de integración
Contrato: `tel.workflow/v3` · `FAIL_CLOSED_LOOP` · FAST-CLOSE · **VERIFIED_CLOSED 100%**.

## Plan autorizado — exactamente 3 pasos
1. Hugging Face — ✅ `CLOSED_EXECUTABLE_SET`: PASS ejecutables preservados; FLAGS externos/runtime explícitos.
2. GitHub/C01-C23 — ✅ `CLOSED_HOT_PATH_EXECUTABLE_SET`: se cerraron sólo bloqueantes del E2E, sin materializar contratos no necesarios.
3. API Key Manager + E2E — ✅ `VERIFIED_CLOSED`: 100 slots, hash-only, revoke/rotate y E2E real.

## Hot-path verificado
`FastAPI -> Auth/APIKeyGuard -> Enchufe Gate -> RedUniversal -> GitHub public adapter -> GitHub API -> verifier -> response`.
C01 REST, C15, C16, C17 y C20 quedaron verificados en ejecución. Componentes C01-C23 no requeridos por este hot-path permanecen como GAP no bloqueante, conforme FAST-CLOSE.

## Evidencia de cierre
GitHub Actions `RIU FAST-CLOSE` run `34582284615`, job `103208408709`: `success`; `2 passed in 6.79s`.
El primer E2E rechazó correctamente un adapter activo sin hash real. RIU-0057 lo corrigió calculando SHA-256 del adapter físico; commit `af469152fd0306d706c67b8cf6548512fdc4f1c0`, gateway blob `e970b5de2281d236b916ea41492ee52df8454153`.

## Cierre
`verify_final=PASS_GLOBAL_EXECUTABLE_CORE_100_PERCENT`. Los FLAGS HF/provider/RW-storage/tamaño/runtime siguen documentados y no se convierten en PASS ni retienen artificialmente el cierre del core.