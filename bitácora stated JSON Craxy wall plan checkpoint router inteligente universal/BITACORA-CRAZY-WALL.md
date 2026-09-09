# BITÁCORA CRAZY WALL — ROUTER INTELIGENTE UNIVERSAL

**Contrato:** `tel.workflow/v3`
**Modo:** `FAIL_CLOSED_LOOP`

## RIU-0001 — BASELINE
Método de trabajo replicado desde UI YAIWES sin copiar su arquitectura funcional.

## RIU-0002 — COMPONENTES OPEN SOURCE
Componentes centralizados y movidos a `router inteligente universal/Componente open soure router inteligente universal/`.

## RIU-0003 — ÍNDICE / HANDOFF
Índice + Handoff C01-C23 con regla `presencia != integración`.

## RIU-0004 — PLAN 3 PASOS
1. Componentes + auditoría LLM/HF/FastAPI.
2. Cableado + poda + faltantes + filtro LLM.
3. Test HF + GitHub + API + agentes.

## RIU-0005 — HF REUSE / GAP
Bridge HF auditado; owner público HF COUNT 0; privados/endpoints quedan `GAP-HF-CATALOG-001` no bloqueante; prohibido inventar `model_id`.

## RIU-0006 — P02 REUSE ENCHUFE GATE
`router inteligente universal/red/enchufe_gate.py` baseline v1.5 verificado.

## RIU-0007 — P02 REUSE CONECTORES BASELINE
`red/conectores.py` reutilizado sin reescribir HTTP/MCP.

## RIU-0008..0015 — P02 CONECTORES V6
HF/DB/GitLab/MCPApp/VPS/Memoria/Interno/Webhook + registry verificados con tests remotos HF; sin segundo core.

## RIU-0016 — P02 AUDIT RECOVERY CONTRATO FILTRO LLM
README arquitectura ordenó materializar filtro LLM únicamente con contrato definido/recuperado. Se abrió `GAP-BEHAVIOR-CONTRACT-001` sin generar policy.

## RIU-0017 — P02 RECOVER + MATERIALIZE VALIDATOR V2
`enchufe/validator_v2.py` recuperado desde FABLES Enchufe Universal v2, blob fuente `1f2de5b0578391164e6f6f7331507299130e8579`; HF Job `6aa15fea900620b5c77e6fa1`: `6 passed in 0.02s`.

## RIU-0018 — P02 MATERIALIZE C05 ENCHUFE SCHEMA PYDANTIC V2
`domain/schemas/enchufe_v2.py` materializado desde JSON Schema FABLES; HF Job `6aa165be32d5d0c22c5b07df`: `4 passed in 0.09s`.

## RIU-0019 — P02 REUSE R-003 RED UNIVERSAL
`red/red_universal.py` recuperado desde fuente canónica, blob `66154b60ad53aa797094df8741389c8427f9bec0`; HF Job `6aa16b68900620b5c77e7259`: `5 passed in 0.05s`.

## RIU-0020 — P02 PATCH C15 ENCHUFE GATE v1.5→v2.0
Auditoría cruzó el Gate v1.5 fuente `692daca7ace7ac983aeb585dd05ac281e571f2f3` contra Enchufe Universal v2 fuente `1f2de5b0578391164e6f6f7331507299130e8579`. El delta demostrado: v1.5 excluía `agent` y no delegaba invariantes v2. Se aplicó PATCH mínimo manteniendo `validar_contrato_conexion()` y la ruta v1.5; fichas v2 delegan a `EnchufeV2.model_validate()` + `validator_v2.validar()` sin duplicar invariantes. Producción commit `4e256e1332d41f9177e0df4806bb749cbd1f1e54`, blob `b5fdc15a4b4c3747425d7db86a81f2c4e409de9e`. Tests v1.5/v2: commits `e938ff557670d27763c6d5b507fd2946e1cd6702` y `8536808a3a53cab0afb89b007f5e7095bf37a047`. HF Job `6aa16ff732d5d0c22c5b0912`: `5 passed in 0.09s`.

## RIU-0021 — P02 AUDIT R-004 BACKUP / RESPALDO
Handoff declara C19/R-004 `infrastructure/backup/respaldo.py` como `EXISTING_COMPLETE → REUSE`, pero lectura directa del destino activo devolvió 404. Historial GitHub para `router inteligente universal/infrastructure/backup/respaldo.py` y `infrastructure/backup/respaldo.py` devolvió `[]`. StrategyDelta distinto: se enumeraron las ramas `download/router-missing-07` (`7fa837fa...`), `forensic-router-50-recovery` (`519cae1...`) e `import/maxbry-router-code` (`949c71f...`) y sus árboles; ninguna contiene match `respaldo`. Se abre `GAP-R004-SOURCE-001`; no se escribió código, no se marcó REUSE y el progreso permanece 93%.

## COUNCIL12 / CROSS-CHECK / CODA / VERIFY_FINAL RIU-0021
PASS de auditoría fail-closed: 12 perspectivas convergen en que una declaración documental no demuestra source/ownership; cross-check Handoff↔main↔history↔branches encontró contradicción; CODA preservó `REUSE > PATCH > ADAPT > GENERATE`; `verify_final` confirma que no hubo implementación falsa ni avance porcentual artificial.

## 3 REFUTACIONES
1. Handoff `EXISTING_COMPLETE` ≠ archivo fuente recuperado.
2. Ausencia de fuente ≠ autorización para generar `respaldo.py` desde la descripción.
3. Auditoría R-004 PASS ≠ C19 integrado ≠ Paso 2 cerrado ≠ E2E Paso 3.

## NEXT
Cola 1×1: recuperar source/ownership canónico R-004 desde evidencia del proyecto; si sigue ausente, mantener GAP y continuar únicamente una tarea P02 independiente segura respaldada por arquitectura. Filtro LLM sigue fail-closed hasta policy explícita.
