# Prompt para Grok Bot / Sol GPT — Settings del Space y Deploy Hook de Vercel

Copia desde la línea de abajo hasta el final y pégalo tal cual. No lleva ningún valor real: los secretos los pegas tú, nunca el bot.

---

Eres mi guía. Explícame PASO A PASO, en español sencillo y de uno en uno (espera mi "listo" antes del siguiente), cómo hacer lo siguiente. No inventes pasos que no estén aquí; si algo de mi pantalla no coincide, dímelo y párate. Nunca me pidas ni repitas claves, tokens ni hashes: yo los pego directamente en el campo. Si el chat te los muestra, no los copies a ningún otro sitio.

Contexto: el Space se llama COMAND-CENTER-1/riu-router (https://comand-center-1-riu-router.hf.space). Ya había ejecutado en mi computadora `bash chat-router/DEPLOY/generar-aprobadores.sh <mi-operador>`; el script imprimió el token de cada operador (una sola vez, lo guardé en mi gestor de secretos) y tres líneas: `RIU_SWE_APROBADORES=...`, `BRIDGE_APROBADORES=...` y `RIU_SWE_OPERADORES=...`. De esas tres solo uso la parte que va DESPUÉS del `=` de las dos primeras (la línea de operador:hash); `RIU_SWE_OPERADORES` ya no hace falta.

PARTE A — Settings del Space en Hugging Face
1. Abrir https://huggingface.co/spaces/COMAND-CENTER-1/riu-router/settings e ir a la sección "Variables and secrets".
2. (a) Pulsar "New secret" y crear el secreto `BRIDGE_APROBADORES`. En el valor: pega aquí la línea que te dio el script (solo lo que va después del `=`). Guardar.
3. Pulsar "New secret" otra vez y crear `RIU_SWE_APROBADORES` con EL MISMO valor (pega aquí la línea que te dio el script). Guardar. Los dos deben quedar idénticos.
4. (b) Confirmar que en la misma lista ya existen los secretos `RIU_API_KEY` y `GITHUB_TOKEN` (solo comprobar que aparecen por nombre; no abrir ni copiar su valor). Si falta alguno, avísame y párate: no se inventa.
5. No hace falta crear `BRIDGE_TOKEN`, `SWECODE_URL_S1`, `SWECODE_URL_S2`, `SWECODE_URL_S3`, `RIU_DEEPSEEK_HARNESS_URL` (si el Harness está en este mismo Space), `RIU_SWE_WORKSPACE_RAIZ`, `RIU_SWE_OPERADORES` ni `BRIDGE_EXIGIR_CONFIRMACION`: tienen valor por defecto.
6. Esperar a que el Space se reinicie tras guardar los secretos (si no lo hace solo, usar la opción de reiniciar del panel del Space, "Restart"/"Factory reboot") y a que el estado diga "Running".
7. (c) Verificar el código desplegado: abrir https://comand-center-1-riu-router.hf.space/health. Debe mostrar `"status":"ok"` y un `commit` de 10 caracteres. Compararlo con el inicio del último commit de la rama `main` del repositorio (los primeros 10 caracteres del SHA). Si coincide, el código está al día; si no, el autopull tarda hasta 60 s: reintentar tras un minuto.
8. Verificar el estado del bridge: abrir `https://comand-center-1-riu-router.hf.space/web/health` (esta ruta pide la clave de acceso en la cabecera `X-API-Key`; hazlo yo desde mi terminal con mi propia clave, sin pegarla en este chat). Debe responder con `ok`, `pool`, `respaldo` (groq, nvidia, hf_local) y `banco`. Esa ruta no devuelve el commit: el SHA se mira solo en `/health`.

PARTE B — Solo si el Harness corre en un Space SEPARADO (si está en este mismo Space, saltar esta parte)
9. En los Settings del Space del Router añadir la variable `RIU_DEEPSEEK_HARNESS_URL` con la URL pública del Space del Harness (empieza por https://). Este Space es el que la usa.
10. En los Settings del Space del Harness, confirmar que existen `GITHUB_TOKEN` y `RIU_API_KEY` (la misma clave de acceso) y añadir `RIU_SWE_APROBADORES` con el mismo valor de antes (pega aquí la línea que te dio el script) para que reconozca a los operadores.
11. El Harness NO tiene autopull: debo reiniciarlo una vez (panel del Space → Restart o Factory reboot) para que cargue el código nuevo de `main`. Al terminar, su log muestra una línea `HEAD=<sha>`; comprobar que es el de `main`.
11b. IMPORTANTE — los agentes (OpenClaw, SWE-agent, OpenHands, OpenCode, Codex, Claude Code) hoy salen "NO INSTALADO" en el selector porque el Space del Harness
   todavía no tiene la imagen reconstruida con el Dockerfile nuevo (trae Node 22 + instala los agentes en el build). Un "Restart" simple NO basta si el Space
   reutiliza la imagen ya construida: hace falta forzar una reconstrucción completa. Pasos:
   a) Panel del Space del Harness → menú (⋮, arriba a la derecha) → "Factory reboot". Si ese botón no fuerza un build nuevo (puede reusar cache), usar en su
      lugar: Settings → hacer scroll hasta abajo → "Rebuild" (o, si no aparece, un commit/push vacío al repo del Space, o "Restart this Space" seguido de
      "Factory reboot" otra vez).
   b) Confirmar que el secreto `GITHUB_TOKEN` existe en el Space del Harness ANTES de reconstruir (el build lo usa para clonar el repo privado e instalar los
      agentes; sin él, el build sigue funcionando pero los agentes quedan pendientes para el arranque, que es más lento y puede no terminar a tiempo).
   c) Esperar a que el estado diga "Running" otra vez (puede tardar varios minutos, instala Node + 5 paquetes npm + un entorno Python).
   d) Verificar en los logs del Space (pestaña "Logs" del panel) que aparece la línea de `instalar-agentes.sh` / `verificar-agentes.sh` sin errores graves.
   e) Volver al chat, abrir el selector de agentes y pulsar "Actualizar disponibilidad": ya no debe decir NO INSTALADO para los agentes cuyo binario se instaló
      (puede seguir diciendo NO CONFIGURADO si falta un token/URL de pasarela propio de ese agente — eso es otro tema, no de instalación).

PARTE C — Crear el Deploy Hook de Vercel (opcional; sirve para desplegar el frontend a mano)
12. Entrar en https://vercel.com, abrir el proyecto `riu-jev-bridge` y ir a Settings → Git → "Deploy Hooks".
13. Poner un nombre (por ejemplo `main`), elegir la rama `main` y pulsar "Create Hook". Vercel muestra una URL: es secreta.
14. Pegar esa URL SOLO como variable de entorno en la terminal desde la que ejecuto el script de despliegue: `export VERCEL_DEPLOY_HOOK='<la URL del hook>'`, y luego `bash chat-router/DEPLOY/deploy-unificado.sh` (simulacro) o con `--ejecutar`. No guardarla en ningún archivo del repo, no commitearla y no pegarla en este chat.
15. Comprobación: tras desplegar, https://riu-jev-bridge.vercel.app/version.json debe mostrar el `commit` de `main`.

Al final dime en una lista corta qué pasos quedaron hechos y cuáles pendientes.
