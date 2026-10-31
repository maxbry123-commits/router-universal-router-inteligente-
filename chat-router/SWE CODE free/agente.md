# Agente SWEN CODE free — instrucciones nativas

Resumen de `INSTRUCCIONES.md` (manual completo para los 2 chats). Todo va por el web-bridge `:7870`, `POST /v1/chat/completions`.

## 1. Activar modo y modelo
Todo mensaje del sistema empieza con `SWEN CODE free`. Elegir modo:

| Si el pedido es... | Modo |
|---|---|
| mirar/criticar un código o plan | `revision` |
| resolver un gap, bug o problema | `solucion` |
| diseñar estructura de programa | `arquitectura` |
| convertir documentos/archivos en código | `archivos` |
| pedir un prompt de código completo | `prompt_code` |
| preguntar/consultar un plan (concilio de 3 + síntesis) | `consulta` |
| aplicar y verificar lo que te entregan | `despliega` |
| planear antes de ejecutar (plan, mapa mental, estructura, cómo resolver problemas; no ejecuta) | `asesoria` |

Modelo: `concilio` = los 3 web (`swecode-consulta`); nombre (`deepseek v4` → `web-dsv4-flash`, `qwen 3.7` → `web-qwen37max`, `qwen 3.8` → `web-qwen38max`, `liquid` → `lfm2.5-350m`, `qwen code` → `qwen2.5-coder-1.5b`, `groq`, `nvidia`) = UN solo modelo; sin nombre → consulta=concilio, resto=`qwen38max`.

Forma: `SWEN CODE free modo <modo> [con|solo|modelo <nombre>] [chat <id>] [doc <ruta>] <texto>`.
POST: `model`, `messages`, `conv_id`, `proyecto`, `cuentas`, `clave`, `documentos` (+ `modo` solo con `web-*`; con `swecode-<modo>` el modo va en el id) y, según el caso: `stream:true` (SSE real), `ejecutor_tools` (`swe`|`openclaw`: quién ejecuta los `tool_calls`), `claves` (`{groq, nvidia}`, solo con clave de acceso), `tools`/`tool_choice`, `tarea_id`/`x-tarea-id` (normalmente lo deriva el bridge de `conv_id`; no lo inventes), `respaldo:true`.

## 1b. Autenticación (siempre)
Toda ruta salvo `GET /health` exige `x-api-key` con una de las 4 claves de acceso (`RIU_API_KEY`, `RIU_PUBLIC_CHAT_KEY`, `RIU_MCP_KEY`, `RIU_ROUTER_API_KEY`) o `BRIDGE_TOKEN` (`Authorization: Bearer`). Sin ella: 401 `NO_AUTORIZADO`; bridge sin clave configurada: 503 `SIN_CLAVE_DE_ACCESO`. `/v1/swe/*` exige `BRIDGE_TOKEN` y `aprobar` además `BRIDGE_OPERATOR_TOKEN` (`x-operator-token`) + `x-operador`. Los valores reales salen del entorno; jamás los escribas en archivos, prompts ni commits.

## 2. Reiniciar y recuperar la sesión
- `SESSION_EXPIRED` → el bridge ya reintenta una vez; si persiste `POST {WEB_BRIDGE_URL}/refresh_session`.
- Página reiniciada a media tarea → reenviar el MISMO `conv_id` y el mismo texto (`checkpoints/<conv_id>.json` retoma), o `POST /v1/secciones/<conv_id>/retomar` sin reenviar nada; `GET /v1/secciones` lista las que están a medias. Al arrancar, el bridge retoma solo las pendientes (`BRIDGE_AUTORETOMAR`, activo por defecto).
- Modelos `groq/…`, `nvidia/…` o locales: checkpoint por tarea (`tarea_id` derivado); respuesta cortada por `finish_reason=length` o API caída (429/402/timeout) → el bridge continúa y cambia de clave/API solo, sin repetir texto. Para ver el estado: `GET /health` (`metricas` con TTFT y tokens/s por modelo) y `GET /v1/modelos/disponibilidad`.
- Space dormido → reintentar (despierta solo, ~1-3 min).
- La web cae → el bridge responde con el respaldo, en este orden: Groq → NVIDIA → HF local (S1/S2/S3). Mira `via_respaldo` y `aviso`. El APK móvil (`puente-movil`) es último recurso manual: el bridge no lo llama.
- `aviso: CUENTAS_FALTAN` → reenviar `cuentas` y `clave` en el POST.

## 3. Asesoría y trabajo en paralelo
- Antes de ejecutar un proyecto: `swecode-asesoria` con `proyecto`. Queda en `ASESORIA.md`; léela con `GET /v1/proyectos` y `GET /v1/proyectos/<proyecto>`.
- 2 secciones: `chat 1` y `chat 2` (conv_id `chat-1`, `chat-2`) corren por separado a la vez, cada una con su tab web.
- Espejo: mismo modelo en otro `conv_id` (contexto aparte) para dividir el trabajo.

## 4. Crear archivos markdown cuando haga falta
La salida larga se materializa en `salidas/` del repo: un `.md` por entregable, nombre `AAAAMMDD-<modo>-<tema>.md`.

## 5. Desoligar, escribir, transcribir el code y desplegar en GitHub
Documentos: `doc <ruta>` / campo `documentos` del POST → se incrustan al prompt (máx 100 000 caracteres c/u).

El modelo lee la salida web, la transcribe a código limpio, la organiza en archivos del repo, commit + push a `main` (mensaje con prefijo del modo). El agente nunca deja el resultado solo en el chat web.
