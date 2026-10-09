# T08 — 6 motores base de la Fábrica UI

Implementación determinista de los seis motores base definidos para la Fábrica UI. Cada motor tiene una responsabilidad separada y se registra mediante `ENGINE_REGISTRY`.

## Motores

- **Capability** — resuelve capacidades requeridas, candidatos compatibles, conflictos y componentes no registrados.
- **Canvas** — crea y modifica páginas, secciones y componentes como un modelo JSON determinista.
- **Layout** — calcula grid/flex, gaps, snap, límites y breakpoints sin depender de una LLM.
- **Action/Flow** — conecta `action_id` con handlers y compila flujos visuales a un DAG ejecutable; detecta botones muertos.
- **Sandbox** — ejecuta código en subprocesos aislados con timeout y límite de salida.
- **QA** — valida de forma determinista acciones, solapes, tamaño táctil mínimo y breakpoints.

## Flujo

```text
INPUT → Capability → Canvas → Layout → Action/Flow → Sandbox → QA → PASS | FAIL
```

## Registro

Capacidades base esperadas:

```text
ui.capability
ui.canvas
ui.layout
ui.actions
code.sandbox
qa.visual
```

Las tareas independientes pueden ejecutarse en paralelo mediante `asyncio.gather(...)`.

## Aceptación

```bash
python -m pytest "chat router/Workflow Loop code Yaiwes/12-FABRICA-MOTORES" -q
```

El cierre requiere tests reales y los checks objetivos del contrato T08; un `pytest` verde por sí solo no basta.
