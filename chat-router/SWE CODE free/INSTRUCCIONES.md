# INSTRUCCIONES — SWE CODE / SWE CODE free

> Manual único para modelos y agentes. **La misma instrucción sirve a los 2 chats**
> (chat Riu y chat OpenClaw): viaja por `plugins → deepseek_harness → HTTP router`.

## 1. Activación

- Todo mensaje empieza con `SWE CODE free` → `activar.js` saca modo + modelo + chat.
- SWE CODE (cascada codex→opencode→swe-agent→openhands) corre por ficha/motor; no lleva prefijo.
- En HF solo vive el **código mínimo** (arranque/serving); manuales y lógica están en GitHub.

## 2. Elegir modelo

| Lo que dices | Qué sale |
|---|---|
| `concilio`, `cóncil`, `consenso`, `todos`, `los 3` | fan-out: dsv4-flash + qwen37max + qwen38max → síntesis qwen38max |
| `deepseek`, `dsv4`, `deepseek v4` | `web-dsv4-flash` (solo ese modelo) |
| `qwen 3.7`, `qwen 3.7 max` | `web-qwen37max` |
| `qwen 3.8`, `qwen 3.8 max` | `web-qwen38max` |
| `liquid`, `lfm`, `lfm2.5` | `lfm2.5-350m` (cola local S1/S2/S3) |
| `coder`, `qwen code`, `qwen2.5` | `qwen2.5-coder-1.5b` (cola local) |

- Prefijos aceptados: `con`, `solo`, `modelo`, o el nombre como primera palabra.
- Sin nombre: `consulta` → concilio; otros modos → `web-qwen38max` único.
- Tarea individual con un solo modelo = modo + nombre: `SWEN CODE free modo solucion solo deepseek v4 <tarea>`.

## 3. Modos

`revision` · `solucion` · `arquitectura` · `archivos` · `prompt_code` · `consulta` · `despliega`
(`despliega`: aplica lo que te entregan y verifica; en FREE no refactorizas.)

## 3b. Pipeline ejecutable

`SWEN CODE free pipeline [code|free|auto] <tarea>`:
- `code` → anota lfm2.5 → qwen-coder organiza+refactor → otro lfm2.5 despliega.
- `free` (default) → qwen instruye → swe-agente → otro lfm2.5 despliega. Sin refactor.
- Ejecutor: `mini_router.py --pipeline code|free "<tarea>"` (cascada.json → pipelines).

## 4. Trabajo en paralelo

- `chat <id>` / `seccion <id>` / `conv <id>` → `conv_id` propio: web/tab aparte, hilo separado.
- **2 secciones trabajan por separado al mismo tiempo** — divide la tarea en 2 mensajes con `chat 1` y `chat 2`.
- Capacidad: `BRIDGE_MAX_TABS=4` tabs por sitio; encolado si se llena.
- **Espejo**: un modelo se clona a otro conv_id/slot (mismo modelo, contexto aparte) para repartirse el trabajo — igual que el mirror de agentes.

## 5. Pipelines

- **CODE (refactor incluido)**: anota `lfm2.5-350m` (rápido) → pasa info a `qwen2.5-coder-1.5b` (organiza + refactoriza) → otro `lfm2.5-350m` despliega.
- **FREE (solo despliegue)**: `qwen` da las instrucciones → `swe-agente` → otro `lfm2.5-350m` despliega. Sin refactor.

## 6. Conectividad (única vía)

```
chat → plugins → deepseek_harness → HTTP router → plugins → harness → respuesta
```

- Nada habla directo al router ni al chat: todo pasa por el harness.
- Modelos locales: `POST {SWECODE_URL_S1..S3}/v1/chat/completions` con `model=` (slots intercambiables, GGUF bajo demanda desde dataset swe-code-hf-gguf, 1 vivo por Space, unload 5 min idle).
- Modelos web: `POST {WEB_BRIDGE_URL}/v1/chat/completions` con `model=web-*` o `swecode-<modo>`.
  - Fallback automático dentro de la web: modelo pedido cae → `qwen38max→qwen37max→dsv4-flash` antes de escalar.
  - Respuesta trae `modelo_usado` (body + header `x-modelo-usado`) = el que respondió de verdad.
  - `GET {WEB_BRIDGE_URL}/v1/queue` = tabs abiertas por sitio + conv_ids + cola + cuentas.
- Móvil: `POST {PUENTE_MOVIL_URL}/mcp` → tools sobre Chrome del teléfono.

## 7. Recuperar

| Fallo | Acción |
|---|---|
| `SESSION_EXPIRED` | `POST {WEB_BRIDGE_URL}/refresh_session` (re-login solo; rota correo si la cuenta murió) |
| Página reiniciada a media tarea | Reenviar el MISMO `conv_id` — `checkpoint.json` retoma solo |
| Space dormido | Reintentar: scale-to-zero despierta solo (~1-3 min) |
| Todo web cae | Cadena → modelos locales S1/S2/S3 (`model=`) → APK móvil |
| `INPUT_NO_ENCONTRADO`/`SELECTOR_BROKEN` | Marcar SELECTOR_BROKEN + sitio; no reintentar a ciegas |

## 8. Reparar cableado

Señal de pieza desconectada (chat no responde / modo no existe):

1. `chat-router/plugins/<nombre>` debe ser symlink → `../<raiz>` (swe_code → SWE CODE; swen_code_free → SWE CODE free).
2. La raíz debe tener `ficha.json` (plugin_host/v1).
3. `cableado.manifest.json` debe listar el enlace en `enlaces` y la pieza en `plugins`.
4. **Nada dentro de `protegido` se toca** (sha256 verificado).
5. Rutas: `SWE CODE/web-bridge/` = edificio 1 (router temporal HF); `SWE CODE free/` = edificio 2 (OpenClaw mirror + APK + puente).

## 9. Reglas del agente

- Salida larga → `.md`/`code` en `salidas/` y a GitHub; nunca se queda solo en el chat web.
- Un paso FAIL → cascada para y devuelve recibo del paso que cayó.
- Sin PASS sin evidencia real.
