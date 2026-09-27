---
id: fabrica-01
estado: activa
repo: frontend
rama_base: main
carpeta_trabajo: "fabrica de UI INTERFACE fromtend/motores"
---
# TAREA fabrica-01 — 6 motores base de la Fábrica UI (documento 18 del Director)

## Objetivo
Crear los 6 motores deterministas base que pidió el Director para la Fábrica UI: Capability, Canvas, Layout, Action/Flow, Sandbox y QA.
La IA solo decide; los motores hacen el trabajo real.

## Lee primero (en el repo router-universal-router-inteligente-, rama main)
1. `chat router/00-INSTRUCCIONES/INPUT-BLOCK-VERBATIM-CHAT-Y-PANEL-PARTE-4.md` — documento 18 (15 motores, contrato común `Engine`, `ENGINE_REGISTRY`, "primera implementación: 6 motores base") y documentos 14/15/16 (Capability Engine, registro obligatorio, cobertura, recetas).
2. En este repo (frontend): `fabrica de UI INTERFACE fromtend/` (F1/F2, CABLEADO, action-bus, catálogos). Reusa lo que exista; no dupliques.

## Entregables (solo dentro de `fabrica de UI INTERFACE fromtend/motores/`)
1. `engine.py` — clase base `Engine` (id, capabilities, `can_handle`, `execute`, `verify`, async) + `ENGINE_REGISTRY`.
2. `capability_engine.py` — busca componentes por capacidad leyendo un registro JSON (`registry/component_registry.json`); cobertura obligatoria (si una capacidad tiene 0 candidatos → error explícito); registra descartes.
3. `canvas_engine.py` — operaciones sobre un árbol de página en JSON: createPage, addSection, addComponent, moveComponent, setProperty, export JSON.
4. `layout_engine.py` — grid/flex/gap/snap/bounds/breakpoints: entrada viewport + elementos → posiciones y tamaños. Sin IA.
5. `action_engine.py` — action_id → handler/workflow (action-bus); compila flujo a DAG `{"steps": [...]}`. Ningún botón sin handler.
6. `sandbox_engine.py` — selector de runtime (JS pequeño → QuickJS, Python → subprocess aislado con timeout, React → marca "sandpack") con interfaz única; implementar de verdad solo el de Python.
7. `qa_engine.py` — recibe resultado y devuelve `{"status": PASS|FAIL, "issues": [...]}` con reglas deterministas (sin navegador todavía).
8. `registry/component_registry.json` — ejemplo mínimo con 10 componentes reales del banco `UI YAIWES/componentes open soure UI YAIWES/` (id, provides, requires, compatible_with, runtime).
9. `tests/test_motores.py` — pytest para los 6 motores (sin red). Deben pasar.
10. `README.md` — 20 líneas: qué hace cada motor y cómo se prueba.

## Reglas
- Máximo 500 líneas por archivo. Solo librería estándar + pytest.
- No toques nada fuera de `fabrica de UI INTERFACE fromtend/motores/`.
- No es el T-3000 (ese se discute aparte con el Director).
- Al terminar: `python -m pytest "fabrica de UI INTERFACE fromtend/motores/tests" -q` debe pasar.
