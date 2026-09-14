# YAIWES — PLAN MAESTRO COMPACTO V3

## Objetivo
Construir una capa externa de razonamiento/datos y un Cognitive Control Plane determinista sin entrenar el modelo base, manteniendo cobertura global Mythos + YAIWES + Meta con ~30–35 archivos físicos y ~1.100–1.150 registros.

## Fase 0 — Resolución previa
**Context Composer vs Input Shark:** separados. Context Composer tendrá contrato `ContextRequest -> ContextPack`. Input Shark queda upstream externo no implementado hasta encontrar su contrato real. No se duplica ni se fusiona sin evidencia.

## Fase 1 — Arquitectura y registry
1. Congelar 107 métodos canónicos.
2. Asignar Tier A/B/C.
3. Definir aliases sin duplicar métodos equivalentes.
4. Crear schemas de método/caso/context/state.
5. Crear provenance obligatorio.

### Tier A — 12 críticos, 20 registros c/u
- M07 GOAL_DECOMPOSITION
- M14 DEPENDENCY_GRAPH_BUILD
- M19 CONTRADICTION_DETECTION
- M23 SIMULATION_ENGINE
- M30 REPLANNER_LOOP
- M32 DECISION_ENGINE
- Y27 SHERIFF_ACCEPTANCE_GATE
- C04 AGENT_ROUTER
- C01 SOURCE_OF_TRUTH
- C03 CONSISTENCY_ENGINE
- C05 POLICY_GUARD
- Y26 RECOVERY_STATE

Distribución Tier A: 10 debugging + 5 causal + 3 errores + 2 contraejemplos.

### Tier B — core frecuente, 10 registros c/u
Distribución recomendada: 5 debugging + 3 causal + 1 error + 1 contraejemplo.

### Tier C — soporte/formato, 7 registros c/u
Distribución recomendada: 3 debugging + 2 causal + 1 error + 1 contraejemplo.

## Fase 2 — Data compacta
Archivos únicos por familia:
- `data/mythos.jsonl`
- `data/yaiwes.jsonl`
- `data/meta_runtime.jsonl`
- `data/cognitive_control.jsonl`

Cada registro obligatorio:
`id, method_id, method, tier, category, source, commit, added_at, trigger, problem, correct_method, verification, tags`.

FABLES/MYTHOS recibe ejemplos de máxima calidad y variedad: APIs, sistemas distribuidos, bugs de estado, planificación, causalidad, hipótesis, simulación, contradicción, replanning, decisión, crítica, evidencia y recuperación.

## Fase 3 — Cognitive Control Plane
Cinco módulos reales y separados:
1. `source_of_truth.py`: jerarquía `runtime > test > repo > agent_inference > llm_text`; provenance/freshness.
2. `context_composer.py`: token budget, prioridades, compresión, deduplicación, ContextPack.
3. `consistency_engine.py`: conflictos deterministas; `CONFLICTED -> RECONCILE`.
4. `router.py`: classifier + scorer + selección paralela de método/agente/modelo.
5. `policy_guard.py`: fail-closed; capability/approval/irreversibility/sandbox gate.

## Fase 4 — Tests obligatorios
- dataset: schema, provenance, tier counts, IDs únicos, registry.
- router: clasificación, lookup, límites, selección paralela.
- control: source authority, contradiction, context budget, fail-closed.
- integration: `request -> route -> context -> consistency -> policy`.

## Fase 5 — Multi-chat
Protocolo obligatorio:
`READ_FRESH -> CLAIM -> LEASE -> CHECK_REVISION -> WRITE_SCOPE -> TEST -> EVIDENCE -> TERMINAL -> RELEASE`.

Cada nodo tiene scope exclusivo. Ningún chat debe reclamar dos nodos que comparten path de escritura.

## Fase 6 — Plugin universal, ÚLTIMO
No cablear antes. Cuando dataset/control/tests estén PASS:
1. Validar ficha v2.0.
2. Crear adapters sólo para I/O compatibles.
3. Shadow load.
4. Shadow tests.
5. Policy Guard/Sheriff approval.
6. Hot swap/cableado.
7. Evidence + telemetry + health + failover.

## Cierre
PASS sólo si:
- registry cubre los 107 métodos;
- data cumple tiers y provenance;
- cinco módulos tienen test PASS;
- integration PASS;
- Crazy Wall contiene SHA/evidencia;
- plugin final se mantiene PENDING hasta el último gate.
