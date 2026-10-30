# SWEN CODE free

Sistema libre del router: modos + cuentas web (Qwen/DeepSeek) + móvil como último respaldo.
**Solo se activa cuando el mensaje empieza con `SWEN CODE free`.**
Manual de trabajo (modelos + agentes, igual para los 2 chats): **`INSTRUCCIONES.md`**.

## Arquitectura

```
chat (Riu o OpenClaw) ──► plugins ──► deepseek_harness ──► HTTP router
        │                                                    │
        └─ los 2 chats leen INSTRUCCIONES.md por la misma vía ─┘

SWEN CODE free ──► web-bridge :7870 ──► cuentas web (Qwen/DeepSeek)
               ──► cola S1/S2/S3 ──► modelos locales (model=)
               ──► puente-movil ──► APK ──► Chrome del móvil (último respaldo)

Pipelines paralelos (conv_id = tab/hilo propio):
  CODE: lfm2.5 anota → qwen-coder organiza+refactor → lfm2.5 despliega
  FREE: qwen instruye → swe-agente → lfm2.5 despliega (sin refactor)
Espejo: un modelo se clona a otro conv_id/slot para dividir trabajo.
```

## Piezas

| Pieza | Qué es |
|---|---|
| `activar.js` | Parser: `SWEN CODE free [modo <m>] [con|solo|modelo <modelo>] [chat <id>] <texto>` → `{modo, modelo, conv_id, prompt}` |
| `swen.json` | Config: modos, selección de modelo (cóncil/aliases), paralelo+espejo, cadena de respaldo, endpoints por env |
| `agente.md` | Las cosas que el agente sabe hacer solo (modos, re-sesión, .md, deploy) |
| `INSTRUCCIONES.md` | Manual único compartido por los 2 chats (Riu + OpenClaw) via plugins→deepseek_harness |
| `../SWE CODE/web-bridge/` | Puente web: métodos 1+4 / respaldo 2+3, bloques+checkpoint, consenso 3-modelos+síntesis, rotación de correos, tabs por conv_id |
| `puente-movil/` | MCP-HTTP ↔ WSS: los modelos llaman `tools/call`, la APK ejecuta en el móvil |
| `apk-movil/` | APK mínima: servicio foreground + WSS saliente + accesibilidad sobre Chrome |

## Selección de modelo

- `concilio`/`cóncil`/`todos`/`los 3` (o `consulta` sin modelo) → fan-out a los 3 web + síntesis.
- Nombre de modelo (`deepseek v4`, `qwen 3.7`, `qwen 3.8`, `liquid`, `qwen code`) → **un solo modelo** para consulta o tarea individual.
- `chat <id>`/`seccion <id>` → conv_id propio = web/tab separada = **2 secciones en paralelo**.
- Espejo: un modelo se clona a otro conv_id/slot para dividir trabajo.

## Pipelines

- CODE: anota `lfm2.5` → `qwen-coder` organiza+refactoriza → otro `lfm2.5` despliega.
- FREE: `qwen` da instrucciones → `swe-agente` → otro `lfm2.5` despliega (sin refactor).

## Cadena de respaldo

1. web-bridge (proceso en el servidor Riu :7870, métodos CDP/nativo; respaldo intercept/DOM)
2. rotación de correos dentro del web-bridge
3. modelos locales cola S1/S2/S3 (`model=`)
4. **apk-movil**: Chrome del móvil (IP residencial, sesión real) — último eslabón

## APK

- Se compila en HF (Job/Space, no GitHub Actions) y se sirve en `GET /apk` del Space.
- Descarga: panel **Configuración → 13 · Agente móvil (APK) → "Descargar APK"** — un tap desde el chat.
- Instalación una vez: instalar → "Conectar agente" → "Activar accesibilidad".
- El móvil abre WSS a `PUENTE_MOVIL_URL/agente` (tras NAT, el canal sale del móvil).
- Acciones del modelo: `abrir_url`, `leer_pantalla`, `escribir`, `tap`, `atras`.

## Recuperar y reparar

- `SESSION_EXPIRED` → `POST /refresh_session`. Media tarea → mismo `conv_id` (checkpoint). Space dormido → reintentar.
- Cable roto: symlink `plugins/<nombre>` → raíz + `ficha.json` + entrada en `cableado.manifest.json`. Nada protegido se toca. Detalle: `INSTRUCCIONES.md` §8.

## Handoff / enlaces

| Pieza | Ubicación |
|---|---|
| Parser/activación | `chat-router/SWE CODE free/activar.js` |
| Config + selección modelo + paralelo/espejo | `chat-router/SWE CODE free/swen.json` |
| Instrucciones nativas del agente | `chat-router/SWE CODE free/agente.md` |
| Manual único (2 chats) | `chat-router/SWE CODE free/INSTRUCCIONES.md` |
| Ficha plugin (registro en harness) | `chat-router/SWE CODE free/ficha.json` |
| Cascada CODE (edificio 1) | `chat-router/SWE CODE/` |
| Puente web | `chat-router/SWE CODE/web-bridge/` |
| Puente móvil MCP↔WSS | `chat-router/SWE CODE free/puente-movil/` |
| APK fuente | `chat-router/SWE CODE free/apk-movil/` |
| Registro en el mapa | `cableado.manifest.json` (enlaces + plugins) |
| Descarga APK en el chat | Configuración → 13 · Agente móvil → "Descargar APK" |
