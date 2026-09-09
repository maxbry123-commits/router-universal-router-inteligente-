# RECOVERY PATCH — ROUTER INTELIGENTE UNIVERSAL

Contrato: `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP`.

## Estado válido
- Plan limitado a 3 pasos.
- Paso 1: componentes centralizados; owner público HF verificado en 0 modelos; registry persistido no contiene `model_id` HF; privados/endpoints quedan FLAG no bloqueante.
- Paso 2 ACTIVE: Gate y conectores reutilizados desde fuente canónica antes de ampliar capacidad.
- Baseline conectores: `8dc43490cc14f21c6d09d9e3d824606868679766`; test `94ad8b8879c8c03b2f084ac62059bd346da6a610`; `3 passed in 0.11s`.
- `ConectorHuggingFace` v6 integrado quirúrgicamente en `router inteligente universal/red/conectores.py`; commit `eb3d9fc2f67a33d8cf22056488ea299a2ffa7875`, blob `e7a125354e32b718a9410f1c53485dc75ca4cf15`.
- Test HF: `router inteligente universal/tests/test_conector_huggingface_v6.py`; commit `0458b589e89d5c4ff9245528f3acb515936fa34e`, blob `90425867a0c2f1b090e6a51c584cb018fda13b18`; exact-blob pytest `3 passed in 0.10s`.
- Paso 3 pendiente.

## Boot de recuperación
1. Leer STATE/CHECKPOINT/PLAN/BITACORA/README arquitectura.
2. Verificar HEAD y SHAs.
3. Continuar P02 cola 1×1 con el siguiente conector v6 demostrado por arquitectura; preservar `ConectorHTTP`, `ConectorMCP`, `ConectorGitHub` y `ConectorHuggingFace` ya verificados.

## GAP-HF-CATALOG-001
No inventar modelos. Reintentar privados/endpoints solo cuando exista nueva credencial/evidencia consumible; mientras tanto continuar tareas P02 independientes.

## Refutaciones
1. Adapter HF probado contra contrato != endpoint/modelo HF real confirmado.
2. Un conector v6 integrado != catálogo v6 completo.
3. PASS unitario != Paso 2 ni Paso 3 completos.
