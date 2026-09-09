# RECOVERY PATCH — ROUTER INTELIGENTE UNIVERSAL

Contrato: `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP`.

## Estado válido
- Plan limitado a 3 pasos.
- Paso 1: componentes centralizados; owner público HF 0; privados/endpoints FLAG no bloqueante.
- Paso 2 ACTIVE: Gate/conectores/registry + validator/schema/RedUniversal recuperados y verificados.
- C15 `red/enchufe_gate.py` preserva firma pública v1.5 y delega fichas v2 a `domain/schemas/enchufe_v2.py` + `enchufe/validator_v2.py`; no duplica invariantes.
- C15 producción commit `4e256e1332d41f9177e0df4806bb749cbd1f1e54`, blob `b5fdc15a4b4c3747425d7db86a81f2c4e409de9e`.
- HF Job `6aa16ff732d5d0c22c5b0912` ejecutó archivos del commit `8536808a...`: `5 passed in 0.09s`.
- Schema/validator/perfiles siguen sin autorizar inventar una policy standalone del filtro de comportamiento LLM.
- R-004 auditado fail-closed: Handoff lo declara `EXISTING_COMPLETE`, pero `router inteligente universal/infrastructure/backup/respaldo.py` responde 404 en `main`; historial de ambas rutas consultadas está vacío y no hay match `respaldo` en las ramas `download/router-missing-07`, `forensic-router-50-recovery`, `import/maxbry-router-code`.
- Se abre `GAP-R004-SOURCE-001`; no crear backup desde descripción ni marcar REUSE por presencia documental.
- Paso 3 pendiente.

## Boot de recuperación
1. Leer STATE/CHECKPOINT/PLAN/BITACORA/README arquitectura/Handoff.
2. Verificar HEAD/blobs y evidencia del último delta cerrado.
3. Para R-004, recuperar primero fuente física/canónica y ownership desde evidencia del proyecto; la declaración del Handoff no basta.
4. Si aparece fuente R-004: exact REUSE → read-back/blob → test fijo → persistir. Si no aparece: mantener GAP y pasar solo a una tarea P02 independiente segura respaldada por arquitectura.
5. Filtro LLM solo si aparece policy standalone explícita; en otro caso GAP permanece fail-closed.

## GAP-HF-CATALOG-001
No inventar modelos. Reintentar privados/endpoints solo con nueva evidencia consumible; continuar tareas P02 independientes.

## GAP-BEHAVIOR-CONTRACT-001
`validator_v2`, C05 Pydantic, perfiles y repetición son contratos estructurales/invariantes; todavía no existe evidencia de policy standalone allow/deny del comportamiento LLM.

## GAP-R004-SOURCE-001
StrategyDelta A: lectura física + historial GitHub de la ruta declarada → fuente ausente. StrategyDelta B materialmente distinta: enumeración de ramas de recuperación/importación y árbol completo → sin `respaldo`. Resultado: source/ownership no demostrado; FAIL_CLOSED.

## Refutaciones
1. Handoff `EXISTING_COMPLETE` ≠ archivo fuente existente.
2. Ruta 404 + historia vacía ≠ permiso para GENERATE un backup por inferencia.
3. Auditoría R-004 cerrada ≠ C19 integrado ≠ Paso 2 cerrado ≠ E2E Paso 3.
