# 02 — Historial de cableado

## Archivos del historial (verificados en `main`)

| Archivo | Tamaño | sha (blob) | Qué es |
|---|---|---|---|
| `connections/wiring_history.jsonl` | 12.344.585 B | `e29b354765b9` | histórico de cambios de cableado |
| `connections/wiring_changelog.md` | 5.865 B | `7172028dd8e3` | bitácora legible del cableado |
| `connections/bridge_report.json` | 5.741 B | `f6ad057b2dde` | informe central de conexiones |
| `connections/baseline_unresolved.json` | 8.751.014 B | `7dfada1b75f6` | baseline de referencias sin resolver |

## Enlace al sistema principal

El historial se referencia desde:
- [`README.md`](../../README.md), sección "Cableado y estado".
- [`handoff/INDEX.md`](../INDEX.md).
- [`connections/registry.yaml`](../../connections/registry.yaml), que documenta su origen (`ops/make_registry.py`, grafo `j2_graph`).

## Recuperar el cable

Para recuperar el estado de una conexión concreta: buscar su `id` (CON-NNN) en `connections/registry.yaml` y su historial en `connections/wiring_history.jsonl`.

## Verificaciones pendientes

El sha del historial en el Dataset de Hugging Face (`d087146d…88d0`) citado en el documento de cierre no se ha comparado en esta pasada.
