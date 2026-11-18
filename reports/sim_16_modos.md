| # | Familia | Modo | Detectado | Adapter | Dataset | LoRA | Destino | Veredicto |
|---|---|---|---|---|---|---|---|---|
| 1 | codigo | code_refactor | code_refactor | OK | OK | n/a | swe-code-s1 | PASS |
| 2 | codigo | code_debug | code_debug | OK | OK | OK | swe-code-s2 | PASS |
| 3 | codigo | code_review | code_review | OK | OK | OK | swe-code-s2 | PASS |
| 4 | codigo | code_generate | code_generate | OK | OK | OK | swe-code-s1 | PASS |
| 5 | codigo | architecture | architecture | OK | OK | OK | swe-code-s3 | PASS |
| 6 | codigo | reasoning | reasoning | n/a | n/a | n/a | - | SIN ADAPTER |
| 7 | codigo | tool_call | tool_call | OK | OK | OK | proveedor externo (NVIDIA/Groq) | PASS |
| 8 | codigo | planning | planning | n/a | n/a | n/a | - | SIN ADAPTER |
| 9 | codigo | documentation | documentation | OK | OK | n/a | swe-code-s1 | PASS |
| 10 | codigo | frontend | frontend | OK | OK | OK | swe-code-s1 | PASS |
| 11 | codigo | 3d_code | 3d_code | OK | OK | OK | swe-code-s3 | PASS |
| 12 | codigo | verification | verification | OK | OK | n/a | swe-code-s1 | PASS |
| 13 | servicio | swe_code | swe_code | OK | n/a | n/a | servicio | PASS |
| 14 | servicio | swe_free | swe_free | OK | n/a | n/a | servicio | PASS |
| 15 | servicio | team_qwe | team_qwe | OK | n/a | n/a | servicio | PASS |
| 16 | servicio | deployment | deployment | OK | n/a | n/a | servicio | PASS |
