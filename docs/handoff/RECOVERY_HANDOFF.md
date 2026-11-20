# Handoff — Router Recovery (`router_recovery/`)

Actualizado: 2026-11-09. Rama: `ccr-f01c3de9-bmry0s`.

## 0. Registro de actividad
- 2026-11-09 — Creado `router_recovery/` (runner determinista sin LLM, validación Pydantic, ledger append-only, STATE atómico). 14 pruebas pasan. Kill -9 en N2 verificado: N1 no se re-ejecuta.
- 2026-11-09 — Input block registrado: `router_recovery/input_block.yaml` sha256 `bc8198a3be7ff61cdaee12397ddc3011cfb32f5ac96cefe0429f6b75404bc67c`. DAG `router_recovery/dag_schema.yaml` sha256 `88cc3c6540fa2f90af9d7bcb2c5ff390fcc7ac184db98a2145b7af66ceeeb102`.

## 1. Estado
| Componente | Estado |
|---|---|
| Validación DAG (ciclo, dep inexistente, duplicado, >200 LOC, acceptance vacío) | Hecho, probado |
| Orden topológico determinista (Kahn + cola ordenada) | Hecho, probado |
| Ledger append-only con checksum, descarte de líneas parciales | Hecho, probado |
| STATE.json atómico y rebuild desde ledger | Hecho, probado |
| Resume tras kill -9 (no repite nodos completados) | Hecho, probado (prueba real con SIGKILL y reproducción manual) |
| Handler `dispatch_implementer` | **STUB** (🚩). Marca PASS sin trabajo real. |

## 2. Cambios respecto a la spec del owner (🚩 para revisión)
1. `resume` en la spec marcaba como completo el nodo en vuelo sin ejecutarlo. Corregido: se re-ejecuta.
2. El runner de la spec usaba imports relativos y no corría como script. Ejecutar con `python -m router_recovery.runner`.
3. El bloque `validation` de `dag_schema.yaml` es documental; las reglas se aplican en código.
4. Ubicación de checkpoints: la spec dice `checkpoints/`, el CLI usa `.checkpoints/` (igual que N1).
5. `Claude notas.md` existe en `main` y en la rama restaurada, no en esta rama. El registro está aquí.

## 3. Pausado (por decisión del owner)
anchor, watchdog, ocr, handoff, validate_memory, hybrid_search, memory_auditor, context_fabric, resource_registry, state_delta.

## 4. Cómo verificar
```bash
python3 -m py_compile router_recovery/*.py router_recovery/tests/*.py
python3 -m pytest router_recovery/tests -q
python3 -m router_recovery.runner --dag router_recovery/dag_schema.yaml --store .checkpoints/
```
