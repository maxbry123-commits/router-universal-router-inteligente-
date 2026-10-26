# Pruebas que faltan — solo con las herramientas MCP (Sol, GPT, Grok)

Sin HTTP directo al Space (DNS/403): todo se hace con las herramientas del conector `riu-router-github`. Resultado real de Sol (24-oct): 10/12 PASS (Qwen 3.8 Max y GLM 5.3, tareas t1–t6, t4 bloqueada).

## 0. Antes de empezar (1 llamada)
Llamar a `salud`: debe traer `commit` = el último de `main` y `permisos`. **t4 (delegar con `llm`) solo pasa con `permisos.ia = true`.**
Esos permisos los enciende el Director en el chat (chip **IA ON** / **Agentes ON**); un modelo o una prueba no se los puede dar a sí misma. Si `ia=false`, t4 devuelve `HTTP 403: ia=false` (la causa ya viaja en el error): pedir al Director que pulse IA ON y repetir solo t4.

## 1. Las llamadas exactas de cada tarea (sin Python)
`python3 -m mvp.pruebas_vivo.guion --modelos glm-5.3 --pruebas t1,t2,t3,t4,t5,t6` imprime, por modelo, el JSON de cada `chat` (mensaje, `request_id`, `tools`, `llm_tool`) y la llamada de comprobación (`github_leer`, `almacen leer`, `pendientes listar`…). Se ejecuta en cualquier máquina con Python, sin red ni clave. Después de cada `chat`: `resultado` con su `proceso_id` hasta `estado=completado`.
PASS solo si la comprobación lee de verdad lo que el modelo dijo haber escrito (no basta con su respuesta).

## 2. Qué falta (nada de esto está probado todavía)
| # | Prueba | Quién | Cómo |
|---|---|---|---|
| 1 | t4 con IA ON (Qwen 3.8 Max y GLM 5.3) | quien tenga el Director al lado | punto 0 + `guion --pruebas t4` |
| 2 | t1–t6 en los otros 10 modelos de texto: `qwen3.8-flash`, `qwen3.7-max`, `qwen3.7-plus`, `qwen3.6-flash`, `glm-5.2`, `deepseek-v4-pro`, `deepseek-v4-pro-0813`, `deepseek-v4-flash-0731`, `deepseek-v4.1-flash`, `deepseek-v4.1-flash-1017` | repartir: Sol 1–4, GPT 5–7, Grok 8–10 | `guion --modelos <ids>` |
| 3 | Nombre antiguo: `chat` con `modelo:"ficha-qwen38max"` debe responder (antes: «modelo no permitido») | cualquiera | 1 llamada + `resultado` |
| 4 | Groq y NVIDIA: `salud` → `proveedores_externos`; si es `true`, `chat` con `modelo:"groq/llama-3.3-70b-versatile"` | Grok | si es `false` el Space no tiene `GROQ_API_KEY`/`NVIDIA_API_KEY`: avisar al Director |
| 5 | Medios: imagen (`qwen-image-3.0-pro`), voz (`qwen-audio-3.0-tts-plus`), ASR, video (`wan3.0-video`) con `chat` y su modelo | GPT | el resultado trae `[[imagen:URL]]`/`[[video:URL]]`/`[[audio:URL]]`; abrir la URL |
| 6 | Alcance: tras t6, `pendientes listar` no debe tener cambios que no pidió esa tarea (Qwen marcó `tarea3-…` sin que se lo pidieran) | Sol | comparar la lista antes y después |
| 7 | Limpieza | quien termine | borrar `Prueba/<modelo>/…` solo de tus modelos |

## 3. Qué entregar
Una tabla `modelo | prueba | PASS/FAIL | commit o proceso_id | evidencia (lo leído, no lo dicho)`. Un FAIL con su error exacto vale más que un PASS sin comprobar. No modificar secretos ni configuración del Router.
