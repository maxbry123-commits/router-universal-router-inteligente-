# RECOVERY PATCH — ROUTER INTELIGENTE UNIVERSAL

Contrato: `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP`.

## Estado válido
- Plan limitado a 3 pasos.
- Paso 1: componentes centralizados; owner público HF 0; privados/endpoints FLAG no bloqueante.
- Paso 2 ACTIVE: Gate/conectores reutilizados desde fuente canónica.
- `ConectorHuggingFace`, `ConectorDB`, `ConectorGitLab` y `ConectorMCPApp` permanecen contractualmente verificados.
- `ConectorVPS` ya existía en `router inteligente universal/red/conectores.py`; se aplicó REUSE y solo WIRE en registry, sin duplicar adapter.
- Registry VPS commit `2b57fe8e4ef7965ee23a6a086415ef8c21db7f60`.
- Test VPS commit `7f04404876b2fb1123742d32dd4d48741a2b388d`.
- Verify remoto: HF Job `6aa12c19900620b5c77e61d2` status `success`; `PASS_CONECTOR_VPS_V6: 3/3`.
- Paso 3 pendiente.

## Boot de recuperación
1. Leer STATE/CHECKPOINT/PLAN/BITACORA/README arquitectura.
2. Verificar HEAD y SHAs.
3. Continuar P02 cola 1×1 con siguiente conector v6 respaldado por arquitectura; conservar registry y baselines.

## GAP-HF-CATALOG-001
No inventar modelos. Reintentar privados/endpoints solo con nueva evidencia consumible; continuar tareas P02 independientes.

## Refutaciones
1. ConectorVPS contractual PASS != VPS remoto real del Paso 3.
2. Registry con VPS != catálogo v6 completo.
3. PASS contractual != Paso 2 ni Paso 3 completos.
