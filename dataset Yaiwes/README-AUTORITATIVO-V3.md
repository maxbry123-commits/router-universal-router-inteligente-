# YAIWES — ARQUITECTURA AUTORITATIVA COMPACTA V3

## MODO
`FAIL_CLOSED_STRICT_3_STEPS`

## SCOPE AUTORIZADO ACTUAL
La instrucción más reciente amplía la arquitectura física a DOS raíces del mismo repo/branch:

```text
router-universal-router-inteligente-/main/
├── dataset Yaiwes/                 # SOLO contenido: jsonl + schemas + registry + docs/bitácora
└── Yaiwes Cognitive Control Plane/ # SOLO mecanismo: 5 módulos de código + tests
```

No crear ni modificar nada fuera de esas dos raíces para este proyecto.

## INPUT BLOCK LITERAL — ACTUALIZACIÓN APROBADA

```text
# INSTRUCCIÓN — dataset Yaiwes + Cognitive Control Plane
repo: router-universal-router-inteligente-
modo: FAIL_CLOSED_STRICT_3_STEPS

OBJETIVO
Construir la versión COMPACTA (no la de 600 archivos): ~30-35 archivos,
~1.100 registros, tiers A/B/C por criticidad, cobertura completa de 107+
métodos (Mythos/YAIWES/Meta).

ESTRUCTURA FÍSICA (separación real, no solo lógica)
router-universal-router-inteligente-/
├── dataset Yaiwes/          ← SOLO contenido (jsonl + schemas + registry)
└── Yaiwes Cognitive Control Plane/   ← SOLO mecanismo (5 módulos, código)

PASO 0 — ANTES DE ESCRIBIR CÓDIGO
Detente y reporta en el Crazy Wall si "Context Composer" y "Input Shark"
(este último vive en el repo osquestador-auditor) se van a fusionar en
uno solo o si tienen contratos de entrada/salida distintos y separados.
NO construyas ambos por separado sin esta resolución explícita.

PASO 1 — DATASET (Tier A/B/C)
- Tier A (crítico, 20 registros c/u): GOAL_DECOMPOSITION, DEPENDENCY_GRAPH,
  CONTRADICTION_DETECTION, SIMULATION, REPLANNING, DECISION_ENGINE,
  SHERIFF, ROUTER, SOURCE_OF_TRUTH, CONSISTENCY_ENGINE, POLICY_GUARD, RECOVERY
- Tier B (core, 10 registros c/u): resto de métodos con uso frecuente
- Tier C (soporte, 7 registros c/u): métodos de formato/salida
- Cada registro incluye: id, method_id, method, category, source, commit,
  added_at (provenance obligatoria)
- registry.json como índice maestro — el Router NUNCA lee el .jsonl completo

PASO 2 — COGNITIVE CONTROL PLANE (5 módulos, código real)
- source_of_truth/: jerarquía runtime>test>repo>inferencia_agente>texto_LLM
- context_composer/: budget de tokens + priorización + compresión
- consistency_engine/: detecta conflictos (ej. CI=PASS vs runtime=FAIL) →
  produce STATE=CONFLICTED + acción RECONCILE, nunca lo decide el LLM
- router/: clasificador + scorer + selector paralelo de agente/método/modelo
- policy_guard/: gate determinista pre-ejecución, fail-closed por defecto

PASO 3 — TESTS OBLIGATORIOS
tests/test_router.py, test_data.py, test_control.py, test_integration.py
Ningún módulo se declara PASS sin su test correspondiente.

EVIDENCIA REQUERIDA
path/blob/SHA de cada archivo creado + resultado de test + registro en
Crazy Wall de este repo.
Métele buenos ejemplos a lo de Fables es la parte más importante del proyecto

Inicia monta un wachdog activo de tareas pendientes de chat gpt cada una hora para revisar y ejecutar las tareas pendientes de lo que estás haciendo

Inicia modo Loops y bucle hasta terminar todas las tareas
```

## PASO 0 — RESOLUCIÓN INPUT SHARK vs CONTEXT COMPOSER
Auditoría del árbol `maxbry123-commits/osquestador-auditor/main`: no se encontró un path/artefacto identificable como `Input Shark` con contrato inspeccionable. En FAIL-CLOSED no se inventa su interfaz.

**Resolución explícita V3:**
- `Context Composer` SÍ se construye en este proyecto con contrato propio: `ContextRequest -> ContextPack`.
- `Input Shark` NO se construye ni se copia aquí; se trata como upstream externo pendiente de contrato verificable.
- NO se fusionan por ahora.
- Si luego aparece su contrato, sólo se añade un adapter si sus I/O son compatibles.

## COBERTURA CANÓNICA
- 40 métodos MYTHOS/FABLES.
- 42 métodos/sistemas YAIWES.
- 20 métodos Muse/Glimmer/Meta.
- 5 métodos Cognitive Control.
- Total lógico inicial: **107 métodos**.

## TIERS
- Tier A: 12 métodos × 20 registros = 240.
- Tier B: métodos core restantes × 10.
- Tier C: soporte/formato × 7.
- Objetivo físico aproximado: **~1.100–1.150 registros**, no 2.040.

## ARCHIVOS FÍSICOS COMPACTOS
Los métodos NO se convierten en carpetas/archivos individuales. Se agregan por dominio en JSONL y `registry.json` conserva separación lógica, tier, offsets/índices y conteos.

```text
dataset Yaiwes/
├── README-AUTORITATIVO-V3.md
├── PLAN-MAESTRO-COMPACTO-V3.md
├── CRAZY-WALL-DATASET-YAIWES-V3.json
├── manifest.yaml
├── registry.json
├── data/
│   ├── mythos.jsonl
│   ├── yaiwes.jsonl
│   ├── meta_runtime.jsonl
│   └── cognitive_control.jsonl
├── schemas/
│   ├── case.schema.json
│   ├── method.schema.json
│   ├── context_pack.schema.json
│   └── state.schema.json
├── indexes/methods.json
├── sources/provenance.json
├── filters/rules.yaml
├── adapters/adapters.yaml
└── tests/test_data.py

Yaiwes Cognitive Control Plane/
├── README.md
├── contracts.py
├── source_of_truth.py
├── context_composer.py
├── consistency_engine.py
├── router.py
├── policy_guard.py
└── tests/
    ├── test_router.py
    ├── test_control.py
    └── test_integration.py
```

## ROUTER
`INPUT -> classify -> registry lookup -> score -> selective retrieval -> ContextPack -> kernel`

El Router nunca lee el JSONL completo en contexto; usa `registry.json`/índices y recupera sólo registros relevantes.

## PLUGIN UNIVERSAL
El enchufe universal subido se cablea **AL FINAL**, después de dataset + cinco módulos + tests PASS, para dejar abierta la incorporación de capacidades adicionales antes de congelar contratos.

## MULTI-CHAT / ANTI-COLISIÓN
Cada nodo Crazy Wall tiene `owner`, `claim_id`, `lease_expires_at`, `base_revision`, `write_scope`. Un chat sólo escribe en su `write_scope`; revisión divergente => `STALE_AND_RECONCILE`.
