# Dos sistemas que conviven con propósitos distintos

Estado de este documento: **PROPUESTA** de arquitectura (fecha 2026-10-25), pendiente de aprobación de Antonio. Lo que existe hoy se marca como **EXISTENTE**; lo que falta, como **PROPUESTO**.

## 1. Los dos sistemas

UI YAIWES **no es un sistema de memoria ni un agente**: es el sistema operativo de la interfaz del chat, con triggers (disparadores por evento que solo cambian la pantalla). La memoria, el estado y la auditoría viven solo en el Sistema 1. Detalle: README de https://github.com/maxbry123-commits/ui-yaiwes

| | Sistema 2: control del chat | Sistema 1: memoria de los agentes |
|---|---|---|
| Nombre | **UI YAIWES** (sistema operativo de interfaz con triggers) | **Sistema de memoria y almacenamiento** |
| Qué guarda | Solo preferencias y caché de interfaz en el navegador; muestra lo que el Sistema 1 le informa. No guarda la verdad | Estado (planilla / handoff), conocimiento con evidencia, almacenamiento HF, auditoría, recursos, gobierno de agentes |
| Dónde vive | Repo `maxbry123-commits/ui-yaiwes` (https://github.com/maxbry123-commits/ui-yaiwes). Servida en `/yaiwes` desde `chat/frontend/yaiwes/` | `chat-router/memoria/` de este repo |
| Quién la controla | La interfaz pide y muestra, sin lógica propia; no decide ni escribe memoria | El software del sistema (los agentes no escriben libremente) |

- **EXISTENTE:** UI YAIWES con 39 ventanas, host y action bus (fábrica F0–F3); puente `puente-yaiwes.js` hacia el Harness. En memoria de agentes: `chat/backend/mvp/{memoria.py,hf_store.py,trabajos.py}` cableado, y `memoria-yaiwes/` (SQLite, grafo, adaptadores) sin cablear del todo.
- **PROPUESTO:** el kernel que une ambas por acciones y eventos (no existe todavía).

## 2. Reglas de convivencia

1. **Ids compartidos:** proyecto, sesión y tarea son los mismos ids en las dos memorias.
2. **Comunicación solo por eventos.** Chat -> agentes: ancla, aprobación. Agentes -> chat: tarea terminada, conflicto.
3. **Acceso mínimo.** Los agentes no leen la conversación completa, solo lo anclado o autorizado. El chat pide solo el contexto que necesita mostrar.
4. **Ninguna escribe directamente en la otra.**
5. **En el navegador solo preferencias de interfaz** (localStorage); nunca la verdad.
6. Las ventanas no llevan tokens: GitHub, Hugging Face, Drive y base de datos los abre el kernel (hoy `connectors.js` responde `KERNEL_ONLY`).

```
SISTEMA 2 (UI YAIWES)  --acciones/anclas-->  SISTEMA 1 (memoria de los agentes)
 ventanas, slots, action bus  <--eventos run.*/memory.*--  estado, memoria, almacenamiento,
 solo preferencias en el navegador                          auditoría, recursos, gobierno
```

## 3. Servicios de la memoria de agentes (PROPUESTO)

Siete servicios; la base existente en el repo es orientativa.

| # | Servicio | Contenido | Base existente |
|---|---|---|---|
| S1 | Estado | Planilla única (Profile/Index/Handoff), STATE DELTA como único canal de escritura, journal, transacciones, versiones | `trabajos.py`, memoria_yaiwes |
| S2 | Memoria | Tipos RAW/EVENT/OBSERVATION/FACT/DECISION/EXPERIENCE, scope obligatorio (tenant/agente/proyecto/sesión), anclas en servidor | `memoria.py`, `plugins/memoria` |
| S3 | Recuperación | Niveles 0–5, FTS5 + BM25S + vector + grafo, Context Pack con presupuesto | `context_composer.py`, `source_of_truth.py` |
| S4 | Almacenamiento | HOT / WARM (SQLite) / COLD (bucket HF), registries, backup con sha256 | `hf_store.py`, `plugins/hf_storage`, motores |
| S5 | Auditor | Duplicados, conflictos, huérfanos, evidencia/procedencia | memoria_yaiwes |
| S6 | Recursos | Resource Brain, providers intercambiables con manifest y canary | `ficha.json` de plugins |
| S7 | Gobierno de agentes | Máquina de estados + DAG, event bus, watchdog, locks, Sheriff/Centinela/Guardián | `control.py`, `sala_turno.py` |

Herramientas de agente previstas (PROPUESTO): `memory_profile`, `memory_index`, `memory_anchor`, `memory_read`, `memory_search`, `memory_handoff`, `memory_context`, `memory_audit`, `resource_status`. Escritura solo por el software (STATE DELTA).

## 4. Mapa de los 11 módulos de YAIWES (PROPUESTO)

Los 11 módulos salen de `T2-R1-WINDOW-CAPABILITY-MAP` en ui-yaiwes (EXISTENTE). El enlace a servicios y eventos es la propuesta.

| Módulo YAIWES (vista) | Servicio de memoria de agentes | Acciones / eventos |
|---|---|---|
| M_AGENT_CHAT_SHELL (PANEL-01, GBOT-01) | S7 + Router | `send_message`, `cancel_run` -> `run.started/delta/completed/failed/cancelled` |
| M_KNOWLEDGE_MEMORY_CONTEXT (FOTO-01/07/10) | S2 + S3 | `memory.context`, `memory.search`, `memory.anchor.set` -> `memory.updated` |
| M_GIT_VERSION_TIMELINE (FOTO-03/12) | S1 (journal/versiones) | `state.history`, `state.rollback` (con autorización) |
| M_STORAGE (FOTO-09) | S4 | `storage.list`, `storage.pull` -> `storage.progress` |
| M_EVIDENCE_AUDIT (RUN-03, FOTO-14) | S5 | `audit.run`, `audit.resolve` -> `audit.conflict` |
| M_ASSETS_SKILLS_MODELS (FOTO-04/05/11) | S4 registries + S6 | `resource.status`, `dataset.get`, `adapter.get` |
| M_RUNTIME_ORCHESTRATION (RUN-01/02/04/05/07/08) | S7 | `plan.approve`, `task.run`, `task.cancel` -> `task.*`, `watchdog.alert` |
| M_TERMINAL_SANDBOX (RUN-06, FOTO-02) | S7 sandbox runner | `sandbox.exec` (solo con permiso temporal) |
| M_WORKSPACE_FILES_BLOCKS (WALL-01..16) | S1 planilla + S2 | `sheet.get`, `sheet.delta` |
| M_LAYERS_COMPOSITION (FOTO-08) | S2 tipos + S4 niveles | `memory.layers` |
| M_PERSONALITY_SETTINGS (FOTO-13) | S2 perfil + S7 políticas | `profile.get/set` (escritura vía STATE DELTA) |

## 5. Fallos conocidos de UI YAIWES (EXISTENTES, a corregir en ui-yaiwes cuando se autorice)

- `puente-yaiwes.js` devuelve `{ok:true}` a toda acción distinta de `send_message` sin hacer nada; contradice `failClosed`.
- `ABS.js` usa `postMessage(..., '*')`, prohibido por el contrato de runtime-orchestration.

Referencia de UI YAIWES (sistema operativo de interfaz con triggers): README de https://github.com/maxbry123-commits/ui-yaiwes
