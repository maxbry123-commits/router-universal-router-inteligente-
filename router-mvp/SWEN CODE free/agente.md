# Agente SWEN CODE free — instrucciones nativas

El agente/modelo que usa este sistema sabe hacer 4 cosas sin depender del usuario:

## 1. Activar el modo según el caso
Todo mensaje del sistema empieza con `SWEN CODE free`. Elegir modo:

| Si el pedido es... | Modo |
|---|---|
| mirar/criticar un código o plan | `revision` |
| resolver un gap, bug o problema | `solucion` |
| diseñar estructura de programa | `arquitectura` |
| convertir documentos/archivos de proyecto en código | `archivos` |
| pedir un prompt de código completo | `prompt_code` |
| preguntar/consultar un plan (fan-out DSv4-flash + Qwen3.7Max + Qwen3.8Max, síntesis Qwen3.8Max) | `consulta` |

Forma: `SWEN CODE free modo <modo> <texto>`.

## 2. Reiniciar y recuperar la sesión
- Si el web-bridge devuelve `SESSION_EXPIRED`: llamar `POST {WEB_BRIDGE_URL}/refresh_session` (re-login solo; rota correo si la cuenta murió).
- Si la página se reinicia a media tarea: el bridge retoma desde `checkpoint.json` con la resume-card — reenviar el MISMO `conv_id`, no empezar de cero.
- Si el Space está dormido: primer request lo despierta (scale-to-zero, ~1-3 min); reintentar, no abortar.
- Si todo el puente cae: cadena → modelos locales `model=` en S1/S2/S3 → puente-movil (APK último).

## 3. Crear archivos markdown cuando haga falta
La salida larga/archivos se materializa en `salidas/` del bridge (o del repo): un `.md` por entregable, nombre `AAAAMMDD-<modo>-<tema>.md`.

## 4. Desoligar, escribir, transcribir el code y desplegar en GitHub
El modelo: lee la salida web, la transcribe a código limpio, la organiza en archivos del repo, commit + push a `main` (mensaje con prefijo del modo). El agente nunca deja el resultado solo en el chat web.
