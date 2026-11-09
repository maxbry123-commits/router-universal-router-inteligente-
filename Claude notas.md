# Claude notas.md — Pizarra de trabajo (Crazy Wall)

Estado: 2026-11-09 · Fuente de tareas: `Claude.md` · Verbatim: `kernel/INPUT_BLOCK_YAIWES_CABLEADO.md`

## Reparto de trabajo (para que no se pisen)

| Router | Responsable | Carpetas que toca |
|---|---|---|
| Router 1 | Claude Code (chat actual) | `ROUTER MVP v1/` (cómputo, almacenamiento, memoria, MCP, conexiones) y `llm system HF/` (control de LLM) |
| Router 2 | Claude Code (chat nuevo) | `HUGGUEFACE SPACE/` (código de los Spaces que no es comunicación) y el borrado asistido en Hugging Face |
| Compartido, solo lectura para los dos | — | `SATÉLITE CENTRAL CONECCION` (cableado y registro en `connections/`), `_quarantine/`, `Claude.md`, esta notas |

Regla: un Claude solo escribe en su carpeta. Si necesita tocar la del otro, lo anota aquí con 🚩 y espera.

## Estado por tarea

| Tarea | Estado | Evidencia |
|---|---|---|
| Lote 35 y pendientes heredados | ✅ | Ver `Claude.md` §6 |
| Plan Hugging Face para Router 2 | 🟡 borrador | `handoff/HF_PLAN_ROUTER2.md` (auditoría de 4 pasadas pendiente) |
| Auditoría forense de los Spaces | ⬜ | Pendiente |
| Quarantine `_quarantine/` con README | ⬜ | Pendiente de aprobación del owner para cada archivo |

## Flags 🚩

- 🚩 Riesgo de secretos en `riu-router/proxy.py` y `riu-router/swecode_provider.json`. Escanear antes de copiar.
- 🚩 `proxy.py` es control de LLM. Debe ir a `llm system HF`, no a cómputo.
- 🚩 `scaler.py` es autoarranque. Se retiró del router MVP; hay que decidir si sale de los Spaces de modelos.
- 🚩 Duplicados: `manager.py`, `scaler.py`, `fetch_models.py` en `swe-code-s1/s2/s3`. Se fusionan en una sola copia.

## Preguntas para el owner (al final del loop)

1. ¿Confirmas que `_quarantine/` es la raíz de cuarentena? Ya existe en `main`.
2. ¿Autorizas escanear el contenido de los Spaces (solo lectura) para buscar secretos?
3. ¿Cuándo se autoriza el borrado en Hugging Face (lo ejecuta MiniMax)?

## Bitácora

- 2026-11-09 — Creado `Claude.md` con la checklist del input block verbatim (secciones 2 a 6) y las tareas heredadas.
- 2026-11-09 — Creado `Claude notas.md` (esta pizarra) y el reparto de trabajo entre Router 1 y Router 2.
- 2026-11-09 — Plan de Hugging Face como borrador, a la espera de la auditoría de 4 pasadas.

## Resolución de flags (2026-11-09)

- 🚩1 RESUELTO. `riu-router/proxy.py` no lee ningún banco de claves. Solo reenvía a los puertos internos. Las claves llegan por variables de entorno del Space (`GITHUB_TOKEN`, `RIU_API_KEY`, `WEB_ACCOUNTS`, `WEB_PASS`, `PUENTE_TOKEN`). `swecode_provider.json` no contiene claves (`apiKey: "local"`). Hallazgo: `riu-router/boot.sh` clona la rama `main` (no la de trabajo) con sparse-checkout que excluye `chat-router/agentes/*`, `chat-router/chatbot/`, `chat-router/memoria/`, `chat-router/otros/`, `chat-router/workflow-loop-code-yaiwes/`. Va a Router 2 como tarea.
- 🚩2 Pendiente de Router 2: `scaler.py` (autoarranque) y `door.py`/`fleet.py`/`mini.py` sin dueño claro.
- 🚩3 Pendiente de Router 2: duplicados `manager.py`/`scaler.py`/`fetch_models.py` en s1/s2/s3.

## Router 2: prompt y handoff

- Handoff: `handoff/HF_PLAN_ROUTER2.md` (solo lectura para Router 2 salvo la sección de estado).
- Única bitácora que edita Router 2: esta `Claude notas.md`.
- Router 2 escribe solo en `HUGGUEFACE SPACE/` y en esta notas.
