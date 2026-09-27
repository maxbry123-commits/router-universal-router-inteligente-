---
id: chat-01
estado: activa
repo: router-universal-router-inteligente-
rama_base: main
carpeta_trabajo: "chat router/05-AGENTES/gobierno"
---
# TAREA chat-01 — Gobierno del equipo: contratos, Sheriff, Sentinel, Judge, MirrorManager, EngineeringLoop

## Objetivo
Crear el código Python del gobierno del equipo de agentes del chat, tal como lo pidió el Director (documentos 22 y 23).

## Lee primero (obligatorio)
1. `chat router/00-INSTRUCCIONES/INPUT-BLOCK-VERBATIM-PARTE-5-B-DOCS-22-23.md` — contiene el CÓDIGO BASE exacto (Sheriff, Judge, Sentinel, RufloAdapter, EngineeringLoop, MetaTeam, MirrorManager, contratos job/result, Task, State). Úsalo como base; NO inventes otra arquitectura.
2. `chat router/05-AGENTES/AGENTES.yaml` — jerarquía, colmena y grafo.
3. `chat router/01-PLAN/PLAN-DSL-DAG-00-CONTRATO.yaml` — reglas R01–R12.

## Entregables (solo estos archivos, dentro de `chat router/05-AGENTES/gobierno/`)
1. `contratos.py` — dataclasses `Job`, `Result`, `Task` y enum `State` (doc 22 y 23), con `to_dict()`/`from_dict()`.
2. `sheriff.py` — clase `Sheriff.validate(plan) -> (bool, str)` (código del doc 23, sin LLM).
3. `sentinel.py` — clase `Sentinel.inspect(task_state) -> dict` (doc 23) + detección de estancamiento: mismo error ×3 → `REASSIGN`.
4. `judge.py` — clase `Judge.decide(task, evidence, review_a, review_b) -> "PASS"|"REVISE"|"BLOCK"` (doc 23, sin LLM).
5. `mirror_manager.py` — `MirrorManager` con `SYSTEM_MAP` (doc 22) que crea `git worktree` en `../mirrors/<job_id>` con rama `mirror/<job_id>`, lista rutas permitidas, `get_diff()`, `destroy()`, `keep_for_debug()`. Sin red.
6. `engineering_loop.py` — `EngineeringLoop` y `MetaTeam` (doc 22) con los agentes como interfaces abstractas (Protocol) para enchufarlos después al Router.
7. `tests/test_gobierno.py` — pruebas con `pytest` para 1–6 (sin red, con dobles/fakes). Deben pasar.
8. `README.md` — 20 líneas máximo: qué hace cada archivo y cómo se prueba.

## Reglas
- Máximo 500 líneas por archivo. Solo librería estándar + pytest.
- No toques nada fuera de `chat router/05-AGENTES/gobierno/`.
- Nada de claves ni tokens en archivos.
- Al terminar: `python -m pytest "chat router/05-AGENTES/gobierno/tests" -q` debe pasar.

## Cierre (lo verifica el sentinela)
Todos los archivos existen, compilan y las pruebas pasan.
