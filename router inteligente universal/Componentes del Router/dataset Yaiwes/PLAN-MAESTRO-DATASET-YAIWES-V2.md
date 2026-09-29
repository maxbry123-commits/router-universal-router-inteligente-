# YAIWES — PLAN MAESTRO V2

Este plan integra el Dataset YAIWES, los 40 métodos MYTHOS/FABLES, los 42 paquetes YAIWES, los 20 paquetes META/MUSE/GLIMMER y cinco módulos explícitos de control cognitivo: Source of Truth, Context Composer, Consistency Engine, Agent Router y Policy Guard.

## Restricción autoritativa

Única raíz de escritura autorizada:

```text
maxbry123-commits/router-universal-router-inteligente-/main/dataset Yaiwes/
```

No se permite crear, editar, mover ni borrar archivos fuera de esa raíz.

## Regla de dataset

Por cada método canónico:
- 10 casos debugging
- 5 patrones causales
- 3 errores similares/conocidos
- 2 contraejemplos
- 20 registros totales

## Cobertura V1

- 40 métodos MYTHOS/FABLES = 800 registros.
- 42 paquetes YAIWES = 840 registros.
- 20 paquetes META/MUSE/GLIMMER = 400 registros.
- Total = 102 métodos / 2.040 registros.

## Módulos de control cognitivo

1. Source of Truth: arbitra autoridad, provenance, freshness y prioridad de evidencia.
2. Context Composer: arma contexto compacto, priorizado, deduplicado y con budget.
3. Consistency Engine: detecta contradicciones, UNKNOWN y reconcilia estados.
4. Agent Router: selecciona método, LLM/agente, herramienta, adapter, paralelismo y budget.
5. Policy Guard: valida capabilities, approvals, sandbox, commandId y side effects antes de ejecutar.

## Arquitectura

```text
INPUT
→ SOURCE OF TRUTH
→ CONTEXT COMPOSER
→ CONSISTENCY ENGINE
→ AGENT ROUTER
→ POLICY GUARD
→ YAIWES KERNEL
→ LLM/AGENTS/TOOLS
→ EVIDENCE
↺
```

## Ejecución multi-chat SOL GPT

- Cada chat debe leer Crazy Wall fresh.
- Reclamar sólo un nodo READY sin owner.
- Escribir únicamente en los `scope_paths` del nodo.
- No tocar nodos CLAIMED/IN_PROGRESS de otro owner.
- Mantener `claim_id`, `owner_id`, `lease_until`, `revision` y hashes.
- Sólo pasar a PASS con evidencia y tests.
- Al terminar, releer Crazy Wall antes de reclamar otro nodo.

## Fases

F0 Ingesta de documentos y hashes.
F1 Registry canónico y aliases.
F2 Schemas y contratos.
F3 Generación de 2.040 registros.
F4 Cognitive Control Plane.
F5 Router, filtros y adapters externos.
F6 Integración con kernel YAIWES.
F7 Verificación, Sheriff y cierre.
