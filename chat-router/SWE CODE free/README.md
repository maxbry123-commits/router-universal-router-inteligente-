# SWE CODE free y SWEN CODE

**Objetivo:** usar las cuentas web gratis de Qwen y DeepSeek como si fueran una API (0 por token) para que OpenClaw trabaje sin depender del Router MVP. Si la web cae, responden Groq, NVIDIA y los modelos locales de HF.
**SWEN CODE free** = la capa de uso (se activa con el prefijo `SWEN CODE free`). **SWE CODE** = la cascada local de HF (`../SWE CODE/`).
Documentos: `INSTRUCCIONES.md` (manual del agente) · `ARQUITECTURA.md` (cómo funciona y cómo se recupera) · `HANDOFF.md` (dónde está todo, estado y gaps).

## Flujo

```
Selector del chat / UI OpenClaw ➡️ plugins ➡️ Harness DeepSeek (HTTP) ➡️ plugin swen_code_free / swe_code (router propio: web-bridge :7870) ➡️ tab por conv_id ➡️ Qwen/DeepSeek web ➡️ respuesta por el mismo camino
Respaldo: web ➡️ rotar correo ➡️ Groq ➡️ NVIDIA ➡️ HF local S1-S3 ➡️ APK móvil
```

OpenClaw es un espejo del chat Yaiwes: usa sus componentes y sus modelos, pero su router propio (el web-bridge) no depende del Router MVP.

## Piezas

| Pieza | Dónde |
|---|---|
| Router propio (puente web OpenAI-compatible) | `../SWE CODE/web-bridge/src/` (`server.js`, `motor.js`, `respaldo.js`, `bloques.js`, `cuentas.js`) |
| Activador y gramática | `activar.js`, `swen.json` |
| Manual del agente | `INSTRUCCIONES.md`, `agente.md` |
| Selector de OpenClaw | `provider-openclaw.json` |
| Auto-evolución | `evolucion.py` |
| Puente móvil + APK | `puente-movil/`, `apk-movil/` (descarga: Configuración del chat ➡️ «Agente móvil (APK)») |
| Cascada local | `../SWE CODE/mini_router.py` |
