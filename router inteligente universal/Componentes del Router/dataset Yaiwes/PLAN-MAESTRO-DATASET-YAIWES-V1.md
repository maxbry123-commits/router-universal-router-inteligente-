# YAIWES — PLAN MAESTRO DATASET EXTERNO + ROUTER

## Objetivo
Crear una capa externa compacta para YAIWES dentro del Router Universal Inteligente. No modifica pesos del modelo. Organiza conocimiento de razonamiento, control y operación para retrieval selectivo.

## Regla por método
- 10 casos debugging
- 5 patrones causales
- 3 errores similares/conocidos
- 2 contraejemplos
- Total: 20 registros

## Cobertura inicial

### MYTHOS/FABLES — 40 métodos
M01 INPUT; M02 INTENT_PARSING; M03 PROBLEM_FRAMING; M04 DOMAIN_DETECTION; M05 CONTEXT_BUILDING; M06 CONSTRAINT_EXTRACTION; M07 GOAL_DECOMPOSITION; M08 COMPLEXITY_ESTIMATION; M09 RISK_SCORING; M10 STRATEGY_SELECTION; M11 ARCHITECTURE_DESIGN; M12 PLAN_GENERATION; M13 SUBTASK_BREAKDOWN; M14 DEPENDENCY_GRAPH_BUILD; M15 HYPOTHESIS_GENERATION; M16 ALTERNATIVE_PATH_GENERATION; M17 SEARCH_EXPANSION; M18 REASONING_SWARM; M19 CONTRADICTION_DETECTION; M20 CRITIC_SWARM; M21 SELF_REFLECTION_LOOP; M22 FAILURE_MODE_ANALYSIS; M23 SIMULATION_ENGINE; M24 EDGE_CASE_GENERATION; M25 VALIDATION_LAYER; M26 KNOWLEDGE_RETRIEVAL; M27 INSIGHT_EXTRACTION; M28 MEMORY_WRITE_SHORT; M29 MEMORY_WRITE_LONG; M30 REPLANNER_LOOP; M31 OPTIMIZATION_PASS; M32 DECISION_ENGINE; M33 CONFIDENCE_SCORING; M34 SOLUTION_RANKING; M35 FUSION_ENSEMBLE; M36 SAFETY_CONSISTENCY; M37 FINAL_SYNTHESIS; M38 OUTPUT_GENERATION; M39 POST_OUTPUT_AUDIT; M40 FEEDBACK_LOOP_STORAGE.

Subtotal: 800 registros.

### YAIWES — 42 paquetes
Y01 Kernel recurrente/durable runtime; Y02 State Machine; Y03 Planning R16/R24; Y04 12 Goals Input/Output; Y05 Multi-LLM; Y06 Cognitive Lottery Router; Y07 Contextual Bandit/Thompson Router; Y08 Reasoning Tournament; Y09 Cognitive Beam Search; Y10 Ask Council R16; Y11 Critic Council; Y12 Judge Council; Y13 Multi-Simulation; Y14 Digital Twin/World Model; Y15 Risk Engine; Y16 Memory Plane; Y17 Procedural Memory; Y18 Editable Workflow; Y19 Constitution/Project Manifest; Y20 Deterministic Microflows; Y21 JSON/YAML Schemas; Y22 Document Templates; Y23 Document Ingestion; Y24 Hash/Diff Incremental Update; Y25 Reverse Dependencies; Y26 Recovery State; Y27 Sheriff/Acceptance Gate; Y28 Event Bus/Queue; Y29 Parallel Workers; Y30 Sandbox Execution; Y31 Observability; Y32 Tool Learning; Y33 Tool Gym; Y34 Learning by Demonstration; Y35 Video/Manual Procedure Learning; Y36 Process Mining; Y37 Skill Compiler; Y38 Skill Promotion Ladder; Y39 Skill Registry; Y40 Reinforcement/Imitation Learning; Y41 Continuous Evaluation; Y42 Checkpoint/Replay.

Subtotal: 840 registros.

### Muse/Glimmer/Meta — 20 métodos
META01 EventStore; META02 StateFold; META03 PendingCommandSet; META04 CommandId/Idempotency; META05 Cursor/Revision; META06 Gap Recovery; META07 Turn/Queue Control; META08 Structured Approvals; META09 Subagent Lifecycle; META10 UNKNOWN+Reconciliation; META11 Reason→Action→Observation; META12 Tool Registry; META13 Structured Action Parser; META14 Tool Error Autocorrection; META15 Perception→Action→Verification; META16 Sheriff→MCP→Sandbox; META17 Source Trust; META18 Capability Profile; META19 Shared Multi-Agent Board; META20 Claim+Owner+Lease+Heartbeat.

Subtotal: 400 registros.

## Total V1
102 métodos × 20 = 2.040 registros.

## Estructura
```text
dataset Yaiwes/
├── README.md
├── manifest.yaml
├── registry.json
├── CRAZY-WALL-PLAN-DATASET-YAIWES-V1.json
├── constitution/
├── schemas/
├── reasoning/
├── yaiwes/
├── meta_runtime/
├── router/
├── filters/
├── adapters/
├── sources/
└── tests/
```

Cada método tendrá: `method.yaml`, `debugging.jsonl`, `causal_patterns.jsonl`, `similar_errors.jsonl`, `counterexamples.jsonl`.

## Router
`INPUT → CLASSIFIER → MÉTODO(S) → FILTERS → SCORER → RETRIEVER → CONTEXT PACK → YAIWES KERNEL`.

El pool es de 20 registros por método; el retrieval real será configurable y normalmente mucho menor.

## Fases
F0 Ingesta y hashes de documentos.
F1 Registry canónico y aliases.
F2 Schemas.
F3 Dataset de 20 registros por método.
F4 Router, filtros y context builder.
F5 Adaptadores externos e integración.
F6 Tests, trazabilidad y Sheriff.
F7 README final, manifest, métricas y cierre.

## Criterios de cierre
- Todos los métodos canónicos registrados.
- 20 registros válidos por método.
- Sin duplicados críticos.
- Fuentes y hashes trazables.
- Schemas PASS.
- Router/retrieval PASS.
- Context budget PASS.
- Tests PASS.
- Crazy Wall y README sincronizados.
