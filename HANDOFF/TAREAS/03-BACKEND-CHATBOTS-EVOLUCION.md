# 03 — Backend de Chat BOTS / evolución (código)

Actualizado: 17-oct-2026 00:55, hora Bogotá (UTC-5). Índice: [README.md](README.md).

**Estado: EN PAUSA** (orden de Antonio). No retomar sin su orden.

## Objetivo
Backend de Chat BOTS (orquestador de agentes) y evolución de Grok Bot a nivel de código, reciclando componentes open source antes de escribir código propio.

## Ramas y evidencia
| Rama | Qué | Evidencia | Pendiente |
|---|---|---|---|
| [`orquestador-agentes-rebase`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/orquestador-agentes-rebase) ([`9dc637165f`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/commit/9dc637165f)) | Plugin backend `plugins/orquestador` (Chat BOTS v2) | sandbox HF Jobs 6 s 627 ms; pruebas v1 (ver [arquitectura](../CHATBOTS/README-ARQUITECTURA.md)) | Red de HF Jobs: pendiente de respuesta de Antonio |
| [`wip/grokbot-evolucionado`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/wip/grokbot-evolucionado) ([`5778306623`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/commit/5778306623)) | 24 propuestas + `research/grokbot-evolucionado/SINTESIS.md` | 24 imágenes `propuesta-01..24.png` | Pasar de propuestas a código |

## Pendiente
1. Mirror desde los enlaces de agentes: enlaces encontrados en [ENLACES DE AGENTES PARA MIRROR](#enlaces-de-agentes-para-mirror).
2. Respuesta de Antonio sobre la red de HF Jobs.
3. Reciclar componentes open source antes de escribir código: depende de [05-MOTORES-DESCARGA.md](05-MOTORES-DESCARGA.md).

## ENLACES DE AGENTES PARA MIRROR

Recopilado el 17-oct-2026 00:55, hora Bogotá (UTC-5), solo leyendo GitHub por API (nada descargado). Sin inventar: si un agente no tiene URL, se dice.

| Agente | URL | Dónde se encontró |
|---|---|---|
| OpenClaw | Repo propio (única ubicación): https://github.com/maxbry123-commits/openclaw — hoy `main` = `038b10b48d` (v2026.9.6, 27-sep-2026), **más viejo** que v2026.10.4 (`383c124c`) | Orden de Antonio 17-oct-2026: «No quedan en main trabaja organizado no cambias mi arquitectura» |
| Hermes | Repo propio (única ubicación): https://github.com/maxbry123-commits/hermes-agent — hoy `main` = `ca16be564d` (27-sep-2026), **más viejo** que v0.22.2 (`d923a5eb`) | Orden de Antonio 17-oct-2026 |
| OpenCode | https://github.com/maxbry123-commits/Agentes-motores-Wordflow-YAIWES/tree/main/OpenCode/OpenCode | [`agent_fleet_registry.json:24`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/chat%20router/workflow%20Loops%20code%20Yaiwes/code/wordflow_loop/wordflow_loop/agent_fleet/agent_fleet_registry.json#L24) |
| OpenHands | https://github.com/maxbry123-commits/Agentes-motores-Wordflow-YAIWES/tree/main/OpenHands/OpenHands | [`agent_fleet_registry.json:44`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/chat%20router/workflow%20Loops%20code%20Yaiwes/code/wordflow_loop/wordflow_loop/agent_fleet/agent_fleet_registry.json#L44) |
| Claude Code CLI | https://github.com/maxbry123-commits/Agentes-motores-Wordflow-YAIWES/tree/main/Core%20kernel%20razonamiento%20repo%20para%20Yaiwes/Claude-Code/Claude-Code | [`agent_fleet_registry.json:63`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/chat%20router/workflow%20Loops%20code%20Yaiwes/code/wordflow_loop/wordflow_loop/agent_fleet/agent_fleet_registry.json#L63) |
| MiMo Code | https://github.com/maxbry123-commits/Agentes-motores-Wordflow-YAIWES/tree/main/Core%20kernel%20razonamiento%20repo%20para%20Yaiwes/MiMo | [`agent_fleet_registry.json:84`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/chat%20router/workflow%20Loops%20code%20Yaiwes/code/wordflow_loop/wordflow_loop/agent_fleet/agent_fleet_registry.json#L84) |
| Codex | https://github.com/maxbry123-commits/Agentes-motores-Wordflow-YAIWES/tree/main/Core%20kernel%20razonamiento%20repo%20para%20Yaiwes/Codex/Codex | [`agent_fleet_registry.json:106`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/chat%20router/workflow%20Loops%20code%20Yaiwes/code/wordflow_loop/wordflow_loop/agent_fleet/agent_fleet_registry.json#L106) |
| SmolAgents | https://github.com/maxbry123-commits/Agentes-motores-Wordflow-YAIWES/tree/main/Core%20kernel%20razonamiento%20repo%20para%20Yaiwes/SmolAgents | [`agent_fleet_registry.json:125`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/chat%20router/workflow%20Loops%20code%20Yaiwes/code/wordflow_loop/wordflow_loop/agent_fleet/agent_fleet_registry.json#L125) |
| Aider | https://github.com/maxbry123-commits/Agentes-motores-Wordflow-YAIWES/tree/main/Core%20kernel%20razonamiento%20repo%20para%20Yaiwes/Aider/Aider | [`agent_fleet_registry.json:183`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/chat%20router/workflow%20Loops%20code%20Yaiwes/code/wordflow_loop/wordflow_loop/agent_fleet/agent_fleet_registry.json#L183) |
| Kimi K Code | https://github.com/maxbry123-commits/Agentes-motores-Wordflow-YAIWES/tree/main/Core%20kernel%20razonamiento%20repo%20para%20Yaiwes/Kimi-K2.5/Kimi-K2.5 | [`agent_fleet_registry.json:221`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/chat%20router/workflow%20Loops%20code%20Yaiwes/code/wordflow_loop/wordflow_loop/agent_fleet/agent_fleet_registry.json#L221) |
| Qwen Code | https://github.com/maxbry123-commits/Agentes-motores-Wordflow-YAIWES/tree/main/Core%20kernel%20razonamiento%20repo%20para%20Yaiwes/Qwen-Agent/Qwen-Agent | [`agent_fleet_registry.json:240`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/chat%20router/workflow%20Loops%20code%20Yaiwes/code/wordflow_loop/wordflow_loop/agent_fleet/agent_fleet_registry.json#L240) |
| Cline | https://github.com/maxbry123-commits/Agentes-motores-Wordflow-YAIWES/tree/main/Core%20kernel%20razonamiento%20repo%20para%20Yaiwes/Cline/Cline | [`agent_fleet_registry.json:259`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/chat%20router/workflow%20Loops%20code%20Yaiwes/code/wordflow_loop/wordflow_loop/agent_fleet/agent_fleet_registry.json#L259) |
| Agent Zero | https://github.com/maxbry123-commits/Agentes-motores-Wordflow-YAIWES/tree/main/Agent-Zero | [`agent_fleet_registry.json:299`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/chat%20router/workflow%20Loops%20code%20Yaiwes/code/wordflow_loop/wordflow_loop/agent_fleet/agent_fleet_registry.json#L299) |
| OpenDev | https://github.com/maxbry123-commits/Agentes-motores-Wordflow-YAIWES/tree/main/OpenDev | [`agent_fleet_registry.json:316`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/chat%20router/workflow%20Loops%20code%20Yaiwes/code/wordflow_loop/wordflow_loop/agent_fleet/agent_fleet_registry.json#L316) |
| Research Agent Lab | https://github.com/maxbry123-commits/Agentes-motores-Wordflow-YAIWES/tree/main/Research%20Agent%20Lab | [`agent_fleet_registry.json:333`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/chat%20router/workflow%20Loops%20code%20Yaiwes/code/wordflow_loop/wordflow_loop/agent_fleet/agent_fleet_registry.json#L333) |
| MiroThinker | https://github.com/maxbry123-commits/Agentes-motores-Wordflow-YAIWES/tree/main/MiroThinker | [`agent_fleet_registry.json:351`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/chat%20router/workflow%20Loops%20code%20Yaiwes/code/wordflow_loop/wordflow_loop/agent_fleet/agent_fleet_registry.json#L351) |
| Muse/Glimmer Code | **Sin URL de código** en el registro (`source_repo: operator_runtime`, `EXTERNAL_NOT_VENDORED`). Solo hay URL del modelo: https://huggingface.co/meta-models/Muse-Glimmer-30B-GGUF y del cookbook https://github.com/meta-models/meta-oss-cookbook/tree/main/agentic-fundamentals | [`agent_fleet_registry.json:203`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/chat%20router/workflow%20Loops%20code%20Yaiwes/code/wordflow_loop/wordflow_loop/agent_fleet/agent_fleet_registry.json#L203) · [`INPUT-VERBATIM-2026-09-21-r-auditor-meta-agents-watchdog.md:44`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/Documentos%20del%20proyecto/Notas%20del%20Director%20%28verbatim%29/INPUT-VERBATIM-2026-09-21-r-auditor-meta-agents-watchdog.md#L44) · [`INPUT-VERBATIM-2026-09-21-r-auditor-meta-agents-watchdog.md:82`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/Documentos%20del%20proyecto/Notas%20del%20Director%20%28verbatim%29/INPUT-VERBATIM-2026-09-21-r-auditor-meta-agents-watchdog.md#L82) |
| Goose | **Sin URL** (`source_repo: operator_runtime`, `source_path: null`) | [`agent_fleet_registry.json:282`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/chat%20router/workflow%20Loops%20code%20Yaiwes/code/wordflow_loop/wordflow_loop/agent_fleet/agent_fleet_registry.json#L282) |
| Agent Zero (upstream) | https://github.com/agent0ai/agent-zero | [`05-MOTORES-DESCARGA.md:15`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/HANDOFF/TAREAS/05-MOTORES-DESCARGA.md#L15) |
| OpenManus | https://github.com/FoundationAgents/OpenManus | [`05-MOTORES-DESCARGA.md:16`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/HANDOFF/TAREAS/05-MOTORES-DESCARGA.md#L16) |
| OpenHands (upstream) | https://github.com/OpenHands/OpenHands · https://github.com/OpenHands/software-agent-sdk · https://github.com/OpenHands/automation | [`05-MOTORES-DESCARGA.md:17`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/HANDOFF/TAREAS/05-MOTORES-DESCARGA.md#L17) |
| Agent-S | https://github.com/simular-ai/Agent-S | [`05-MOTORES-DESCARGA.md:18`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/HANDOFF/TAREAS/05-MOTORES-DESCARGA.md#L18) |
| Browser Use | https://github.com/browser-use/browser-use | [`05-MOTORES-DESCARGA.md:19`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/HANDOFF/TAREAS/05-MOTORES-DESCARGA.md#L19) |

Notas:
- OpenClaw y Hermes viven solo en sus repos propios (`maxbry123-commits/openclaw`, `maxbry123-commits/hermes-agent`). Las demás copias se borraron el 17-oct-2026 (rama `limpieza/openclaw-hermes-duplicados`): Yaiwes PR #1, osquestador-auditor PR #1, Agentes-motores-Wordflow-YAIWES PR #12, agentes PR #25 (`wordflow_loop/agent_sources`). **Pendiente** en `agentes/Core kernel Yaiwes/` (OpenClaw, Hermes-Agent, agents/Hermes, Componentes recuperados A/B: OpenClaw, Hermes-Agent y sus zips): la API de GitHub da timeout en esa carpeta. También quedan en la raíz de Agentes-motores-Wordflow-YAIWES archivos sueltos de OpenClaw 2026.7.1 (`openclaw.mjs`, `package.json`, README, etc.) mezclados con archivos del repo: por confirmar con Antonio.
- La copia de descarga en `router inteligente universal/Componente open soure router inteligente universal/` (`openclaw-v2026.10.4`, `hermes-agent-v0.22.2`) **sigue en main de forma temporal**: los repos propios están en versiones más viejas (27-sep-2026). Se borra cuando los repos propios lleguen a v2026.10.4 / v0.22.2 o más nuevo.
- En Yaiwes no hay carpeta de agentes ni de workflow loop: solo `namespace.json` que apunta a `maxbry123-commits/Agentes-motores-Wordflow-YAIWES` y `maxbry123-commits/agentes` (`memoria/osquestador auditor memoria core/…/almacenamiento huggueface/`).
- Wordflow loop completo (no se copia por tamaño): https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes ([`README-ARQUITECTURA.md:41`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/chat%20router/workflow%20Loops%20code%20Yaiwes/README-ARQUITECTURA.md#L41)).
- No se encontró ninguna URL de HF Space para los agentes.

## INSTRUCCIÓN PARA EL AGENTE BACKEND (MVP)

Orden de Antonio (verbatim): «El agente que va hacer el backend revisa que sirve lo Mvp necesario y borra los archivos que sobran»

1. Cuando terminen las descargas del motor (tarea 05), el agente backend de Chat BOTS revisa los componentes open source descargados y deja solo lo necesario para el MVP.
2. Borra directamente los archivos que sobran (permiso de Antonio ya dado).
3. Cablea los componentes en la arquitectura existente COMPONENTE → HARNESS → HTTP → FICHA → MODELO, sin arquitectura paralela ni puente.
4. Cruza con las 40 mejoras de [`HANDOFF/CHATBOTS/GROKBOT-FUNCIONAMIENTO-Y-MEJORAS.md`](../CHATBOTS/GROKBOT-FUNCIONAMIENTO-Y-MEJORAS.md), completa el código que falta y termina.

Orden de Antonio (verbatim, 17-oct-2026):

> Que haga una comparación investigación como funciona grockbot
> Luego la información que te di
> Luego los componentes que aporta sin sobre ingeniería
> Luego poda usa solo lo escencial
> Luego cablea y actuliza readme de arquitectura
> Borra la basura
>
> El agente backend pasa información a el agente de fromte el sistema chatbot debe tener
> 1. Una arquitectura interna usas skills archify lo descarga y lo usa dentro del chat dentro de chatbot luego crea una ventana de información donde está la pestaña de chatbot y va acrulizando creando la arquitectura de chat bot según
> 1. Fromtend aprobado
> 2. Backend lo que el agente le informa
> Luego el agente de fromtend dibuja en el diagrama el avance

Pasos, en orden:
1. Investigar y comparar cómo funciona Grok Bot.
2. Cruzar con la información de Antonio ([`HANDOFF/CHATBOTS/GROKBOT-FUNCIONAMIENTO-Y-MEJORAS.md`](../CHATBOTS/GROKBOT-FUNCIONAMIENTO-Y-MEJORAS.md), las 40 mejoras).
3. Elegir los componentes que aportan, sin sobreingeniería.
4. Podar: solo lo esencial.
5. Cablear en COMPONENTE → HARNESS → HTTP → FICHA → MODELO y actualizar la arquitectura en [`chat router/chat bot/README.md`](../../chat%20router/chat%20bot/README.md).
6. Borrar la basura (permiso de Antonio ya dado).
7. Informar el avance al agente de frontend en un archivo de estado: `chat router/chat bot/ESTADO-BACKEND.md`.

La arquitectura interna usa la skill «archify», que se descarga y se usa dentro de Chat BOTS. **Archify**: la skill más probable es [`tt-a1i/archify`](https://github.com/tt-a1i/archify) («Turn any idea, plan, or codebase into a beautiful interactive diagram. An agent skill for Claude Code, Codex, and more»). No está en los repos de Antonio. **Por confirmar con Antonio** que es esa.

## Reglas
- Una tarea = un agente, en su propia rama. Sin trabajo doble.
- Revisión ×3 por otro agente (conecta, prueba en PC y Android).
- Prueba en vivo Android 412 px, 4G, E2E real (Enviar → respuesta visible) **antes** de merge o deploy.
- No borrar nada sin el sí explícito de Antonio.
- No imprimir ni subir secretos (solo por nombre).
- No tocar la arquitectura: COMPONENTE → HARNESS (puente_chat) → HTTP → FICHA → MODELO.
- La computadora del bot es solo para pruebas de frontend.
- Español, mínimo, tiempos como «X s YYY ms». Al empezar y al terminar: actualizar PROGRESO en [`HANDOFF/CHATBOTS/HANDOFF.md`](../CHATBOTS/HANDOFF.md) y [`HANDOFF/TAREAS.md`](../TAREAS.md).
