# RECOVERY PATCH — ROUTER INTELIGENTE UNIVERSAL
Contrato: `tel.workflow/v3` · `FAIL_CLOSED_LOOP` · FAST-CLOSE · **VERIFIED_CLOSED 100%**.

## Estado RIU-0058
- Paso 1: `CLOSED_EXECUTABLE_SET`; PASS reales preservados y FLAGS externos/runtime siguen explícitos, no convertidos en PASS.
- Paso 2: `CLOSED_HOT_PATH_EXECUTABLE_SET`; C01 REST + C20 Auth/APIKeyGuard + C15 Enchufe Gate + C17 RedUniversal + C16 GitHub public adapter + verifier ejecutados en el hot-path.
- Paso 3: `VERIFIED_CLOSED`; API Key Manager probado hasta 100 slots, hash-only, revoke/rotate, slot 101 fail-closed y E2E real.
- GitHub Actions run `34582284615`, job `103208408709`: success, `2 passed in 6.79s`.
- Código verificado: commit `af469152fd0306d706c67b8cf6548512fdc4f1c0`; gateway blob `e970b5de2281d236b916ea41492ee52df8454153`; E2E test blob `23473c2a33cb9e5a451ad5a19ce5c4e5a58fc2c7`.

## Recuperación
Releer STATE/CHECKPOINT/BITACORA/PLAN; no reabrir P01-P03 salvo cambio de requisitos o regresión demostrada. Los FLAGS externos de HF/provider/RW-storage permanecen como límites documentados y no invalidan el core ejecutable verificado.