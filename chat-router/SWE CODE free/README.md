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

## Piezas

| Pieza | Dónde |
|---|---|
| Router propio (puente web OpenAI-compatible) | `../SWE CODE/web-bridge/src/` (`server.js`, `motor.js`, `respaldo.js`, `bloques.js`, `cuentas.js`, `proyectos.js`, `memoria.js`, `formato.js`, `modos.js`) |
| Memoria compartida con el chat | `../SWE CODE/web-bridge/memoria_hf.py` |
| Activador y gramática | `activar.js`, `swen.json` |
| Manual del agente | `INSTRUCCIONES.md`, `agente.md` |
| Selector de OpenClaw | `provider-openclaw.json` |
| Entrada desde el chat Yaiwes | `../chat/frontend/swe-directo.js` |
| Auto-evolución | `evolucion.py` |
| Puente móvil + APK | `puente-movil/`, `apk-movil/` (descarga: Configuración del chat ➡️ «Agente móvil (APK)») |
