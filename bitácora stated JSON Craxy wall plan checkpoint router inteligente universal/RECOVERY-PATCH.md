# RECOVERY PATCH — ROUTER INTELIGENTE UNIVERSAL

Contrato: `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP`.

## Estado válido
- Plan limitado a 3 pasos.
- Paso 1: componentes centralizados; owner público HF 0; privados/endpoints FLAG no bloqueante.
- Paso 2 ACTIVE: Gate/conectores/registry + validator/schema/RedUniversal recuperados y verificados.
- C15 `red/enchufe_gate.py` preserva firma pública v1.5 y ahora delega fichas v2 a `domain/schemas/enchufe_v2.py` + `enchufe/validator_v2.py`; no duplica invariantes.
- C15 producción commit `4e256e1332d41f9177e0df4806bb749cbd1f1e54`, blob `b5fdc15a4b4c3747425d7db86a81f2c4e409de9e`.
- Tests: v1.5 commit `e938ff557670d27763c6d5b507fd2946e1cd6702`; v2 commit `8536808a3a53cab0afb89b007f5e7095bf37a047`.
- HF Jobs `6aa16f6932d5d0c22c5b090a` y `6aa16f8d32d5d0c22c5b090c` fueron refutados por loader/cache del harness; StrategyDelta registró módulos en `sys.modules` y fijó el commit exacto.
- HF Job `6aa16ff732d5d0c22c5b0912` ejecutó archivos del commit `8536808a...`: `5 passed in 0.09s`.
- Schema/validator/perfiles siguen sin autorizar inventar una policy standalone del filtro de comportamiento LLM.
- Paso 3 pendiente.

## Boot de recuperación
1. Leer STATE/CHECKPOINT/PLAN/BITACORA/README arquitectura/Handoff.
2. Verificar HEAD/blobs y evidencia HF del último delta C15.
3. Continuar P02 cola 1×1 auditando R-004 `infrastructure/backup/respaldo.py` contra fuente física/canónica.
4. REUSE R-004 solo si presencia y ownership quedan demostrados; test fijo + read-back.
5. Filtro LLM solo si aparece policy standalone explícita; en otro caso GAP permanece fail-closed.

## GAP-HF-CATALOG-001
No inventar modelos. Reintentar privados/endpoints solo con nueva evidencia consumible; continuar tareas P02 independientes.

## GAP-BEHAVIOR-CONTRACT-001
`validator_v2`, C05 Pydantic, perfiles y repetición son contratos estructurales/invariantes; todavía no existe evidencia de policy standalone allow/deny del comportamiento LLM.

## Refutaciones
1. C15 v1.5/v2 + 5 tests PASS != filtro LLM implementado.
2. C15 contractual PASS != R-004 ni resto de Paso 2 cerrado.
3. Tests contractuales HF PASS != E2E HF→GitHub→API→agentes del Paso 3.
