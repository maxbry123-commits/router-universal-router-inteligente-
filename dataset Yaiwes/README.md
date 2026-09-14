# dataset Yaiwes

## Propósito

Capa externa de conocimiento operacional y de razonamiento para YAIWES. No entrena ni modifica los pesos del modelo. Alimenta al Router Universal Inteligente con métodos, patrones, errores, contraejemplos, contratos y contexto selectivo.

## Arquitectura V1

```text
INPUT
  ↓
CLASSIFIER
  ↓
ROUTER
  ↓
FILTERS + SCORER
  ↓
RETRIEVAL SELECTIVO
  ↓
CONTEXT PACK
  ↓
YAIWES KERNEL
  ↓
CRITIC / VERIFIER / JUDGE / SHERIFF
```

## Fuentes funcionales

- MYTHOS/FABLES: 40 métodos de razonamiento.
- YAIWES: 42 sistemas del kernel/project OS/learning/simulation/assurance.
- Muse/Glimmer/Meta: 20 métodos operacionales de runtime, control, tools y coordinación.

Total inicial: 102 métodos.

## Regla por método

```text
10 debugging
5 patrones causales
3 errores similares/conocidos
2 contraejemplos
= 20 registros
```

Total V1 previsto: 2.040 registros.

## Separación de capas

- MYTHOS/FABLES = razonamiento.
- YAIWES = kernel, planificación, decisión, aprendizaje y Project OS.
- Muse/Glimmer/Meta = runtime operacional, herramientas, recovery y multiagente.
- Router = selección de método y contexto.
- Dataset = conocimiento externo.
- Sheriff = aceptación basada en evidencia.

## Directorios previstos

```text
dataset Yaiwes/
├── README.md
├── PLAN-MAESTRO-DATASET-YAIWES-V1.md
├── CRAZY-WALL-PLAN-DATASET-YAIWES-V1.json
├── manifest.yaml
├── registry.json
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

## Reglas operativas

1. El LLM no es la fuente autoritativa del estado.
2. Todo side effect debe ser idempotente e identificable.
3. Estado compartido debe llevar revision/cursor.
4. Un gap congela ejecución hasta reconciliar.
5. UNKNOWN no se convierte automáticamente en PASS o FAIL.
6. PASS requiere evidencia verificable.
7. Acciones peligrosas deben pasar por sandbox/policy.
8. Las observaciones reales vuelven al loop.
9. Razonamiento y control son capas diferentes.
10. README, registry y Crazy Wall deben permanecer sincronizados.

## Estado actual

`BOOTSTRAP_CREATED`

Esta versión es el esqueleto inicial. Cuando se incorporen los documentos fuente, se realizará auditoría, deduplicación semántica, registro canónico de métodos y actualización de esta arquitectura con trazabilidad y hashes.
