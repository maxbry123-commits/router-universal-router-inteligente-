# Cómo se conecta el backend · local + nube · factory oculta

Fecha: 2026-09-09 · **antes de más ventanas**. Esperando decisión D01–D12.

## Error a no repetir

El botón **FACTORY dentro de RUN-01** es útil para **probar**. **No** es el producto.  
Si el HTML del usuario tiene Factory, View Source lo ve. Eso viola G11.

**Producto final = 0 Factory.** El cableado vive **fuera** de la ventana.

## Tres capas (no una)

```
[1 FÁBRICA]  solo tú. App/host interno. Clave OS. Nunca se empaqueta al usuario.
     │  inyecta BACKEND_WIRE por postMessage (una vez al arrancar)
     ▼
[2 HOST]     chrome YAIWES. Carga ventanas aprobadas (1 HTML = 1 iframe).
     │  no secretos. solo IDs de enchufe.
     ▼
[3 VENTANA]  RUN-01, RUN-02, WALL-01…  UI del producto.
             Botón → plugin OUT → host → (local kernel | nube)
```

## Qué es local vs nube

| Corre **local** (dispositivo) | Corre **nube** |
|------------------------------|----------------|
| HTML/CSS/JS de cada ventana | LLM (Grok, Claude, MiniMax…) |
| Host chrome + unión de iframes | Agent API / webhooks |
| Sandbox iframe / worker / docker local | Sync de proyecto si lo pides |
| State de UI, DAG YAML, bitácora | Auth de cuentas AI |
| Kernel: cola, sentinel, files | |

El botón **Run** no “es la IA”. **Arma un paquete** `{nodes, input, dest}` y lo **entrega** al enchufe.  
Quién ejecuta: **tú lo decides en la fábrica**, no el usuario.

## Flujo de un clic (producto)

1. Usuario toca **Run** en RUN-01.  
2. Ventana emite `FROMTED_CASCADE_RUN` + payload (sin URL, sin token).  
3. Host recibe. Mira `wire.json` (archivo **fuera** del HTML, en `$APPDATA` o kernel local).  
4. Host llama:
   - `local://kernel/cascade.run` **o**
   - `https://api…/agent/complete` con el token que **el kernel** lee del **keychain OS** (Tauri/Capacitor).  
5. La respuesta vuelve al host → `postMessage` IN a RUN-01 → pinta destino.

La ventana **nunca** guarda `sk-…` ni URL secreta.

## Cómo se integra DESPUÉS del OK (producto)

| Paso | Qué |
|------|-----|
| A | `OK RUN-01` → copia a `02-fromted` |
| B | Fábrica (app aparte) abre la ventana en iframe, pruebas 5 clicks, pegas wires |
| C | **Lock producto**: script quita Factory del HTML, escribe `wire/RUN-01.json` en kernel, no en git público |
| D | Host `03-producto` carga `RUN-01.html` + `RUN-02.html`… |
| E | Empaque: web / Linux / Android / iOS / Windows (mismo HTML, kernel nativo distinto) |

## Cómo el usuario NO entra a configuración

1. **No hay botón Factory en el HTML de producto.**  
2. Fábrica = `fabrica.html` **otro origen o app nativa** con clave + OS keyring.  
3. View Source del producto: solo `emit("CASCADE_RUN", packet)` — ni URL.  
4. `wire.json` permisos de archivo: solo el proceso kernel (Tauri `fs:deny` webview).  
5. Lo que SÍ puede el usuario: tema, tamaño letra, on/off de **módulos que tú habilitaste** — panel **in-product** inocuo, no backend.

## 8 simulaciones

| # | Caso | Qué debe pasar |
|---|------|----------------|
| 1 | Run sin wire | UI: “sin conexión”. Log fábrica: `SIN_BACKEND`. No inventa respuesta IA. |
| 2 | Wire local docker | Kernel ejecuta sandbox en máquina. Nube = 0. |
| 3 | Wire nube Grok/MiniMax | Kernel pone token. Ventana no lo ve. |
| 4 | Usuario View Source | No hay URL ni Factory. |
| 5 | RUN-01 + RUN-02 juntas | Host enruta eventos. No se unifican HTML. |
| 6 | Offline | Local sigue. Nube: cola local, retry. |
| 7 | Clave fábrica robada | Keyring OS + clave no en git. Rotar. |
| 8 | APK Android | Mismo HTML. Kernel Capacitor. Wires en app private storage. |

## 12 pasos para DECIDIR (antes de seguir)

Contesta **sí/no** o elige. Sin esto no fabrico RUN-02.

| D | Pregunta | Default que recomiendo |
|---|----------|------------------------|
| D01 | ¿Factory **fuera** de cada ventana (app aparte)? | **SÍ** |
| D02 | ¿Producto = HTML sin secretos + kernel local? | **SÍ** |
| D03 | ¿Nube solo a través del kernel, nunca `fetch` directo desde la ventana? | **SÍ** |
| D04 | ¿Tokens en OS keyring, no localStorage? | **SÍ** |
| D05 | ¿Host iframe + postMessage (micro-frontend)? | **SÍ** |
| D06 | ¿Tres carpetas: 01-original / 02-fromted / **03-producto** (lock)? | **SÍ** |
| D07 | ¿Usuario puede cambiar tema/letras, nunca endpoints? | **SÍ** |
| D08 | ¿Run sin wire = error visible, no fake? | **SÍ** |
| D09 | ¿Sandbox: iframe ahora, docker en kernel después? | **SÍ** |
| D10 | ¿Una nube por “destino” (agent-api, webhook) configurable en fábrica? | **SÍ** |
| D11 | ¿Siguiente ventana solo tras `OK` + lock RUN-01? | **SÍ** |
| D12 | ¿Fotos+handoff ya bastan para retomar? | **SÍ** (ya en git) |

Enlaces de patrón (no clonar): micro-frontends + postMessage, iframe plugins (Tolgee/Shopware/Figma), local-first, Tauri keyring.
