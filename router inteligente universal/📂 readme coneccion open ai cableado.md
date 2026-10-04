# 📂 readme coneccion open ai cableado

Fecha: 2026-10-04. Autor de las instrucciones: Hy (el Director). Este archivo anota **1 a 1** lo que el Director dijo y pegó sobre la conexión del plan de ChatGPT al Router, más el handoff y el estado real del Router. Los textos del Director van **tal cual** (sección A). Lo que hizo Claude va aparte (sección B) y no se mezcla.

Reglas que no cambian: ningún token ni clave va en el repo, en commits ni en el chat; todo va en el banco del Router; sin GitHub Actions; Vercel es solo puente; el cómputo corre en Hugging Face.

---

## A. Instrucciones del Director, tal cual

### A1. Pedido inicial
> Añade esto a la raíz de Router inteligente universal lo descargas haces el puente con en router para darle servicio de el plan de chat gpt luego lo colocas binario con la clave del banco o lo metes en el mismo banco
>
> Luego lo integras a el router con 30 secciones  para tener el Serviciones diferentes con caché y que rota
>
> Monta los motores de descarga y extracción de main y vas descargado y añades el code que falte mvp y lo metes en el banco conectado al router

Después subió las secciones de 30 a **50** ("Súbelo a 50 secciones") y pidió que el puente quede **en GitHub** (código) y que el cómputo se pida en Hugging Face para operar por el Router.

### A2. Corrección sobre cómo conectar (mensaje del Director, 2026-10-04 03:28)

> Sí: para tu app personal, la forma simple es la de app open-source/local. No necesitas meterte en client_id web, partner program ni callback HTTPS de Hugging Face.
>
> Hazlo así: TU CÓDIGO EN GITHUB → @siwc/local → chatgpt.signIn() → OpenAI abre el login → tú autorizas tu cuenta Pro UNA VEZ → sesión protegida → getSession() → listModels() → streamResponse() → tus 30 proyectos.
>
> OpenAI confirma que para apps open-source/locales el flujo registra automáticamente el cliente OAuth y permite a usuarios elegibles Plus/Pro usar su plan sin proporcionar API key.
>
> El código conceptual mínimo es:
>
> ```js
> import { createChatGPT } from "@siwc/local";
>
> const chatgpt = createChatGPT({
>   appName: "YAIWES",
>   appId: "yaiwes",
>   sendHostId: true,
> });
>
> // Primera vez: abre OpenAI y tú autorizas.
> await chatgpt.signIn();
>
> // Después:
> const session = await chatgpt.getSession();
>
> if (session.sharing) {
>   const models = await chatgpt.listModels();
>
>   const result = await chatgpt.streamResponse({
>     model: models[0].slug,
>     input: "Prueba YAIWES"
>   });
>
>   console.log(result.text);
> }
> ```
>
> OpenAI usa precisamente getSession(), listModels() y streamResponse() en su ejemplo oficial para verificar que una app está usando el plan ChatGPT.
>
> Para tus 30 proyectos: UNA AUTENTICACIÓN CHATGPT PRO → AUTH MANAGER → PROJECT ROUTER → P01, P02 ... P30.
>
> No haces 30 logins. Todos tus proyectos pueden pasar por el mismo AuthManager mientras mantienes separado el historial, memoria, instrucciones y modelo de cada proyecto.
>
> Lo único que no puede hacer puro código por ti es la primera autorización de tu cuenta. OpenAI requiere que tú autentiques y des consentimiento. Después, el SDK conserva la sesión/registro y puede reutilizarla y renovarla.
>
> Página oficial que corresponde exactamente a tu caso: https://developers.openai.com/siwc/token-sharing-open-source
>
> Ejemplo oficial completo: https://developers.openai.com/cookbook/articles/sign-in-with-chatgpt
>
> Eso es lo que debe implementar Claude: open-source/local SIWC, no inventar un flujo web remoto.
>
> haces una mini app solo con los botones
>
> Dime si te quedo claro para que no vuelvas a alucinar ?
>
> Sí, puede renovarse automáticamente, pero la conexión no debe "mandarse a GitHub" como tokens o sesión. GitHub guarda el código; la sesión debe ir al runtime donde realmente corre tu Router. OpenAI dice que los tokens no deben ir a source control, logs ni URLs.
>
> Tu arquitectura correcta es: APK LOCAL EN TU MÓVIL → Sign in with ChatGPT → OAuth aprobado → credencial SIWC protegida → transferencia segura → RUNTIME donde corre YAIWES/Router → Router usa Responses API. GITHUB solo guarda el código del Router.
>
> Si tu Router se ejecuta después en una VM, contenedor o servidor que carga el código desde GitHub, a ese runtime se le entrega la credencial protegida. OpenAI tiene una guía específica para esto: completar OAuth localmente, transferir las credenciales protegidas al host remoto y conservar el ext_agent_host_id propio de ese host.
>
> Renovación automática. Sí. Es exactamente como debe programarse. Cuando autorizas por primera vez, con offline_access, OpenAI entrega: access_token, refresh_token, client_id, id_token, expires_in.
>
> El access_token dura 1 hora. El refresh_token dura 30 días, y cada renovación correcta devuelve un access token nuevo y un refresh token nuevo con otros 30 días. No hay un número fijo de renovaciones mientras cada refresh siga siendo válido.
>
> Tu Router hace automáticamente: REQUEST → ¿access_token sigue válido? SÍ → llamar OpenAI. NO / próximo a vencer → refresh_token → OpenAI OAuth → access_token NUEVO y refresh_token NUEVO → guardar ambos protegidos → continuar.
>
> La llamada oficial de renovación es conceptualmente:
>
> ```js
> async function refreshOpenAISession(session) {
>   const body = new URLSearchParams({
>     grant_type: "refresh_token",
>     client_id: session.client_id,
>     refresh_token: session.refresh_token,
>     resource: "https://api.openai.com/v1",
>   });
>
>   const response = await fetch(
>     "https://auth.openai.com/api/accounts/oauth/token",
>     {
>       method: "POST",
>       headers: {
>         "content-type": "application/x-www-form-urlencoded",
>       },
>       body,
>     }
>   );
>
>   if (!response.ok) {
>     throw new Error(`OAuth refresh failed: ${response.status}`);
>   }
>
>   const updated = await response.json();
>
>   // Sustituir ATÓMICAMENTE las credenciales anteriores.
>   await secureStore.save({
>     ...session,
>     access_token: updated.access_token,
>     refresh_token: updated.refresh_token,
>     id_token: updated.id_token ?? session.id_token,
>     expires_in: updated.expires_in,
>     saved_at: new Date().toISOString(),
>   });
>
>   return updated;
> }
> ```
>
> OpenAI especifica que debes usar el client_id emitido, no dynamic_agent_client, y que los refresh deben serializarse para evitar que dos procesos intenten reutilizar simultáneamente un refresh token rotativo.
>
> Entonces, para tu sistema. PRIMERA VEZ — TÚ: APK Android → Continue with ChatGPT → login Pro → Autorizar → listo. DESPUÉS — AUTOMÁTICO: Router arranca → carga sesión protegida → mira expiración → refresca cuando corresponde → guarda token nuevo → llama Responses API → continúa funcionando.
>
> Solo tendrás que volver a iniciar sesión si, por ejemplo, revocas el acceso desde ChatGPT, el refresh token llega a ser inválido/expira, o OpenAI exige una nueva autorización. Para esos errores OpenAI indica volver a OAuth usando el client_id que ya fue emitido.
>
> Y para tus 30 proyectos no necesitas 30 sesiones: 1 SESIÓN CHATGPT PRO → AUTH MANAGER → ROUTER YAIWES → P01 ─ P02 ─ P03 ─ ... ─ P30.
>
> GitHub contiene el código que sabe hacer todo esto; las credenciales nunca se suben al repo.
>
> Anota todo 1 a 1 en un readme llamado 📂 readme coneccion open ai cableado con el handoff y toda la información del router
>
> dime si te quedó claro para que no alucines ?

### A3. Qué significa "local" (adjunto 1)

> Localmente significa en la misma máquina donde corre tu programa y donde se abre el navegador. OpenAI exige que el callback vuelva a 127.0.0.1; el proceso local debe estar escuchando antes de abrir el login.
>
> Para hacerlo con la menor fricción posible, OpenAI ya dejó una aplicación de ejemplo completa: Paste Perfect. Pero ojo: el ejemplo oficial listo hoy es para macOS 14+, usa Electron/Node.js y no es una página HTML suelta ni una app Android lista.
>
> El proceso local real es: APP LOCAL EN TU DISPOSITIVO → [ Continue with ChatGPT ] → @siwc/local levanta http://127.0.0.1:PUERTO/auth/callback → abre navegador → OPENAI → inicias sesión con tu cuenta Pro → eliges workspace → autorizas uso del plan → el navegador vuelve a 127.0.0.1 → la APP LOCAL recibe la autorización → guarda sesión cifrada → CONNECTED.
>
> OpenAI explica que chatgpt.signIn() se ocupa de generar state, nonce, PKCE, levantar el listener local, abrir el navegador, recibir el client_id, intercambiar el código y verificar la identidad.
>
> El código central es aproximadamente:
>
> ```js
> import { createChatGPT } from "@siwc/local";
>
> const chatgpt = createChatGPT({
>   appName: "YAIWES",
>   appId: "yaiwes",
>   sendHostId: true,
>
>   // además necesitas un proveedor de cifrado local
>   credentialEncryption: encryptionProvider
> });
>
> async function conectar() {
>   const session = await chatgpt.signIn();
>
>   if (!session.sharing) {
>     throw new Error("No se autorizó el uso del plan ChatGPT");
>   }
>
>   console.log("CONECTADO");
> }
> ```
>
> Y tu botón simplemente llama: button.onclick = () => conectar();
>
> Después del primer login: const session = await chatgpt.getSession(); if (session.sharing) { const models = await chatgpt.listModels(); }
>
> Pero para tu teléfono Android. Aquí está el punto que antes te estaba explicando mal: OpenAI no publica actualmente una aplicación Android lista basada en este DevKit. El SDK oficial @siwc/local está pensado para un proceso Node.js local, y el ejemplo terminado de OpenAI es una aplicación Electron para macOS.
>
> Así que, sin Termux y sin PC, no puedes simplemente abrir un HTML en Chrome Android y ejecutar @siwc/local. El navegador por sí solo no proporciona el proceso Node local ni el almacenamiento cifrado requerido por el SDK.
>
> Tienes dos opciones reales: A — AHORA: usar una computadora/macOS → ejecutar app local → login una vez → obtener sesión protegida. B — PARA TU SISTEMA: crear una pequeña app local Android → botón Continue with ChatGPT → runtime local → callback 127.0.0.1 → sesión cifrada → luego conecta con YAIWES.
>
> OpenAI exige además que las credenciales se almacenen protegidas; @siwc/local no tiene fallback a texto plano, y otros runtimes distintos del ejemplo Electron deben proporcionar su propio cifrado respaldado por el sistema operativo.
>
> Por tanto, para tu caso sin Termux y trabajando desde Android, la solución limpia es hacer una mini app Android local únicamente para autenticación. Tendría literalmente: YAIWES — ChatGPT Pro / Estado: Desconectado / [ Continue with ChatGPT ] / [ Ver modelos ] / [ Desconectar ].
>
> Después de autorizar una vez, esa app puede conservar la sesión cifrada y renovarla; OpenAI documenta access tokens de una hora y refresh tokens rotativos de 30 días.
>
> Página oficial exacta: https://developers.openai.com/siwc/token-sharing-open-source/sign-in
> Ejemplo oficial completo: https://developers.openai.com/cookbook/articles/sign-in-with-chatgpt
> DevKit oficial: https://github.com/openai/sign-in-with-chatgpt-devkit
>
> Si tu objetivo es hacerlo desde tu Android sin Termux, entonces el siguiente diseño correcto es esa mini app local de autenticación; no necesitas construir todavía todo el frontend YAIWES.

### A4. La APK se compila fuera y se instala (adjunto 2)

> Sí. Esa es una opción válida de arquitectura, con una corrección: la APK puede construirla donde quieras —incluso usar Hugging Face solo como entorno de compilación—, pero la APK se ejecuta localmente en tu Android y ahí haces el primer Sign in with ChatGPT.
>
> Flujo: 1) Código fuente de la APK en GitHub. 2) Compilas la APK en HF / otro builder. 3) Descargas la APK en tu Android e instalas. 4) Abres la APK LOCALMENTE: [ Continue with ChatGPT ]. 5) OpenAI abre el navegador; entras con tu cuenta ChatGPT Pro y autorizas el uso del plan. 6) OAuth vuelve al runtime LOCAL; la APK valida la sesión y guarda las credenciales protegidas. 7) La APK queda autenticada; puede usar listModels + Responses API. 8) Después conecta con tu sistema YAIWES.
>
> OpenAI confirma que para el flujo open-source el cliente puede registrar dinámicamente la aplicación, no necesita client secret ni API key, y el primer login debe completarse localmente con su propio ext_agent_host_id.
>
> La parte que debes cambiar de tu idea. No sería: APK → autenticación → mandar tokens al Router "en GitHub". Porque GitHub almacena código; no ejecuta tu Router y tampoco deberías guardar los tokens OAuth en el repositorio.
>
> Sería: GITHUB (código fuente YAIWES) → ANDROID APK → AUTH MANAGER (sesión ChatGPT Pro cifrada) → PROJECT ROUTER → P01, P02 ... P30; y la APK → OpenAI Responses.
>
> Si posteriormente tienes un Router ejecutándose en un servidor: ANDROID → OAuth local → sesión protegida, más ROUTER REMOTO → código proveniente de GitHub. OpenAI documenta también cómo transferir una sesión SIWC ya autorizada a una VM self-hosted: se completa OAuth localmente y luego se transfiere la credencial protegida al runtime remoto, manteniendo un host_id distinto para esa máquina.
>
> Tu APK mínima: no necesitas construir toda YAIWES en la APK. Puede ser solamente: YAIWES AUTH / ChatGPT Pro / Estado: DESCONECTADO / [ Continue with ChatGPT ] / [ Verificar sesión ] / [ Ver modelos ] / Cuenta: -------. Por detrás cinco funciones: signIn(), getSession(), listModels(), refreshSession(), signOut(). Después del primer login: abrir APK → getSession() → sesión válida → CONNECTED automáticamente.
>
> Los access tokens duran una hora y, con offline_access, OpenAI entrega un refresh token para renovarlos; cada renovación exitosa entrega un reemplazo.
>
> Y esto es importante: la APK no debe enviar los tokens a GitHub. OpenAI indica que access_token, refresh_token e ID tokens deben mantenerse en almacenamiento local protegido o en el almacenamiento protegido del runtime self-hosted.
>
> Versión de mínima fricción: GitHub → código completo; HF → solo compilar APK si quieres; Android → descargar APK → abrir → Continue with ChatGPT → autorizar una vez. DESPUÉS → login automático → 30 proyectos → Responses API. Eso evita Termux completamente.
>
> Documentación oficial: https://developers.openai.com/siwc/token-sharing-open-source , https://developers.openai.com/siwc/token-sharing-open-source/sign-in , https://developers.openai.com/siwc/token-sharing-open-source/self-hosted-vms

### A5. La sesión vive en el banco privado de HF (adjunto 3)

> No tiene que vivir siempre en tu móvil. Tu móvil se necesita para el primer inicio de sesión/consentimiento. Después, OpenAI documenta expresamente que puedes transferir esa sesión protegida al runtime donde realmente corre tu Router, y desde ahí ese runtime puede encargarse de renovar los tokens.
>
> PRIMERA VEZ: APK / cliente local en tu móvil → Continue with ChatGPT → tu cuenta Pro → OAuth → sesión SIWC protegida → transferencia segura → RUNTIME DEL ROUTER → Banco secreto / secure storage.
>
> USO NORMAL: Router → Banco secreto → access_token → Responses API. Cuando está por vencer: refresh_token → OpenAI → access_token nuevo + refresh_token nuevo → Banco secreto actualizado → continúa funcionando.
>
> Sobre tu banco secreto: sí puede ser el lugar donde viva la autenticación, siempre que ese banco esté en el runtime privado y cifrado. Debe guardar, como mínimo: client_id, access_token, refresh_token, id_token, expires_in, scopes, saved_at, ext_agent_host_id del runtime.
>
> OpenAI indica que estos datos deben mantenerse en almacenamiento protegido local o del runtime self-hosted, y específicamente fuera de source control, logs y almacenamiento del navegador.
>
> Por tanto: Banco secreto ejecutándose con tu Router ✅. Archivo cifrado privado del runtime ✅. GitHub Secrets usados por un runtime, según tu arquitectura ✅. Archivo dentro del repositorio GitHub ❌. Commit con tokens cifrados o sin cifrar ❌.
>
> ¿Y GitHub? GITHUB → guarda el CÓDIGO que sabe autenticar/refrescar. RUNTIME DEL ROUTER → guarda LA SESIÓN REAL. Si dices "mi Router está en GitHub", técnicamente su código está en GitHub. Para hacer llamadas a OpenAI tiene que haber algún proceso ejecutando ese código.
>
> OpenAI permite que el mismo client_id autorizado se utilice en varios hosts del mismo usuario/workspace, pero cada host debe conservar su propio ext_agent_host_id.
>
> ¿Tendrás que volver al móvil cada hora? No. access_token: 1 hora. refresh_token: 30 días. Cada refresh exitoso devuelve otro refresh token con 30 días nuevos. No hay un número fijo de renovaciones mientras la cadena siga siendo válida.
>
> MÓVIL: solo primera autorización (o reautorización excepcional) → UNA VEZ → BANCO SECRETO DEL ROUTER → AUTO REFRESH → 30 PROYECTOS → OPENAI. Solo necesitarías volver a autenticar manualmente si la sesión es revocada, el refresh deja de ser válido o OpenAI requiere una nueva autorización.
>
> Páginas oficiales: https://developers.openai.com/siwc/token-sharing-open-source/self-hosted-vms y https://developers.openai.com/siwc/token-sharing-open-source/profiles-and-sessions
>
> Sí. Ese banco privado de claves en el almacenamiento privado de Hugging Face puede ser el lugar donde viva la sesión OAuth de OpenAI, siempre que esté cifrado y solo lo lea el runtime de tu Router.
>
> Flujo: MÓVIL (solo primera vez) → Sign in with ChatGPT → OAuth de tu cuenta Pro → sesión SIWC → transferencia segura → BANCO PRIVADO EN HF → Router YAIWES → Responses API → 30 proyectos.
>
> Registro parecido a:
>
> ```json
> {
>   "provider": "openai_chatgpt",
>   "client_id": "oaiapp_...",
>   "access_token": "<CIFRADO>",
>   "refresh_token": "<CIFRADO>",
>   "id_token": "<CIFRADO>",
>   "expires_at": "...",
>   "scope": "...",
>   "ext_agent_host_id": "..."
> }
> ```
>
> Nada de eso debe entrar al repositorio GitHub. Una vez importada la sesión en HF, HF puede encargarse de renovarla automáticamente. OpenAI dice que la VM debe ser dueña de los refresh posteriores y que debe conservar su propio ext_agent_host_id.
>
> Proceso automático: Router lee banco → ¿access_token válido? SÍ → usarlo. NO / próximo a vencer → usar refresh_token → OpenAI devuelve access_token NUEVO y refresh_token NUEVO → reemplazar ambos EN EL BANCO → continuar.
>
> Esto es especialmente importante: OpenAI usa refresh tokens rotativos. Cada refresh correcto devuelve uno nuevo, así que tu banco debe reemplazar el token anterior atómicamente y evitar que dos procesos refresquen la misma sesión a la vez.
>
> Así que para tu arquitectura, sí: banco privado HF = lugar adecuado para la sesión del Router. El móvil queda únicamente para la autorización inicial o para una reautorización excepcional si algún día OpenAI revoca/invalida la sesión.

### A6. Corrección anterior del Director (guía "Self-hosted VMs")

> NO HACER: NO interceptar ni falsificar callback OAuth. NO hacer creer a OpenAI que el login ocurrió en HF. NO copiar manualmente la URL final del navegador para simular el callback. NO utilizar API keys para este flujo. NO guardar access_token/refresh_token en texto plano. NO reutilizar el host ID del teléfono como host ID de la VM.
>
> FLUJO OFICIAL: 1) VM: crear UNA VEZ un `ext_agent_host_id` estable y guardarlo. 2) Dispositivo local: ejecutar el mismo cliente SIWC (primer registro con `client_id=dynamic_agent_client`). 3) Director inicia sesión con su cuenta ChatGPT Pro, elige workspace y autoriza. 4) Verificar que el scope concedido contiene `chatgpt.tokens.use.direct`. 5) El callback entrega el `client_id` emitido `oaiapp_...`; guardar ese, NO `dynamic_agent_client`. 6) Transferir el ARCHIVO DE CREDENCIALES PROTEGIDO del dispositivo a la VM por canal seguro; en la importación conservar el `ext_agent_host_id` ORIGINAL DE LA VM. 7) Las renovaciones las hace la VM con `grant_type=refresh_token` + client_id emitido + refresh_token + `resource=https://api.openai.com/v1`. 8) Inferencia por Responses API; sin API key ni client secret.
>
> 30 PROYECTOS: NO crear 30 OAuth. Una sesión alimenta el Router: AUTH MANAGER → PROJECT ROUTER → P01…P30. Cada proyecto separa instrucciones, historial, memoria, archivos, modelo, herramientas y estado.
>
> VARIAS CUENTAS: cada cuenta hace SU PROPIO Sign in with ChatGPT y tiene SU PROPIA sesión/perfil protegido. No mezclar tokens. No usar rotación de cuentas para eludir límites de uso.
>
> CRITERIO DE PRUEBA, PASS solo cuando: 1) OAuth completado oficialmente. 2) ID token validado. 3) client_id emitido guardado. 4) scope `chatgpt.tokens.use.direct` presente. 5) credenciales protegidas importadas en la VM. 6) Host ID de la VM conservado. 7) refresh funciona. 8) listModels funciona. 9) Responses API devuelve una respuesta real.

Fuentes oficiales citadas por el Director: https://developers.openai.com/siwc/token-sharing-open-source/self-hosted-vms , https://developers.openai.com/siwc/token-sharing-open-source , https://developers.openai.com/siwc/token-sharing-open-source/sign-in , https://developers.openai.com/siwc/token-sharing-open-source/profiles-and-sessions , https://developers.openai.com/siwc/quickstart , https://developers.openai.com/cookbook/articles/sign-in-with-chatgpt , https://github.com/openai/sign-in-with-chatgpt-devkit

Nota de fidelidad: los bloques A2 a A5 conservan las frases y el orden del Director; los esquemas de flechas verticales se pusieron en una línea con flechas → para no romper el formato. Ninguna instrucción fue cambiada.

---

## B. Lo que Claude entiende y hizo (aparte de lo del Director)

### B1. Resumen de lo que quedó claro (para no alucinar)
1. **Login local.** El inicio de sesión se completa en el dispositivo del Director (callback `127.0.0.1`), con el cliente oficial `@siwc/local`. No se falsifica, no se pega la URL del navegador, no se hace "como si" ocurriera en Hugging Face.
2. **Android sin Termux.** OpenAI no publica app Android. Se hace una **mini app local de autenticación** (APK) con los botones: Continue with ChatGPT, Verificar sesión, Ver modelos, Desconectar. La APK se compila en otro lado (GitHub guarda el código; Hugging Face puede ser el compilador) y se instala en el teléfono.
3. **La sesión no va a GitHub.** GitHub guarda solo el código. La sesión (client_id emitido, access_token, refresh_token, id_token, expires_in, scopes, saved_at, ext_agent_host_id de la VM) vive en el **banco privado del Router en el almacenamiento privado de Hugging Face**, cifrada.
4. **Renovación automática.** El Router, ya corriendo en Hugging Face, renueva solo: access_token dura 1 hora, refresh_token 30 días y rota en cada renovación. Los refresh se serializan y la sustitución en el banco es atómica.
5. **Una sesión, 50 secciones.** Un solo AuthManager; cada sección con su historial, memoria, instrucciones, modelo y herramientas. Varias cuentas solo si cada una hace su propio login, sin rotar cuentas para evitar límites.

### B2. Estado real del código (hay que cerrar diferencias)
Carpeta: `router inteligente universal/chatgpt-proyectos/` (6 archivos: `server.mjs`, `cifrado.mjs`, `login-local.mjs`, `preparar.sh`, `package.json`, `README.md`), subida a main desde el zip `chatgpt-proyectos.zip`.

Ya hace: 50 proyectos con estado aislado, ejecución en paralelo, caché corto, ruta `POST /perfiles/{perfil}/importar` que recibe la credencial protegida y conserva el `chatgpt-host.json` de la VM, cifrado AES-256-GCM con llave derivada de la clave del banco.

**Falta / difiere de lo que pide el Director (A5):**
- La sesión se guarda hoy en una carpeta de datos del puente, cifrada con la clave del banco. **Debe guardarse en el banco** del Router (registro `openai_chatgpt`).
- Falta la mini app Android (APK) con los botones. Hoy hay un script de línea de comandos (`login-local.mjs`) pensado para Termux; el Director no quiere Termux.
- Falta probar con una sesión real y cumplir el criterio PASS de A6 (9 puntos), incluida la verificación del scope `chatgpt.tokens.use.direct` y del `client_id` emitido.
- Riesgo técnico a resolver: `@siwc/local` es un proceso Node.js. Una APK necesita un runtime Node incluido o un puente equivalente; se decide al construirla.
- Límite documentado por OpenAI: todavía no hay atribución de uso ni revocación por host para sesiones transferidas; la revocación se hace desde la cuenta de ChatGPT.
- El kit de OpenAI tiene licencia no comercial: uso personal del Director.

### B3. Tareas siguientes, en orden
1. Terminar las fichas de modelos (orden del Director, 2026-10-04 03:33), tras una auditoría forense cruzando el chat con las notas de main.
2. Cambiar el almacenamiento de la sesión de ChatGPT al banco del Router (con bloqueo para que dos procesos no refresquen a la vez).
3. Construir la mini app Android y definir dónde se compila (Hugging Face), sin GitHub Actions.
4. Poner el puente a correr en Hugging Face por el Router; login una vez desde el teléfono; correr las 9 pruebas del criterio PASS.
5. Conectar las 50 secciones al selector del chat.

---

## C. Handoff y datos del Router

- **Repo:** `maxbry123-commits/router-universal-router-inteligente-` (principal `main`). Rama de trabajo del chat: `devin/1790824641-chat-agent-plan`. Motores: carpeta `Motores descarga extracción búsquedas`.
- **Puerta del Router:** `https://comand-center-1-claude-github-mcp-backup.hf.space`. El Router corre como Job de Hugging Face (último conocido: 6ac1b074). El paquete vive en el almacenamiento `COMAND-CENTER-1/yaiwes-memoria-storage`, bajo `router-inteligente-universal/codigo`. Se relanza escribiendo `control/router-desired.json` con `{flavor, relaunch_now: true}`.
- **Banco de claves:** archivo cifrado en `router-inteligente-universal/banco/` del mismo almacenamiento. Para abrirlo se necesitan **dos cosas**: un token de Hugging Face (entrar al almacenamiento) y la clave del banco (descifrar). Estado del banco: github 12, groq 6, nvidia 5, huggingface 4, router 1; las claves de OpenAI fueron borradas a petición del Director.
- **Acceso a GitHub:** por una máquina temporal de Vercel con el token pasado por `env` del comando, nunca dentro del texto; se apaga al terminar. Vercel es solo puente; no se deja nada ahí.
- **Fichas (Director):** ficha 0 infraestructura (cómputo, memoria, almacenamiento, con clave del Director); ficha 1 selector de un solo modelo (rota claves del mismo modelo, nunca cambia de modelo); ficha 2 consejo (DeepSeek V4, GLM 5, Groq Qwen 3.8; Kimi K3 decide; Groq Qwen ejecuta, con respaldo NVIDIA DeepSeek y luego Nemotron); fichas 3, 3.1 y 4 con modelo local en L4/T4. NVIDIA espera hasta 108 s.
- **Estado del código de fichas:** motor y laboratorio de modelos escritos y probados (31 pruebas pasan) pero **no subidos**; hay que reaplicarlos, subirlos y relanzar el Router.
- **Laboratorio de modelos:** responden Kimi K3, GLM 5.3, Nemotron 3.5 Lightning, Nemotron 3 Super, Nemotron 3 Ultra y Groq Qwen 3.8. No responden DeepSeek V4.1 Flash en NVIDIA, `hf:DeepSeek-V4-Pro` ni `nemotron-nano`. Reemplazos propuestos: Nemotron 3.5 Lightning (agéntico rápido) y Nemotron 3 Super (code).
- **Prioridad del Director:** poder probar el chat con los modelos y con el workflow.
- **Seguridad:** el Director pegó varios tokens en el chat el 2026-10-04; deben rotarse y guardarse solo en el banco.
