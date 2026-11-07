# CODE_INDEX.md — Punto de entrada e índice de navegación del código

> **Un solo índice, cero copias.** Este fichero NO mueve, NO duplica y NO ejecuta nada: solo apunta con
> enlaces relativos a la **ubicación real** de cada pieza. La autoridad del cableado vive en
> [`SYSTEM_WIRING_REGISTRY.yaml`](SYSTEM_WIRING_REGISTRY.yaml) (registro maestro de integraciones) y en
> [`connections/`](connections/) (registro oficial de conexiones, topología, endpoints y healthchecks).
> La arquitectura y las raíces están en [`AGENTS.md`](AGENTS.md) (guía congelada) y
> [`kernel/INPUT_BLOCK_YAIWES_CABLEADO.md`](kernel/INPUT_BLOCK_YAIWES_CABLEADO.md) (objetivos, verbatim).

**Estado de este índice:** 2026-11-06 · run `20261104-kernel01` · ninguna ruta de este índice es inventada:
todas existen en el repo y están verificadas.

---

## Las 11 entradas del sistema

| # | Componente | Dónde está (ruta real) | Qué es |
|---|---|---|---|
| 1 | **Chatbot** | [`chat-router/chatbot/`](chat-router/chatbot/) | Suite de chatbot: [frontend-yaiwes](chat-router/chatbot/frontend-yaiwes/), [chat_space](chat-router/chatbot/chat_space/), [space](chat-router/chatbot/space/), [10-CHAT-FUNCIONES](chat-router/chatbot/10-CHAT-FUNCIONES/), [13-CHAT-UI-SUITE](chat-router/chatbot/13-CHAT-UI-SUITE/), [arquitectura](chat-router/chatbot/arquitectura/) |
| 2 | **Chat Router** | [`chat-router/chat/`](chat-router/chat/) | Router de chat. [frontend Chat YAIWES](chat-router/chat/frontend/) · [backend Chat YAIWES](chat-router/chat/backend/) ([mvp](chat-router/chat/backend/mvp/), [deepseek_harness](chat-router/chat/backend/deepseek_harness/)) · [espejo de OpenClaw](chat-router/chat/espejo/espejo_prod.js) · [auditoría](chat-router/chat/auditoria/) · [e2e](chat-router/chat/e2e/) |
| 3 | **SWE CODE free** | [`chat-router/SWE CODE free/`](chat-router/SWE%20CODE%20free/) | [ARQUITECTURA.md](chat-router/SWE%20CODE%20free/ARQUITECTURA.md) · [HANDOFF.md](chat-router/SWE%20CODE%20free/HANDOFF.md) · [agente.md](chat-router/SWE%20CODE%20free/agente.md) · [activar.js](chat-router/SWE%20CODE%20free/activar.js) · [apk-movil](chat-router/SWE%20CODE%20free/apk-movil/) |
| 4 | **SWE CODE** | [`chat-router/SWE CODE/`](chat-router/SWE%20CODE/) | [INPUTS_VERBATIM.md](chat-router/SWE%20CODE/INPUTS_VERBATIM.md) · [mini_router.py](chat-router/SWE%20CODE/mini_router.py) · [ficha.json](chat-router/SWE%20CODE/ficha.json) · [cascada.json](chat-router/SWE%20CODE/cascada.json) · [web-bridge](chat-router/SWE%20CODE/web-bridge/) · pruebas `test_mini_router*.py` |
| 5 | **Router MVP** | [`router-mvp/`](router-mvp/) | [raiz_router](router-mvp/raiz_router/) (con [ARQUITECTURA.md](router-mvp/raiz_router/ARQUITECTURA.md) y [HANDOFF.md](router-mvp/raiz_router/HANDOFF.md)) · [raiz_fichas_prompt](router-mvp/raiz_fichas_prompt/) · [mvp](router-mvp/mvp/) ([app.py](router-mvp/mvp/app.py), [bank.py](router-mvp/mvp/bank.py), [compute.py](router-mvp/mvp/compute.py), [control.py](router-mvp/mvp/control.py)) · [router](router-mvp/router/) · [fichas](router-mvp/fichas/) · [componentes](router-mvp/componentes/) |
| 6 | **Router SWE CODE** | [`chat-router/SWE CODE/mini_router.py`](chat-router/SWE%20CODE/mini_router.py) + [`router-mvp/raiz_router/`](router-mvp/raiz_router/) | Router mínimo de SWE CODE y su raíz de router; comparte fichas con [raiz_fichas_prompt](router-mvp/raiz_fichas_prompt/) |
| 7 | **Harness DeepSeek** | [`chat-router/harness/`](chat-router/harness/) · [`chat-router/chat/backend/deepseek_harness/`](chat-router/chat/backend/deepseek_harness/) · [`chat-router/plugins/deepseek_harness/`](chat-router/plugins/deepseek_harness/) | Centro de distribución de instrucciones: [plugin.py](chat-router/harness/plugin.py), [server.py](chat-router/harness/server.py), [ficha.json](chat-router/harness/ficha.json), [README.md](chat-router/harness/README.md) |
| 8 | **Sistema central de conexión y cableo** | [`SYSTEM_WIRING_REGISTRY.yaml`](SYSTEM_WIRING_REGISTRY.yaml) · [`connections/`](connections/) · [`chat-router/MAPA.md`](chat-router/MAPA.md) | **Integration Registry** (registro maestro) + **System Architecture Map**: [registry.yaml](connections/registry.yaml), [topology.yaml](connections/topology.yaml), [endpoints.yaml](connections/endpoints.yaml), [healthchecks.yaml](connections/healthchecks.yaml), [wiring_changelog.md](connections/wiring_changelog.md), [wiring_history.jsonl](connections/wiring_history.jsonl), `bridge_report.json` (lo genera el job `bridge`, N5/E6) |
| 9 | **Agentes** | [`chat-router/agentes/`](chat-router/agentes/) | [adaptadores](chat-router/agentes/adaptadores/) · [agentes-yaiwes](chat-router/agentes/agentes-yaiwes/) · [claude-code](chat-router/agentes/claude-code/) · [orquestacion](chat-router/agentes/orquestacion/) · [runtime](chat-router/agentes/runtime/) · [LEEME.md](chat-router/agentes/LEEME.md) |
| 10 | **Loop, cola y watchdog** | [`chat-router/Loop cola wachdog/`](chat-router/Loop%20cola%20wachdog/) | [Loop](chat-router/Loop%20cola%20wachdog/Loop/) (incluye `EJECUTAR_CODA.py`, `GENERAR_ECC_PY.py`, `NCTModeSelector.tsx`) · [Cola](chat-router/Loop%20cola%20wachdog/Cola/) (plugin.py, ficha.json, nct_addons) · [watchdog](chat-router/Loop%20cola%20wachdog/wachdog/) · [state](chat-router/Loop%20cola%20wachdog/state/) · workflow completo: [workflow-loop-code-yaiwes](chat-router/workflow-loop-code-yaiwes/) |
| 11 | **System prompt y motores** | [`router-mvp/raiz_fichas_prompt/`](router-mvp/raiz_fichas_prompt/) · [`chat-router/motores/`](chat-router/motores/) · [`chat-router/chat/frontend/swe-systemprompt.js`](chat-router/chat/frontend/swe-systemprompt.js) | Raíz de fichas/prompt: [ARQUITECTURA.md](router-mvp/raiz_fichas_prompt/ARQUITECTURA.md), [HANDOFF.md](router-mvp/raiz_fichas_prompt/HANDOFF.md), [sdk_qwen](router-mvp/raiz_fichas_prompt/sdk_qwen/) · Motores: [fabrica-motores](chat-router/motores/fabrica-motores/), [motores](chat-router/motores/motores/), [pruebas-nvidia-groq](chat-router/motores/pruebas-nvidia-groq/), [evidencia](chat-router/motores/evidencia/) |

## Raíces de plataforma y de control (fuera del flujo de producto)

| Pieza | Ruta | Para qué |
|---|---|---|
| Núcleo / kernel | [`kernel/`](kernel/) | [KERNEL.yaml](kernel/KERNEL.yaml) (handoff y estado), [DAG.yaml](kernel/DAG.yaml), [GUIDE.md](kernel/GUIDE.md), [INPUT_BLOCK.yaml](kernel/INPUT_BLOCK.yaml) (congelado), [INPUT_BLOCK_YAIWES_CABLEADO.md](kernel/INPUT_BLOCK_YAIWES_CABLEADO.md) (objetivos, verbatim) |
| Jobs del DAG | [`ops/`](ops/) | `common.py`, `j0..j10`, `j6b_swap.py`, `bridge.py`, `wiring_check.py`, `kernel.py`, `launch.sh`, `launch_hf.py`, `historical_wiring_audit.py`, `root_structure_audit.py` |
| Memoria del agente (estado de sesión) | [`memory_agente_minimax_02.md`](memory_agente_minimax_02.md) | Handoff operativo persistente del agente (no es estado canónico) |
| Cuarentena | [`_quarantine/`](_quarantine/) | Ficheros apartados por análisis de dependencias (nunca se borran sin evidencia) |
| Guía de organización (FROZEN) | [`AGENTS.md`](AGENTS.md) | Raíces, reglas de organización, protocolo de modificación y de mantenimiento |
| Mapa de organización | [`chat-router/MAPA.md`](chat-router/MAPA.md) | De dónde → a dónde de cada pieza, por fases, con riesgo y enlace de compatibilidad |

## Cómo se usa este índice

1. Para **navegar**: pulsa la ruta; no hay copias ni enlaces simbólicos.
2. Para **cablear**: toda conexión nueva se registra primero en
   [`SYSTEM_WIRING_REGISTRY.yaml`](SYSTEM_WIRING_REGISTRY.yaml) y en
   [`connections/registry.yaml`](connections/registry.yaml) (regla R7/R9 de la guía).
3. Para **activar**: una conexión pasa a `ACTIVE` solo con las 7 condiciones del umbral
   (ver [`kernel/INPUT_BLOCK_YAIWES_CABLEADO.md` §4.4](kernel/INPUT_BLOCK_YAIWES_CABLEADO.md)); una prueba
   superficial no la activa.
4. Para **cambiar la arquitectura**: se requiere análisis de impacto y autorización
   (regla 16 de la guía); este índice se actualiza en el mismo commit.
