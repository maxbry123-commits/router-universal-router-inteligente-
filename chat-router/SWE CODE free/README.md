# SWE CODE free y SWEN CODE

**Objetivo:** usar las cuentas web gratis de Qwen y DeepSeek como si fueran una API (0 por token) para que OpenClaw trabaje sin depender del Router MVP. Si la web cae, responden Groq, NVIDIA y HF local.
**SWEN CODE free** = la capa de uso (se activa con el prefijo `SWEN CODE free`, `activar.js`). La cascada local de agentes (codex, opencode, swe-agent, openhands) es **SWE CODE** y se documenta en `../SWE CODE/README.md`, no aquí.
Documentos: `INSTRUCCIONES.md` (manual del agente) · `agente.md` (resumen del agente) · `ARQUITECTURA.md` (cómo funciona, se recupera y trabaja) · `HANDOFF.md` (dónde está todo, cómo retomar, estado).

## Flujo

```
OpenClaw (provider-openclaw.json)  ─┐
Chat Yaiwes (swe-directo.js)       ─┼➡️ web-bridge POST /v1/chat/completions ➡️ tab por conv_id ➡️ Qwen/DeepSeek web ➡️ respuesta
Chat vía Harness (RIU_SWE_BRIDGE_URL) ─┘
Respaldo si la web falla: Groq ➡️ NVIDIA ➡️ HF local (S1..S3)
```

El web-bridge es el router propio de SWE CODE free: no depende del Router MVP (que no se toca). El APK móvil (`puente-movil`) es un canal aparte (MCP `/mcp`); el bridge **no** lo invoca solo.

## Acceso (autenticación)
Toda ruta del bridge salvo `GET /health` exige credencial: `x-api-key` con **una de las 4 claves de acceso** del chat (`RIU_API_KEY`, `RIU_PUBLIC_CHAT_KEY`, `RIU_MCP_KEY`, `RIU_ROUTER_API_KEY`) o `BRIDGE_TOKEN` (`Authorization: Bearer` / `x-bridge-key`). Sin ninguna configurada el bridge responde **503** `SIN_CLAVE_DE_ACCESO`; con una errónea o ausente, **401** `NO_AUTORIZADO`. `/v1/claves` y `/v1/openclaw` piden además la clave de acceso; `/v1/swe/*` exige `BRIDGE_TOKEN` (y `aprobar`, también `BRIDGE_OPERATOR_TOKEN` + `x-operador`). Detalle y variables: `HANDOFF.md`. Las claves reales nunca van al repo, a los prompts ni a los checkpoints.

## Piezas

| Pieza | Dónde |
|---|---|
| Router propio (puente web OpenAI-compatible) | `../SWE CODE/web-bridge/src/`: `server.js` (rutas y puerta de acceso), `motor.js`, `browser.js`, `sites.js`, `consenso.js`, `cuentas.js`, `modos.js`, `formato.js`, `proyectos.js`, `memoria.js` |
| Respaldo, streaming y failover (Groq ➡️ NVIDIA ➡️ HF local) | `respaldo.js` |
| Checkpoints web (bloques) | `bloques.js` |
| Checkpoint universal de tarea (HF local, Groq, NVIDIA; Harness + disco) | `checkpoint_hf.js`, `retomar_local.js` |
| Backend de OpenClaw hacia el Harness (`/v1/swe/*`, capacidades) | `swe_rutas.js` |
| Configuración y espejo de OpenClaw (`GET /v1/openclaw`, `ejecutor_tools`) | `openclaw.js` |
| `POST /v1/responses` (mínimo, para Codex) | `responses.js` |
| Banco de claves Groq/NVIDIA (cifrado; puente a GitHub, rama `banco-claves`) | `clavesbanco.js`, `bancogithub.js`, `../SWE CODE/web-bridge/claves_banco.py` |
| Autoactualización del bridge desde `main` | `autoactualizar.js` |
| Comparación segura de secretos (sha256 + `timingSafeEqual`) | `iguales.js` |
| Memoria compartida con el chat | `../SWE CODE/web-bridge/memoria_hf.py` |
| Activador y gramática | `activar.js`, `swen.json` |
| Manual del agente | `INSTRUCCIONES.md`, `agente.md` |
| Selector de OpenClaw | `provider-openclaw.json` |
| UI de OpenClaw (contrato del plugin; la CLI no está instalada) | `openclaw-ui/` (`README.md`) |
| Entrada desde el chat Yaiwes | `../chat/frontend/swe-directo.js` (envío, contrato `TareaSWE`, SSE), `swe-selectores.js` (hoja de SWE CODE / SWEN CODE free), `swe-claves.js` |
| Agentes y adaptadores (Codex, OpenCode, SWE-agent, OpenHands, Claude Code, OpenClaw) | `../agentes/adaptadores/` (ver `../agentes/LEEME.md`) |
| Auto-evolución | `evolucion.py` |
| Puente móvil + APK | `puente-movil/`, `apk-movil/` (descarga: Configuración del chat ➡️ «Agente móvil (APK)») |
