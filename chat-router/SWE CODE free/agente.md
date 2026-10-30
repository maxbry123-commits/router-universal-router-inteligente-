# Agente SWEN CODE free — instrucciones nativas

El agente/modelo que usa este sistema sabe hacer esto sin depender del usuario.
Manual completo compartido por los 2 chats: `INSTRUCCIONES.md`.

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

Modelo: `concilio` = los 3 web; nombre (`deepseek v4`, `qwen 3.7`, `qwen 3.8`, `liquid`, `qwen code`) = UN solo modelo; sin nombre → consulta=concilio, resto=qwen38max.
Paralelo: `chat <id>`/`seccion <id>` = conv_id propio (tab aparte, hilo separado). Un modelo puede clonarse a otro conv_id/slot (espejo).

Forma: `SWEN CODE free modo <modo> [con|solo|modelo <nombre>] [chat <id>] <texto>`.

## 2. Reiniciar y recuperar la sesión
- `SESSION_EXPIRED` → `POST {WEB_BRIDGE_URL}/refresh_session` (re-login solo; rota correo si la cuenta murió).
- Página reiniciada a media tarea → reenviar el MISMO `conv_id` (`checkpoint.json` retoma).
- Space dormido → reintentar (scale-to-zero despierta solo, ~1-3 min).
- Todo el puente cae → cadena → modelos locales `model=` en S1/S2/S3 → puente-movil (APK último).

## 3. Trabajo en paralelo y espejo
- 2 secciones: `chat 1` y `chat 2` corren por separado al mismo tiempo (tab web propia cada una).
- Pipeline CODE: liquid 1 recibe y delega → liquid 2 despliega; liquid 1 sigue trabajando en paralelo, no para (espejo). qwen-coder solo entra si aparece `[GAP]` y hay refactoría que hacer (costo/token).
- Pipeline FREE: qwen da instrucciones → swe-agente → otro lfm2.5 despliega (sin refactor).
- Espejo: clonarte a otro conv_id para dividir el trabajo — mismo modelo, contexto aparte.

## 4. Crear archivos markdown cuando haga falta
La salida larga/archivos se materializa en `salidas/` del bridge (o del repo): un `.md` por entregable, nombre `AAAAMMDD-<modo>-<tema>.md`.

## 5. Desoligar, escribir, transcribir el code y desplegar en GitHub
El modelo: lee la salida web, la transcribe a código limpio, la organiza en archivos del repo, commit + push a `main` (mensaje con prefijo del modo). El agente nunca deja el resultado solo en el chat web.
