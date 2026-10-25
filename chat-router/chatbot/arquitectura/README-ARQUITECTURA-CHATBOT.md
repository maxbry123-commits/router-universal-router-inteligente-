# README ARQUITECTURA — 2. CHAT BOT (SO de agentes)

Raíz (destino): `chat-router/chatbot/` · Hermano: `chat-router/memoria/arquitectura/README-ARQUITECTURA-MEMORIA-ALMACENAMIENTO.md`
Estado: **arquitectura documentada, nada nuevo cableado** (modo recepción). Fecha: 2026-10-25.

## 1. Objetivo
Un software que (a) funciona como **tool** (cualquier agente lo llama) y (b) como **sistema operativo de agentes**: el software gobierna, el agente ejecuta solo cuando lo activa un trigger, la LLM piensa. **LLM ≤ 5 %** (meta de diseño, aún no medida).
Frase guía: *la LLM piensa, el software gobierna, los agentes ejecutan únicamente cuando el sistema los activa.*
Alcance de esta raíz: solo lo necesario para una app tipo GrokBot (no agentes sueltos: esos están en `chat-router/agentes/`).

## 2. Qué se conserva intacto (ya cableado y funcional — NO se toca)
`chat/frontend/*` (incl. `ventana-room.js`, `ventana-tareas.js`, `ventana-cola.js`, `ventana-loop.js`, `ventana-watchdog.js`, `LOOP-wachdog-cola.json`, `agentes-mirror.js`) · `chat/backend/mvp/{app,control,sala_turno,mcp_route,mcp_cliente,harness_client,trabajos,externos,escalado}.py` · `deepseek_harness` · `router/cognitive_control_plane/policy_guard.py` · MCP del router.
Lo nuevo entra por contratos HTTP/MCP; guardia de cableado como red.

## 3. Mapa de carpetas de esta raíz
```
chat-router/chatbot/
├── arquitectura/        ← este README + INPUT-BLOCK-ANTONIO.md (texto literal)
├── componentes/         OpenBot-nightly-labs [PolyForm NC: solo referencia], OpenBot-ashhart, docs-grok-bot/ (7 .md),
│                        open-webui, guardrails, docker-py, grafana, ollama, vllm, SGLang, llama.cpp, web-llm,
│                        wllama, transformers.js, pglite, sqlite-wasm, react, vite, zustand, tailwindcss, Chart.js, lucide, TypeScript, plex
├── 10-CHAT-FUNCIONES/ · 13-CHAT-UI-SUITE/ · chat_space/ · space/ · frontend-yaiwes/
Relacionados fuera de esta raíz:
  chat-router/agentes/agentes-listos/ (OpenHands, CLI-Anything, browser-use, rea…)
  chat-router/agentes/frameworks/ (openai-agents-python, strands-agents-sdk-python, haystack, pydantic-ai, Temporal, Prefect, Durable-Task…)
  chat-router/motores/ (descarga/copia/move)  ·  router-componentes/mcp-python-sdk
```

## 4. Arquitectura (entrada de Antonio + mejoras integradas)
```
USUARIO → CHAT/ROOM → SOFTWARE SO (estado · agenda · watchdog · triggers · permisos · auditoría)
   PASO 0  INPUT SHARK (literal + hash) → 3 investigaciones → 9 refutaciones → usuario autoriza
   PASO 1  ORQUESTADOR (temporal, OFF al terminar) → plan: objetivos, tareas, DAG, ≤8 agentes, ámbitos de escritura
   PASO 2  AGENDA → TRIGGER → AGENTE ON → SANDBOX → resultado → AGENTE OFF
   PASO 2.1 SHERIFF → CENTINELA → GUARDIÁN (capa 1 reglas + capa 2 LLM) → TESTS → PASS/FAIL (decide el software)
   PASO 3  despliegue autorizado → auditoría post-despliegue (hallazgo ⇒ nueva tarea, no cambio libre)
   TRANSVERSAL  LLM LOCK · TOOL LOCK · TASK LOCK · WATCHDOG · POLICY ENGINE
```
Dos edificios por HTTP: Edificio 1 = chat/router/controlador SO/DAG/scheduler/policy/estado; Edificio 2 = Plugin Host/Agent Runner/Sandbox/herramientas/verificadores.

## 5. Integración 1 a 1 (propuesta de Antonio → mejora integrada → con qué → estado)

Estados: ✅ existe y cableado · 🟡 existe sin cablear / parcial · ⬜ por construir · ⛔ riesgo · ⏳ espera código de Sol. Origen = sección de `INPUT-BLOCK-ANTONIO.md`.

| ID | Origen | Propuesta de Antonio | Mejora integrada (mi edición) | Reutiliza | Estado |
|---|---|---|---|---|---|
| C1 | C§1-2 | Software gobierna, agentes ejecutan | **Un solo núcleo** (máquina de estados + DAG) liberando tareas por eventos; el orquestador solo propone | `trabajos.py`, `LOOP-wachdog-cola.json`, Durable-Task-Python | ⬜ |
| C2 | C§3 P2 | Watchdog (heartbeat, timeout, reintentos) | Pasar la lógica **del frontend al backend** (`ventana-watchdog.js` hoy es UI): timeout 10 min–48 h, clave de idempotencia por ejecución | `control.py`, `ventana-watchdog.js` | 🟡⬜ |
| C3 | C§3 P2.1 | Sheriff / Centinela / Guardián | **Capa 1 = reglas sin LLM** (permisos, rutas, dependencias, pruebas); capa 2 LLM solo si la regla no decide; PASS de LLM nunca sustituye las pruebas | `policy_guard.py`, guardrails | 🟡⬜ |
| C4 | C§3 P4 | Permisos temporales y bloqueos en backend | Cada agente nace **sin permisos**; permiso por tarea con caducidad y revocación; **no copiar** `danger-full-access`/`approvalPolicy: never` de OpenBot | `control.py`, `mcp_route.py` | ⬜ |
| C5 | C§3 P1 | ≤ 8 agentes sin pisarse | **Locks de escritura** por tarea (leer sí, escribir uno); DAG de dependencias | tabla de locks (SQLite/Postgres) | ⬜ |
| C6 | C§3 P0 | Input Shark + 3 investigaciones + 9 refutaciones | Guardar instrucción **literal con hash** (sin LLM); lanzar las 3 investigaciones **solo si el input es nuevo o ambiguo**; el software registra las 9 evaluaciones y comprueba cobertura/contradicciones (el orquestador no se juzga solo) | índice de memoria (M4), `prompt.py` | ⬜ |
| C7 | C§3 P3 | Ejecución → verificación → despliegue → refactoría | Separación estricta; el agente de refactoría **no modifica el despliegue**, produce hallazgo y el software abre tarea de reparación ligada al plan | sandbox (C8), CI propio por git/motores | ⬜ |
| C8 | C§4 | Agent Runner aislado | docker-py + runner (OpenHands SDK / CLI-Anything) por tarea; **sin GitHub Actions** (Antonio: solo motores o comandos git) | `componentes/docker-py`, `agentes-listos/*` | ⬜ |
| C9 | C§6 | Ejecución duradera | Tres registros: **estado / eventos / efectos**. Empezar con PostgreSQL/SQLite + máquina de estados; Temporal solo si crece la concurrencia | Temporal-Python-SDK, Durable-Task (descargados) | ⬜ |
| C10 | C§5 | Dos edificios por HTTP | Controlador SO en Edificio 1; Agent Runner/verificadores en Edificio 2; sin importaciones cruzadas | Harness + Plugin Host existentes | ✅base |
| C11 | A, C§1 | OpenBot / Grok Bot / Muse / Dispatch / Dots como referencia | Tomar **ideas** (delegación, salas, Kanban, Sentinel externo, tareas programadas, continuidad); nightly-labs solo lectura por licencia | `componentes/OpenBot-*`, `docs-grok-bot/` | 🟡 |
| C12 | memoria A | Todo como tool: SDKs | Exponer el SO por MCP y envolturas `FunctionTool` (OpenAI Agents), `@tool` (Strands), Toolset (PydanticAI), `PipelineTool` (Haystack) | SDKs descargados | ⬜ |
| C13 | — (mejora) | Observabilidad | Métricas/trazas por transición y para medir el % real de LLM | Prometheus, Phoenix, Grafana | ⬜ |
| C14 | — (mejora) | UI = panel del SO | ROOM, Kanban, cola y watchdog leen **el estado del núcleo**, no estado propio del navegador | `ventana-*.js` | 🟡 |
| C15 | F (memoria) | Código de Sol (agentes, scheduler, watchdog, verificadores) | Revisión en seco → cablear por partes tras pasar la guardia | ZIP pendiente | ⏳ |

## 6. Orden de construcción
1. **P0** C1, C2, C3, C4 (núcleo, watchdog real, reglas, permisos) — y cierre de tarea con evidencia técnica real.
2. **P1** C5, C6, C8, C9 (locks, Input Shark, sandbox, durabilidad).
3. **P2** C12, C14, C13 (tools/MCP, UI del SO, medición).
4. **P3** C7 completo, C11 refinado.
Cada paso: guardia OK + `pytest mvp` + prueba real antes de PASS.

## 7. Riesgos conocidos
- Licencia de OpenBot nightly-labs (PolyForm Noncommercial): referencia, no copia.
- OpenBot por defecto corre con acceso total sin aprobación: inaceptable aquí (C4).
- Sin sandbox real (Docker) el Agent Runner no se puede certificar.
- Verificación en vivo solo vía Firecrawl/Grok: la sandbox no llega al Space ni a Vercel.
- "Reu" (lista de Antonio) sin identificar.
