# XRAY_REPORT — compresión de la auditoría (fases 0-9)

- commit: `bb3559e66f9ca160031b9da3c5b65aecb807fa45`
- branch: `master`
- tree: `560e9d06f9463f30ff5714a3c43b1d2c83eb67a8`
- generado: 2026-11-16T08:00:07Z
- constitution_ref: `TAREA_01_FUENTE_DE_LA_VERDAD.md`

## 1 · IDENTIDAD (evidencia: FINGERPRINT.json)

| campo | valor |
|---|---|
| repo | canvas |
| commit_sha | `bb3559e66f9ca160031b9da3c5b65aecb807fa45` |
| tree_sha | `560e9d06f9463f30ff5714a3c43b1d2c83eb67a8` |
| ficheros inventariados | 41 |
| ficheros rastreados por git | 66 |
| excluidos | 25 |
| ausentes | 0 |

## 2 · COBERTURA (solo con evidencia; sin porcentajes estimados)

| metrica | valor | evidencia |
|---|---|---|
| inventario | 41/66 ficheros | `INVENTORY.json`.coverage |
| simbolos | 370 | `raw/symbols.json` |
| imports | 152 | `WIRING.json`.counts |
| endpoints | 17 | `CONTRACTS.md` |
| env vars | 20 | `CONTRACTS.md` |
| gaps | 0 | `GAPS.md` |
| acciones | 0 | `NEXT_ACTIONS.md` |

## 3 · GAPS por tipo (conteo evidenced)

| tipo | gaps |
|---|---|
| GAP | 0 |
| ERROR | 0 |
| DRIFT | 0 |
| BROKEN_CANDIDATE | 0 |
| HUÉRFANO | 0 |

## 4 · Veredictos docs vs code

| veredicto | filas |
|---|---|
| CONFIRMADO | 0 |
| CONTRADICHO | 0 |
| SIN_EVIDENCIA | 0 |

## 5 · CONSTITUCIÓN (checklist binario: se cumple o no; no se pondera)

| item | estado | evidencia |
|---|---|---|
| 1_STATE_FASES_0_9 | OK | STATE.json presente; fases 0-8 completas=9/9; fase9=EXECUTING (se marca COMPLETED al cerrar la fase) |
| 2_FINGERPRINT_COMMIT_TREE | OK | commit_sha=bb3559e66f9ca160031b9da3c5b65aecb807fa45 tree_sha=560e9d06f9463f30ff5714a3c43b1d2c83eb67a8 commit_date=2026-11-16T08:00:06+00:00 |
| 3_INVENTARIO_COBRE_100 | OK | tracked=66 inventariados=41 excluidos=25 ausentes=0 |
| 4_WIRING_IMPORTS_NO_VACIOS | OK | imports=152 con_ruta_linea=152 |
| 5_CONTRACTS_RUTA_LINEA | OK | CONTRACTS.md presente; endpoints=17 env_vars=20 filas_sin_ruta_linea=0 |
| 6_GAPS_VEREDICTOS | OK | filas_gap=0 filas_verificacion=25 veredictos_invalidos=0 |
| 7_NEXT_ACTIONS_EVIDENCIA | OK | acciones=0 invalidas=0 gaps=0 |
| 8_VALIDATION_PASS | OK | raw/validation.json escrito con PASS=True |
| 9_GAPS_JSON_EVIDENCIA | OK | gaps_json=0 invalidos=0 |
| 10_GAPS_CON_ESTADO | OK | gaps_sin_estado=0 ([]) |
| 11_CERO_SECRETOS | OK | fugas=0 []; ocurrencias_literal_prefijo=28 |
| 12_V4_MISMO_COMMIT | OK | fingerprint=bb3559e66f9c GAPS.md=bb3559e66f9c NEXT_ACTIONS.md=bb3559e66f9c |
| 13_SHA256_RECOMPROBADO | OK | ficheros=41 sha_distinto=0 ausentes=0 |

## 6 · ESTADO DE LA TAREA

| campo | valor |
|---|---|
| estado | VALIDATING (cierre en fase 9) |
| fase actual | fingerprint + validacion |
| gaps abiertos | 0 |

## 7 · Artefactos

- `STATE.json`
- `MANIFEST.md`
- `ARCHITECTURE.md`
- `WIRING.json`
- `INVENTORY.json`
- `CONTRACTS.md`
- `GAPS.md`
- `NEXT_ACTIONS.md`
- `XRAY_REPORT.md`
- `FINGERPRINT.json`
- `raw/`
