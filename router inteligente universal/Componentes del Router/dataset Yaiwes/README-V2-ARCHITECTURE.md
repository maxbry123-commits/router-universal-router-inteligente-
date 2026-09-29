# YAIWES DATASET — ARQUITECTURA V2 Y CONTRATO MULTI-CHAT

## INPUT BLOCK LITERAL

Ok integra al plan pon todo 1 a 1 imput block en el readme y en el Craxy wall me haces una lista de nodos tipo shema de todo lo que vas a construir
Lo colocas de tal manera que varios chat de sol gpt ayuden y no se pisen

Cuantos archivos vas a crear ? Para hacerlo

## OBJETIVO
Construir la capa externa `dataset Yaiwes/` con MYTHOS/FABLES, YAIWES, Muse/Glimmer/Meta, cinco módulos de control cognitivo, router, filtros, adaptadores, schemas, pruebas y Crazy Wall autoritativo, sin entrenar el modelo base.

## COBERTURA
- 40 métodos MYTHOS/FABLES = 800 registros.
- 42 paquetes YAIWES = 840 registros.
- 20 métodos Muse/Glimmer/Meta = 400 registros.
- Total = 102 métodos = 2.040 registros.

Cada método tendrá: 10 debugging, 5 patrones causales, 3 errores similares/conocidos, 2 contraejemplos.

## CINCO MÓDULOS DE CONTROL COGNITIVO
1. Source of Truth — autoridad, provenance, freshness y precedencia.
2. Context Composer — presupuesto, selección y ensamblado de contexto.
3. Consistency Engine — contradicción, conflicto, UNKNOWN y reconciliación.
4. Agent Router — método + agente + modelo + tool + paralelismo.
5. Policy Guard — capabilities, approvals, sandbox y validación pre-ejecución.

## ARQUITECTURA
```text
INPUT
→ SOURCE OF TRUTH
→ CONTEXT COMPOSER
→ CONSISTENCY ENGINE
→ AGENT ROUTER
   ├─ MYTHOS DATASET
   ├─ YAIWES DATASET
   └─ META RUNTIME DATASET
→ POLICY GUARD
→ YAIWES KERNEL
→ MCP/API/SANDBOX/TOOLS
→ OBSERVATION/EVIDENCE
→ SHERIFF/VERIFIER/CRITIC/JUDGE
→ STATE UPDATE
↺
```

## CONTRATO MULTI-CHAT SOL GPT
- Cada nodo tiene `node_id` único.
- Claim obligatorio: `owner`, `claim_id`, `lease_expires_at`, `revision`, `base_hash`.
- Ningún chat toca nodo `CLAIMED/IN_PROGRESS` de otro owner.
- `write_scope` limita paths permitidos por nodo.
- Antes de escribir: leer Crazy Wall fresh y validar revisión/hash.
- Si el hash cambió: `CONFLICTED`, no sobrescribir.
- Integración sólo cuando dependencias están `PASS`.
- PASS requiere tests y evidencia.
- UNKNOWN nunca se convierte automáticamente en PASS.

## ESTRUCTURA OBJETIVO
```text
dataset Yaiwes/
├── README.md
├── README-V2-ARCHITECTURE.md
├── PLAN-MAESTRO-DATASET-YAIWES-V1.md
├── CRAZY-WALL-PLAN-DATASET-YAIWES-V2.json
├── manifest.yaml
├── registry.json
├── constitution/
├── schemas/
├── reasoning/
├── yaiwes/
├── meta_runtime/
├── source_of_truth/
├── context_composer/
├── consistency_engine/
├── router/
├── policy_guard/
├── filters/
├── adapters/
├── sources/
└── tests/
```

## CRITERIO DE CIERRE
No cerrar hasta que registry, 102 métodos, 2.040 registros, schemas, router, Context Composer, Consistency Engine, Policy Guard, trazabilidad, tests y Sheriff estén PASS y sincronizados con Crazy Wall.
