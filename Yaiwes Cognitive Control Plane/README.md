# Yaiwes Cognitive Control Plane

Mecanismo externo determinista para consumir `dataset Yaiwes/` sin entrenar el modelo base.

## Cinco módulos
1. `source_of_truth.py` — arbitra autoridad: runtime > test > repo > agent_inference > llm_text.
2. `context_composer.py` — ensambla `ContextRequest -> ContextPack` con budget, prioridad y deduplicación.
3. `consistency_engine.py` — conflicto => `STATE=CONFLICTED`, `ACTION=RECONCILE`.
4. `router.py` — lee `registry.json`, clasifica y selecciona rutas paralelas; nunca hace full-scan de JSONL.
5. `policy_guard.py` — fail-closed pre-ejecución.

## Input Shark
No se fusiona. No se encontró contrato verificable en el árbol auditado de `osquestador-auditor`. Se mantiene como upstream externo futuro y sólo se conectará mediante adapter si su contrato real es compatible.

## Flujo
`input -> source_of_truth -> router -> selective retrieval -> context_composer -> consistency_engine -> kernel -> proposed_action -> policy_guard -> tool/MCP/API -> evidence`

## Plugin universal
Cableado reservado al último nodo `PLUGIN-999`, después de tests e integración PASS.
