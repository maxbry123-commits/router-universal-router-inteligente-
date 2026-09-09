# PLAN DE TAREAS — ROUTER INTELIGENTE UNIVERSAL

Contrato: `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP`

## Lista única activa
1. 📌🛜 **Paso 1 — componentes + LLM/Hugging Face** — PARTIAL/CLOSED_SAFE
   - ✅ componentes movidos al code root;
   - ✅ bridge HF local auditado;
   - ✅ owner público HF: COUNT 0;
   - 🚩 GAP-HF-CATALOG-001: privados/endpoints sin `model_id` confirmado; no inventar adapters.
2. 📌 **Paso 2 — cableado + poda + código faltante** — ACTIVE
   - ✅ REUSE `red/conectores.py`; conectores HF/DB/GitLab/MCPApp/VPS/Memoria/Interno/Webhook + registry verificados;
   - ✅ `enchufe/validator_v2.py`, C05 `domain/schemas/enchufe_v2.py` y R-003 `red/red_universal.py` materializados/verificados desde fuentes canónicas;
   - ✅ C15 auditado contra v1.5 + contrato FABLES v2.0: PATCH mínimo conserva `validar_contrato_conexion()` y delega fichas v2 a `EnchufeV2` + `validator_v2`; añade `agent` sin crear segundo validador;
   - ✅ C15 producción `router inteligente universal/red/enchufe_gate.py` commit `4e256e1332d41f9177e0df4806bb749cbd1f1e54`, blob `b5fdc15a4b4c3747425d7db86a81f2c4e409de9e`;
   - ✅ tests v1.5/v2 commits `e938ff557670d27763c6d5b507fd2946e1cd6702` y `8536808a3a53cab0afb89b007f5e7095bf37a047`;
   - ✅ dos harness previos refutados por carga/cache; StrategyDelta fijó `sys.modules` + commit exacto; HF Job `6aa16ff732d5d0c22c5b0912`: `5 passed in 0.09s`;
   - 🚩 GAP-BEHAVIOR-CONTRACT-001 permanece: schema/validator/perfiles no equivalen a policy standalone de comportamiento LLM; prohibido inferir/generar semántica del filtro;
   - ✅ auditoría R-004 ejecutada: lectura directa de `router inteligente universal/infrastructure/backup/respaldo.py` = 404; historial GitHub vacío en ruta objetivo y root-relative; tres ramas locales auditadas sin match `respaldo`;
   - 🚩 GAP-R004-SOURCE-001: Handoff declara C19/R-004 EXISTING_COMPLETE pero no hay fuente/ownership demostrable; prohibido REUSE por declaración y prohibido GENERATE por inferencia.
3. 📌✅ **Paso 3 — tests integración** — PENDING
   - Hugging Face + GitHub + API + agentes;
   - exigir ruta + SHA/diff + read-back + test/log.

Cola 1×1 actual: recuperar fuente/ownership canónico R-004 desde evidencia del proyecto; solo entonces REUSE exacto → test → persistir. Si sigue ausente, mantener GAP y continuar únicamente con tarea P02 independiente respaldada por arquitectura.
Reglas: no sobreingeniería; no añadir pasos; REUSE > PATCH > ADAPT > GENERATE; archivo presente ≠ integrado; declaración documental ≠ fuente; unit/contract PASS ≠ E2E.
