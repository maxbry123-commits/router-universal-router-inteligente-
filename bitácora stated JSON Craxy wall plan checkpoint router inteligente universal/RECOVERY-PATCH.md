# RECOVERY PATCH — ROUTER INTELIGENTE UNIVERSAL

Contrato: `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP`.

## Estado válido
- Plan limitado a 3 pasos.
- Paso 1: componentes centralizados; owner público HF 0; privados/endpoints FLAG no bloqueante.
- Paso 2 ACTIVE: Gate/conectores reutilizados desde fuente canónica.
- `ConectorHuggingFace`, `ConectorDB` y `ConectorGitLab` permanecen contractualmente verificados.
- `ConectorMCPApp` vive en `router inteligente universal/red/conector_mcp_app.py` y extiende `ConectorMCP`; no crea segundo core.
- MCP App adapter commit `8a45204be6c3de7a2b8e95f648ef2cbc678dbda0`, blob `8411989712033186312516c0c229a4facd976446`.
- Registry MCP App commit `1289c5b57e72029a95f9d794eac5ea648c71f9e2`, blob `6c6d4d0efe3e12d9c8512c71d14d80555cb93442`.
- Test MCP App commit `1df8b57fc5a410a383a1a1b4e2b78535eedc5efe`, blob `950c5f4d2d8c974253ff24385352d3504412565c`.
- Verify remoto: HF Job `6aa11dac32d5d0c22c5afb80` status `success` ejecutando pytest del contrato MCP App.
- Paso 3 pendiente.

## Boot de recuperación
1. Leer STATE/CHECKPOINT/PLAN/BITACORA/README arquitectura.
2. Verificar HEAD y SHAs.
3. Continuar P02 cola 1×1 con siguiente conector v6 respaldado por arquitectura; conservar registry y baselines.

## GAP-HF-CATALOG-001
No inventar modelos. Reintentar privados/endpoints solo con nueva evidencia consumible; continuar tareas P02 independientes.

## Refutaciones
1. MCP App contractual PASS != servidor MCP App remoto real del Paso 3.
2. Registry con MCP App != catálogo v6 completo.
3. PASS contractual != Paso 2 ni Paso 3 completos.
