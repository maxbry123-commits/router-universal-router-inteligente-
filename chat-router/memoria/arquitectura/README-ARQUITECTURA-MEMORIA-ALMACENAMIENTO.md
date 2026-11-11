# README ARQUITECTURA — 1. SISTEMA DE MEMORIA Y ALMACENAMIENTO

Raíz (destino): `chat-router/memoria/` · Hermano: `chat-router/chatbot/arquitectura/README-ARQUITECTURA-CHATBOT.md`
Estado: **arquitectura documentada, nada nuevo cableado** (modo recepción). Fecha: 2026-10-25.

## 1. Objetivo
Convertir la memoria en **software de control de contexto** que funciona (a) como **tool** que cualquier agente llama y (b) como **sistema operativo de memoria** por eventos. **LLM ≤ 5 %** (meta de diseño, aún no medida).
Regla: *la memoria no piensa constantemente; sabe qué cambió, dónde está, qué tarea está activa y qué entregar.*

## 2. Qué se conserva intacto (ya cableado y funcional — NO se toca)
`chat/backend/mvp/memoria.py` · `hf_store.py` · `trabajos.py` · herramienta `almacen` · `plugins/hf_storage` · `plugins/memoria` (enlace → `chat-router/memoria/memoria-yaiwes`) · `router/integration/chat_mvp/memoria_loader.py` · frontend `chat-ancla.js` (IndexedDB), `proyecto.js`, `handoff-editor.js`, `contexto.js`, `pendientes-panel.js`, `objetivos-ancla.js`, `anclaje-*.js`.
Todo lo nuevo entra **por adaptadores y contratos**, con la guardia `chat/auditoria/guardia_cableado.py` como red.

## 3. Mapa de carpetas de esta raíz
```
chat-router/memoria/
├── arquitectura/            ← este README + INPUT-BLOCK-ANTONIO.md (texto literal)
├── memoria-yaiwes/          motor existente (SQLite, grafo, adaptadores)   [enlace plugins/memoria]
├── hf_datasets/             almacenamiento HF datasets                      [enlace plugins/hf_datasets]
├── componentes/             Graphify, Graphiti, Memanto, Prometheus, PyGithub, Phoenix,
│                            Qdrant, qdrant-client, Chroma, Redis, redis-py, Postgres, asyncpg, aiomysql,
│                            Sentence-Transformers, llama_index
└── (aquí irá el código de Sol: memory_os/ — pendiente de subir)
Herramientas SDK (descargadas): chat-router/agentes/frameworks/{openai-agents-python, strands-agents-sdk-python, haystack, pydantic-ai}
Capa de conexión MCP: router-componentes/mcp-python-sdk
```

## 4. Arquitectura (entrada de Antonio + mejoras integradas)
```
USUARIO → CHAT/ROOM → ROUTER → MEMORY CONTROLLER (un solo servicio)
   ├─ PLANILLA (estado)   ├─ ÍNDICE (dónde)   ├─ HANDOFF (qué falta)
   ├─ ANCHOR ENGINE (filtro obligatorio en servidor)
   └─ EVENT BUS (único) → consumidores: índice, handoff, ancla, grafo, Memanto-lotes
→ CONTEXT PACK pequeño → AGENTE+LLM → TOOL REQUEST → MEMORY GATE (permisos) → resultado → EVENT BUS → HANDOFF
Microkernel: OFF por defecto → REVIEW → ON → VERIFY → OFF (solo con alerta validada)
```
Dos edificios por HTTP: Edificio 1 = chat/router/`memoria.py`/controlador/anclas/estado; Edificio 2 = Plugin Host/`plugins/memoria`/tools/Graphify/Graphiti/Memanto.

## 5. Integración 1 a 1 (propuesta de Antonio → mejora aplicada → con qué → estado)

Estados: ✅ existe y cableado · 🟡 existe sin cablear / parcial · ⬜ por construir · ⛔ riesgo a corregir. Origen = sección de `INPUT-BLOCK-ANTONIO.md`.

| ID | Origen | Propuesta de Antonio | Mejora integrada (mi edición) | Reutiliza | Estado |
|---|---|---|---|---|---|
| M1 | B§3, C§3 | Proyectos/subproyectos + planilla | **Una sola planilla** (proyecto→subproyecto→tema→tarea) con Profile/Index/Handoff como secciones, versionada por diferencias | `trabajos.py`, `memoria-yaiwes` SQLite | ⬜ |
| M2 | C§6, F | Context Pack / búsqueda anticipada | Paquete de 3–5 referencias; **retirar la inyección larga de `contexto.js`** (si se suma a la vieja no hay ahorro) | `router/cognitive_control_plane/context_composer.compose()` | ⛔⬜ |
| M3 | B§5 | Anchor Engine | Filtro **en servidor** (STRICT), anclas temporales por tarea y persistentes del usuario; ampliar ámbito = pedir autorización | `chat-ancla.js`, `anclaje-*.js` + filtro en `memoria.py` | 🟡⬜ |
| M4 | B§7 | Recuperación por niveles 0–5 | Estado → índice exacto → **SQLite FTS5** → grafo → vectores → LLM; datos exactos = fragmento original con referencia, nunca resumen | `memoria-yaiwes`, FTS5; Graphify/Graphiti/Qdrant solo si fallan niveles previos | ⬜ |
| M5 | B§6 | Event Bus en vez de memoria activa | **Un solo bus**, consumidores especializados, **outbox transaccional**; SQLite/Postgres primero, Redis Streams solo con varios workers | SQLite/Postgres, redis-py | ⬜ |
| M6 | B§10 | Memoria compactada sin perder instrucciones | Dos capas: **instrucciones originales literales + hash (no se compactan)** y memoria operativa (sí); perfil solo referencia | `source_of_truth.py` | ⬜ |
| M7 | C§1 hallazgo 3 | Fachada que consulta/replica a todos | **Recuperación selectiva**: un adaptador por consulta (no todos), guardado sin replicar a ciegas | `memoria_yaiwes/__init__.py` (l.347-395), `runtime_adapters.py` | 🟡 |
| M8 | A, B§12 | Memoria como tool; SDKs | **6 tools** `memory_profile/index/anchor/read/search/handoff`; escritura y anclas solo por software. Envolturas: OpenAI Agents `FunctionTool`, Strands `@tool`, PydanticAI Toolset, Haystack `PipelineTool`, MCP SDK como capa de conexión | SDKs descargados + `mcp_route.py` | ⬜ |
| M9 | C§7-8, E | Microkernel bajo demanda, 3 refutaciones, 12 checkpoints | OFF por defecto; se enciende solo con alerta validada; **8 de 12 checkpoints son reglas sin LLM**; las 3 refutaciones independientes cuando el riesgo lo pida; **cierre exige evidencia técnica real** (⛔ hallazgo de Sol: se cerró COMPLETED sin pruebas) | Memanto en lotes, no por turno | ⛔⬜ |
| M10 | B§8 | Reparto Graphify/Graphiti/Memanto | Graphify = código (AST, sin LLM) · índice propio = día a día · Graphiti = consultas temporales especiales · Memanto = reconciliación por lotes | `componentes/{graphify,graphiti,memanto}` | 🟡 |
| M11 | B§9 | Memoria de tareas de una sola ejecución | Una tarea = contexto limitado = resultado registrado; **handoff con campos estructurados, el agente no puede marcar COMPLETED** sin validación del controlador | `handoff-editor.js`, `pendientes-panel.js` | 🟡⬜ |
| M12 | B§11 | Profile dinámico por diferencias | Actualizar solo campos cambiados; separar **estado vigente / historial / hipótesis** | planilla (M1) | ⬜ |
| M13 | B§13 | Almacenamiento persistente, no caché | 3 clases: base de estado · almacenamiento persistente (HF) · caché opcional. Exige volumen persistente configurado | `hf_store.py`, `plugins/hf_storage` | 🟡 |
| M14 | C§9-10 | Bitácora, mapa mental, Crazy Wall + UI local | **Tres vistas del mismo dato**, sin LLM; planilla en IndexedDB **versionada** (la copia local no otorga permisos); `memory-sheet.js` | `chat-ancla.js` IndexedDB, pglite/sqlite-wasm, Chart.js | ⬜ |
| M15 | C§5 | TAG y TRIGGER | Catálogo **cerrado** de tags/eventos; el modelo devuelve un formulario, el software valida y emite el evento (nunca ejecuta texto libre) | Event Bus (M5) | ⬜ |
| M16 | D, E, F | Código de Sol (`memory_os.py` y paquete completo) | Revisión **en seco** del instalador contra la guardia → cablear por partes (P0 seguridad y memoria → P1 SO → P2 UI → P3 supervisión) | ZIP pendiente de subir | ⏳ |
| M17 | A | CLI-Anything, "Reu" | CLI-Anything ya en `chat-router/agentes/agentes-listos/` (CLI como tool); **"Reu" sin identificar** (¿`rea`?) — pendiente de confirmar | — | ❓ |

## 6. Orden de construcción
1. **P0** M1, M2, M3, M6 + cierre con evidencia real (M9/M11): seguridad y contexto.
2. **P1** M5, M7, M10: bus, fachada selectiva, reparto de grafos.
3. **P2** M8, M14, M15: tools SDK/MCP, vistas y UI local.
4. **P3** M9 completo, M12.
Cada paso: guardia OK + `pytest mvp` + prueba real antes de PASS. Si algo falla se revierte esa fase.

## 7. Riesgos conocidos
- Dos memorias distintas (HF por scope vs SQLite YAIWES): no fusionar sin verificar contratos.
- Dos bancos de secretos (env del MVP vs `riu_vault.db`): pendiente decisión A o B de Antonio.
- El código de Sol está generado y probado solo en local: no certificado en el Space.
- `memoria-yaiwes/tests` ya fallaba antes (3 errores de colección por carpetas heredadas).
