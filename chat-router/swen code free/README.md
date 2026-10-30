# SWEN CODE free

Sistema libre del router: modos + cuentas web (Qwen/DeepSeek) + móvil como último respaldo.
**Solo se activa cuando el mensaje empieza con `SWEN CODE free`.**

## Piezas

| Pieza | Qué es |
|---|---|
| `activar.js` | Parser: `SWEN CODE free modo <modo> <texto>` → `{modo, prompt}` |
| `swen.json` | Config: modos, cadena de respaldo, endpoints por env |
| `agente.md` | Las 4 cosas que el agente sabe hacer solo (modos, re-sesión, .md, deploy) |
| `../swen code/web-bridge/` | Puente web ya montado: métodos 1+4 / respaldo 2+3, bloques+checkpoint, consenso 3-modelos+síntesis, rotación 5-9 correos |
| `puente-movil/` | MCP-HTTP ↔ WSS: los modelos llaman `tools/call`, la APK ejecuta en el móvil |
| `apk-movil/` | APK mínima: servicio foreground + WSS saliente + accesibilidad sobre Chrome |

## Cadena de respaldo

1. web-bridge (Space swe-code-web, métodos CDP/nativo; respaldo intercept/DOM)
2. rotación de correos dentro del web-bridge
3. modelos locales cola S1/S2/S3 (`model=`)
4. **apk-movil**: Chrome del móvil (IP residencial, sesión real) — último eslabón

## APK

- Compila sola en GitHub Actions (`swecode-apk.yml`) → artifact `swecode-agente-apk`.
- Instalación una vez: instalar → "Conectar agente" → "Activar accesibilidad" (1 vez).
- El móvil abre WSS a `PUENTE_MOVIL_URL/agente` (tras NAT, el canal sale del móvil).
- Acciones del modelo: `abrir_url`, `leer_pantalla`, `escribir`, `tap`, `atras`.

## Secretos (nunca en código)

`PUENTE_TOKEN`, `WEB_ACCOUNTS`, `WEB_PASS`, `BRIDGE_PROXY` → HF Secrets del Space correspondiente.
