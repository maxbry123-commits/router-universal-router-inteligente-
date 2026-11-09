# C1 — Mapa de cableado (solo lectura)

Fecha: 2026-11-09 · Fuentes leídas: `chat-router/MAPA.md`, `chat-router/cableado.manifest.json`. No se modificó nada.

## Cadena

| Eslabón | Ubicación real | Conexión | Estado |
|---|---|---|---|
| 1. Frontend (chat YAIWES) | `chat-router/chat/`, `chat-router/chatbot/`, `chat-router/plugins/chat-router/frontend-yaiwes` | UI → backend del chat | Por verificar en vivo |
| 2. Backend del chat | `chat-router/chat/backend/` | backend → Harness | Por verificar en vivo |
| 3. Harness DeepSeek | `chat-router/chat/backend/deepseek_harness` (enlace `chat-router/harness`) | Harness → plugins | Enlace simbólico declarado en `cableado.manifest.json` |
| 4. Plugins | `chat-router/plugins/deepseek_harness` → `../chat/backend/deepseek_harness`; `plugins/router_api_cliente.py` | Plugins → agentes, memoria y router | Enlaces declarados |
| 5. Agentes | `chat-router/agentes/` (destino de `plugins/agentes`, manifest: `agentes-yaiwes`) | Agentes → Harness | Migración de la Fase 2 pendiente |
| 6. Memoria y almacenamiento | `chat-router/memoria/` (manifest: `memoria-yaiwes`, `hf_datasets`) | Harness → memoria | Por verificar en vivo |
| 7. Router de cómputo | `router-mvp/{mvp,router,fichas}`, `ROUTER MVP v1/` | Harness → Router → modelos | Por verificar en vivo |

## Hallazgos

- `chat-router/MAPA.md` declara que la Fase 1 está hecha y que nada se ha movido. Las Fases 2 a 6 están pendientes.
- En `cableado.manifest.json`, `plugins/hf_compute`, `hf_storage` y `lifeguard` no tienen enlace (`enlace: false`), así que no hay cableado declarado para cómputo ni almacenamiento.
- El router de cómputo tiene dos copias: `router-mvp/` en `main` y `ROUTER MVP v1/`. Esto ya lo reporta `Claude.md` (retiro del original pendiente de aprobación).
- Los enlaces simbólicos (`chat-router/harness`) dependen de cómo los resuelva el checkout. No se han verificado en un entorno de ejecución.

## Flags

- 🚩 C1-1: verificar en vivo los eslabones 1, 2, 6 y 7. Requiere red y llaves.
- 🚩 C1-2: aprobar la migración de la Fase 2 (`plugins/agentes` → `chat-router/agentes/`) antes de mover nada.

## Handoff

```json
{"router":"CLAUDE CODE 4","tarea":"C1","estado":"cerrado","evidencia":"chat-router/MAPA.md; chat-router/cableado.manifest.json","subagente":"ninguno","flags":["C1-1","C1-2"]}
```
