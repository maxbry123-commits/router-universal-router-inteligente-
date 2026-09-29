# DOC-A00_MISSION_CONTRACT + GOAL_LOCK + ASK_COUNCIL
ROLE: CHAT A — ARCHITECT
STATUS: DRAFT (bloquea si hay CONFLICT sin resolver)

---

## 1. MISSION_CONTRACT

```yaml
mission_id: "MAXBRY-ROUTER-BACKEND-001"
workspace_id: "maxbry-router"
objective: >
  Backend Python determinista (95%) + asistencia LLM mínima (5%) que actúa
  como enrutador/conector universal: usuario ⇄ N conectores ⇄ destinos
  reales, vía Enchufe Gate v2.0, motor DAG con templates fijas (T01-T12),
  y mecanismo de ventanas encadenables (1-100) para equipos de IA
  configurables por el usuario sin tocar el código fuente.
scope:
  - "Motor DAG determinista (DAGParser, DAGOrchestrator)"
  - "Enchufe Gate v2.0 + validator_v2.py integrado"
  - "Catálogo de Conectores (existentes + nuevos de v6)"
  - "RedUniversal (namespaces, rutas, salud por nodo)"
  - "R1-R10 + Cost Optimizer completos (cierre de gaps de GAP_01_ROUTER.md)"
  - "InboundGatekeeper (Alcabala)"
  - "SecretVault cifrado"
  - "CodeSandbox dual (Docker + fallback subprocess)"
  - "Motor de ventanas encadenables generalizado (Python)"
  - "Persistencia Postgres/Redis tras enchufe plugin de storage"
  - "API REST + WS/SSE de contrato con los 5 paneles ya diseñados"
out_of_scope:
  - "Frontend/UI (fase posterior, no se toca ahora)"
  - "Lógica interna fija de planner/critic/verifier/consensus/judge"
  - "Importación completa de los repos reciclables (solo fusión de piezas puntuales)"
  - "Workflow Mavis M3↔M2.7 como componente de código"
  - "Motor de búsqueda/auto-relleno tipo Perplexity (mejora futura, solo se deja el hook de extensión)"
goals: "Ver DOC-A01_PROJECT_ANALYSIS.md → GOALS"
constraints:
  - "Repo único en GitHub (maxbry-router), arquitectura hexagonal"
  - "95% determinista / 5% LLM"
  - "REUSE > PATCH > ADAPT > GENERATE"
  - "TASK_LIMIT_CHAT_B ≤ 2000 LOC · CODE_BLOCK ≤ 500 LOC"
  - "Secretos solo por referencia (vault/env), nunca en código ni trazabilidad"
  - "Compatibilidad Enchufe v1.5 → v2.0 obligatoria (defaults, no ruptura)"
acceptance: "Ver DOC-A01 → GOALS.success_conditions + definition_of_done"
contracts:
  - "Protocol Conector: async enviar(payload)->dict, async sondear()->bool"
  - "Enchufe v2.0 JSON Schema (artifact_id, categoria, etapa, contrato, ejecucion, seguridad, firma)"
quality_bar: "PRODUCTION/ADVANCED — no MVP. Ver prompt maestro secciones 41-45."
```

## 2. GOAL_LOCK

Ningún Chat B puede, por iniciativa propia:
- Cambiar el objetivo, alcance o criterios de aceptación de arriba.
- Introducir un ORM/DB/framework distinto al fijado en DOC-A02 sin BLOCKER.
- Reintroducir lógica de razonamiento fija (planner/critic/etc.) — eso es out_of_scope.
- Sustituir Docker-only o subprocess-only sin mantener paridad de contrato dual.
- Tocar el schema Enchufe v2.0 sin registrar el cambio como conflicto.

Cualquier desviación → `BLOCKER-TXXX.md` (sección 37 del prompt maestro).

---

## 3. ASK COUNCIL — 12 PUNTOS

| # | Punto | Observation | Risk | Decision | Evidence | Action |
|---|---|---|---|---|---|---|
| 1 | OBJECTIVE | Objetivo único y no ambiguo tras Q&A con usuario | Bajo | **AUTHORIZE** | DOC-A01 OBJECTIVE | — |
| 2 | SCOPE | in/out of scope explícitos y confirmados (OI-01/02/03 resueltos) | Bajo | **AUTHORIZE** | DOC-A01 SCOPE + resoluciones OI | — |
| 3 | ARCHITECTURE | Hexagonal (api/domain/engine/infrastructure/core) ya propuesta por el usuario y consistente con v6 | Bajo | **AUTHORIZE** | Mensaje del usuario (arquitectura DDD) | Formalizar en DOC-A02 |
| 4 | EXISTING_CODE/REUSE | Solo 5 artefactos son código real (enchufe_gate, conectores, red_universal, validator_v2, respaldo.py); todo lo demás se genera | Medio — riesgo de sobre-generar si aparece el README de 26 repos y se duplica lógica | **AUTHORIZE con condición** | DOC-A01 EXISTING_CODE | Chat B debe revisar el README de repos reciclables (cuando se suba) ANTES de generar cada módulo nuevo |
| 5 | DEPENDENCIES | FastAPI, Pydantic v2, docker SDK, cryptography, asyncpg/aiomysql/redis.asyncio | Bajo | **AUTHORIZE** | DOC-A01 DEPENDENCIES | Fijar versiones en DOC-A02 |
| 6 | CONTRACTS/SCHEMAS | Protocol Conector + Enchufe v2.0 Schema ya completos y compatibles con v1.5 | Bajo | **AUTHORIZE** | FABLES_ENCHUFE_UNIVERSAL_v2.md | Integrar validator_v2.py tal cual, sin reescribir |
| 7 | SECURITY | SecretVault cifrado + Alcabala + Sandbox dual + firma GPG en ficha | Medio — CodeSandbox ejecuta código arbitrario del usuario | **AUTHORIZE con condición** | Enchufe v2.0 campo `seguridad` | Límites de recursos obligatorios (timeout_ms, max_memoria_mb) en AMBOS modos (Docker y subprocess), sin excepción |
| 8 | DETERMINISM | DAG fijo (T01-T12), LLM solo en 5% acotado (auto-relleno/búsqueda futura) | Bajo | **AUTHORIZE** | Regla 90/10 (aquí 95/5) prompt maestro §41 | — |
| 9 | TESTABILITY | Checklist de tests ya listado en v6 §10, ampliable a los módulos nuevos (R5/R6/R8/CostOptimizer) | Bajo | **AUTHORIZE** | resumen v6.md §10 | Extender con tests de ventanas encadenables y CodeSandbox dual |
| 10 | INTEGRATION | API REST/WS debe respetar el contrato de los 98 endpoints/funciones ya diseñados para los 5 paneles | Medio — UI llega después, riesgo de desalineación de contrato si cambia | **AUTHORIZE con condición** | __router-funciones.md | Congelar el contrato de API (rutas + payloads) en DOC-A02 antes de implementar, aunque la UI no se toque aún |
| 11 | TRACEABILITY | PROJECT→SOURCE→COMPONENT→DAG→TASK→CHAT_B→ROOT_ID→FILE→FUNCTION→TEST→RESULT | Bajo | **AUTHORIZE** | Prompt maestro §9, §30 | — |
| 12 | DEFINITION_OF_DONE | Ver DOC-A01 GOALS.definition_of_done | Bajo | **AUTHORIZE** | — | — |

**Decision Gate global: AUTHORIZE** (con 3 condiciones registradas en puntos 4, 7 y 10 — ninguna es bloqueante, se incorporan como reglas obligatorias en DOC-A02_ARCHITECTURE).

---

## Siguiente paso

Con MISSION_CONTRACT + GOAL_LOCK + ASK_COUNCIL en AUTHORIZE, quedo habilitado para construir:
- **DOC-A02_ARCHITECTURE.md** (componentes completos, capas hexagonales)
- **DOC-A03_WORKFLOW_DAG.yaml**
- **DOC-A04_FILE_ROOT_MAP.md**
- **DOC-A05_DEPENDENCY_MAP.json**

¿Procedo a construir DOC-A02_ARCHITECTURE.md ahora, o prefieres revisar/corregir algo de este documento primero?
