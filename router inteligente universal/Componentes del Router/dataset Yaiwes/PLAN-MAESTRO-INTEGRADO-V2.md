# YAIWES — PLAN MAESTRO INTEGRADO V2

## ÚNICA RAÍZ AUTORIZADA

`maxbry123-commits/router-universal-router-inteligente-/main/dataset Yaiwes/`

No crear, editar, mover ni borrar nada fuera de esa raíz.

## CONTRATO DEL DATASET
Por cada método: 10 debugging + 5 patrones causales + 3 errores similares/conocidos + 2 contraejemplos = 20 registros.

## COBERTURA
- 40 métodos MYTHOS/FABLES = 800 registros.
- 42 métodos/sistemas YAIWES = 840 registros.
- 20 métodos Muse/Glimmer/Meta = 400 registros.
- Total = 102 métodos / 2.040 registros.

## COGNITIVE CONTROL PLANE
1. Source of Truth — autoridad, provenance, freshness, revision.
2. Context Composer — contexto único, pequeño y priorizado.
3. Consistency Engine — contradicción, UNKNOWN, reconciliación.
4. Agent Router — método, agente, LLM, tool, strategy y paralelismo.
5. Policy Guard — capabilities, approvals, sandbox, idempotency y schema.

## FLUJO
INPUT → Source of Truth → Agent Router → compact retrieval → Context Composer → Consistency Engine → YAIWES Kernel → proposed action → Policy Guard → MCP/API/Tool/Sandbox → evidence → StateFold → Critic/Verifier/Judge/Sheriff → PASS/RETRY/RECONCILE.

## ESTRUCTURA
```text
dataset Yaiwes/
├── README-AUTORITATIVO-V1.md
├── PLAN-MAESTRO-INTEGRADO-V2.md
├── CRAZY-WALL-DATASET-YAIWES-V2.json
├── manifest.yaml
├── registry.json
├── constitution/
├── schemas/
├── reasoning/            # M01–M40
├── yaiwes/               # Y01–Y42
├── meta_runtime/         # META01–META20
├── cognitive_control/    # C01–C05
├── router/
├── filters/
├── adapters/
├── sources/
└── tests/
```

## CONTRATO DE CADA MÉTODO
```text
method.yaml
debugging.jsonl        # 10
causal_patterns.jsonl  # 5
similar_errors.jsonl   # 3
counterexamples.jsonl  # 2
```

## MULTI-CHAT ANTI-COLISIÓN
READ CRAZY WALL FRESH → elegir nodo READY → CLAIM → claim_id/owner/lease/base_revision → trabajar sólo node.scope → validar revision → test → evidencia → PASS/FAIL → release.

Reglas: un owner por nodo; no compartir write_scope en paralelo; conflicto de revision = STALE + RECONCILE; Crazy Wall es autoridad; PASS requiere evidencia; ningún chat puede escribir fuera de `dataset Yaiwes/`.

## FASES
F0 Ingesta/hash. F1 Registry/aliases. F2 Schemas. F3 C01–C05. F4 2.040 registros. F5 Router/retriever/filters/context. F6 adapters externos. F7 integración kernel/policy/source-of-truth. F8 tests/concurrencia/Sheriff. F9 cierre/readme/manifest/métricas.

## ESTIMACIÓN DE ARCHIVOS
- 102 métodos × 5 = 510 archivos.
- Cognitive Control Plane = 20–30.
- Router/filtros/adapters/schemas/tests/sources/control = 45–70.
- Documentos de control = 5–8.
- Total V1 aproximado = **575–610 archivos**.

## CIERRE
102 métodos registrados; 2.040 registros válidos; schemas PASS; trazabilidad PASS; C01–C05 PASS; anti-colisión PASS; Sheriff PASS; README/Plan/Crazy Wall sincronizados.
