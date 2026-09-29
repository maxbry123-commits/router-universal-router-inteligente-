# INPUT BLOCK 08 — LOGINS, PRUEBA DE HF JOBS, OPERADOR WEB, PRECIOS DEEPSEEK Y PRIORIDAD DEL ROUTER — VERBATIM (2026-09-20)

Regla del Director: instrucciones textuales, 1 a 1. Los errores de tipeo son del original. Este mensaje no traía credenciales.
El mensaje incluyó 2 capturas de pantalla (no son texto): 1) la app de GitHub en el móvil con sesión iniciada como `abc1tienda-web` (perfil sin repositorios); 2) el perfil público de `planeta123-usa` (repositorio público `Agentes-`, "Joined last month"). De ahí salen los logins públicos de las cuentas B y C.
Análisis, pruebas y plan: `../bitácora stated JSON Craxy wall plan checkpoint router inteligente universal/RIU-0111-...md` y `../Readme arquitectura router inteligente universal/ADENDA-RIU-0111-...md`.

---INICIO DEL INPUT BLOCK (verbatim)---

En secreto de Github busca esas credenciales de las otras cuentas 


Esto no entiendo estás explicando supoer mal todo . 
Núcleo del Secret Bank: ?!??

Arranca prueba prueba latencia y arranque y costo 

MODELO APAGADO
      ↓
crear HF Job
      ↓
arrancar contenedor
      ↓
leer/montar pesos
      ↓
cargar RAM/VRAM
      ↓
arrancar vLLM
      ↓
READY
====================
      ↓
petición
      ↓
TTFT normal
      ↓
tokens

Una vez que el Job está caliente (READY), ya no deberías esperar varios minutos por cada respuesta. Los minutos corresponden principalmente al arranque inicial.
Hugging Face incluso señala que usando un repositorio montado mediante hf:// con llama.cpp, el servidor puede arrancar mucho más rápido porque no hay una descarga previa completa; el modelo se lee desde el repositorio montado mientras se carga.

Tu contrato del Registry debería distinguir COLD y HOT
Yo cambiaría esa parte del diseño a algo así:
MODEL REGISTRY

execution:
  mode: HF_JOB
  runtime: vllm | llama.cpp | sglang
  model_source: hf://ORG/MODEL

state:
  STOPPED
  STARTING
  LOADING
  READY
  BUSY
  FAILED

latency:
  cold_start_seconds: measured
  hot_ttft_ms: measured
  tokens_per_second: measured

billing:
  max_usd_per_session: X
  max_runtime_minutes: X
  idle_timeout_minutes: X

security:
  exposed_port: true
  auth: HF_TOKEN
Esto permite que tu router sepa:
modelo READY
→ llamada inmediata

modelo STOPPED
→ crear Job
→ esperar healthcheck
→ READY
→ ejecutar

modelo IDLE demasiado tiempo
→ cancelar Job
→ detener facturación

REQUEST
   ↓
¿PROVIDER DISPONIBLE?
   ├── SÍ → HF Inference Provider
   │
   └── NO
        ↓
     HF JOB
        ↓
  COST GUARD
        ↓
  START + LOAD
        ↓
      READY
        ↓
    INFERENCE
        ↓
   idle_timeout
        ↓
   CANCEL JOB
        ↓
  BILLING STOP


El router puede detectar actividad y arrancar el HF Job antes de que llegue la petición que realmente necesita el modelo. Esa es precisamente una buena forma de ocultar gran parte del cold start.
Por ejemplo:
USUARIO ABRE CHAT / LLEGA INPUT / EMPIEZA WORKFLOW
                    ↓
              ROUTER DETECTA
                    ↓
          ¿modelo probablemente necesario?
             ↓ SÍ             ↓ NO
      START HF JOB          continúa
             ↓
      STARTING / LOADING
             ↓
            READY
             ↓
       petición al modelo
Tu interfaz puede mandar algo tan pequeño como PREWARM(model_id) al router cuando el usuario abre una conversación, selecciona un modelo o empieza una tarea. También puedes aprovechar etapas que ya existen en tu flujo —por ejemplo investigación, clasificación o planificación— para arrancar el Job en paralelo. Así, mientras esas etapas trabajan, la GPU/CPU y el modelo se están cargando.

ACTIVITY DETECTOR
       ↓
MODEL PREDICTOR
       ↓
PREWARM
       ↓
HF JOB START
       ↓
HEALTHCHECK / READY
       ↓
REQUESTS
       ↓
IDLE 3-5 MIN
       ↓
CANCEL JOB

Y añadiría al registry state, job_id, ready_url, cold_start_ms, last_used_at, idle_timeout, hourly_cost y max_session_cost.



Instalar un operador web para que tú y los agentes puedan usar la web por mi incluso un agente especializado ejemplo pueda yo darle mi correo y mi contraseña de Github entra y abre la cuenta en el buscador como lo hago 

Procesó durante 12s

Sí. Solo uso DeepSeek V4.1 Flash, el modelo nuevo. No incluyo ningún V4 anterior.

Horarios pico de DeepSeek V4.1 Flash en Colombia

DeepSeek define dos ventanas pico de lunes a viernes en UTC. Convertidas a hora de Colombia (UTC−5) quedan:

Días en Colombia	Horario pico

Domingo a jueves	8:00 PM → 11:00 PM
Lunes a viernes	1:00 AM → 5:00 AM


Por tanto, para tu router:

COLOMBIA

🟥 PRECIO PICO
Domingo–jueves:  8:00 PM → 11:00 PM
Lunes–viernes:   1:00 AM → 5:00 AM

🟩 PRECIO ECONÓMICO
Todo el resto del tiempo

Solo DeepSeek V4.1 Flash nuevo

La API oficial de DeepSeek tiene esta estructura de precio que verificamos:

Ruta	Input / 1M	Output / 1M

DeepSeek oficial — económico	$0.15	$0.60
DeepSeek oficial — pico	$0.30	$1.20
HF → DeepSeek V4.1 Flash / Novita	$0.30	$1.20
HF → DeepSeek V4.1 Flash / Baseten	$0.30	$1.20


El catálogo actual de Hugging Face confirma DeepSeek-V4.1-Flash, con Novita a $0.30/$1.20 y Baseten a $0.30/$1.20. 

Además, HF confirma que con Inference Providers cobra la tarifa del proveedor sin añadir margen, y permite seleccionar :cheapest en lugar del :fastest predeterminado. 

Cómo organizaría tu router

ROUTER DE COSTO
                         │
                         ↓
              HORA ACTUAL COLOMBIA
                         │
             ┌───────────┴───────────┐
             │                       │
      🟩 FUERA DE PICO          🟥 HORA PICO
             │                       │
             ↓                       ↓
   DeepSeek V4.1 Flash           HF ROUTER
      API OFICIAL                    │
     $0.15 / $0.60                   ↓
                            comparar automáticamente
                              ┌───────┴────────┐
                              ↓                ↓
                       MiniMax M3      DeepSeek V4.1
                         :cheapest        :cheapest

La regla sencilla sería:

fuera de pico → DeepSeek V4.1 Flash oficial, porque cuesta la mitad.

en pico → consulta HF :cheapest y compara MiniMax M3 con DeepSeek V4.1 Flash. HF puede cambiar de proveedor sin que tengas que cambiar el token; un único HF token puede servir para múltiples proveedores. 

Así tu router no necesita memorizar manualmente qué proveedor es más barato: puede mantener DeepSeek oficial como ruta económica programada por horario y usar HF como ruta dinámica durante las ventanas pico.

📌 Primero debe intentar usar las api de Nvidia que son 4 usando Kimi k 3 o minimax M3 o DeepSeek si no hay disponible se mueve en a mis api locales en huggueface y luego si el router detectar mucha latencia para grupos del pool Salta a api o HF 

📌 Yo si selecciono el manual el modelo con el selector

---FIN DEL INPUT BLOCK (verbatim)---

---DOCUMENTO ADJUNTO (índice 4, verbatim): operador web---

Procesó durante 27s

Sí. Para lo que quieres —un operador web open source compartido por varios agentes— montaría el navegador como una capacidad independiente accesible por MCP/API, en vez de darle usuario y contraseña a cada LLM.

La opción que mejor encaja con tu arquitectura es open-browser-use: controla el navegador real que ya está autenticado, funciona localmente, es MIT y expone el navegador a agentes como Claude Code, Codex, Gemini CLI y otros mediante MCP. 
[open-browser-use en GitHub](https://github.com/open-browser-use/open-browser-use?utm_source=chatgpt.com)

También usaría Browser Use como motor de navegación. Puede hacer navegación, clics, formularios y reutilizar un perfil existente de Chrome, conservando cookies y sesiones. Su WebUI permite mantener sesiones persistentes y observar las acciones del agente. 
[Browser Use en GitHub](https://github.com/browser-use/browser-use?utm_source=chatgpt.com)
[Browser Use WebUI](https://github.com/browser-use/web-ui?utm_source=chatgpt.com)

Tu arquitectura podría quedar:

AGENTES YAIWES
                          │
        ┌─────────────────┼─────────────────┐
        ↓                 ↓                 ↓
     AGENTE 1           AGENTE 2          AGENTE 3
        └─────────────────┼─────────────────┘
                          ↓
                    ROUTER YAIWES
                          ↓
                    WEB OPERATOR
                     MCP / API
                          ↓
             Browser Use / Playwright
                          ↓
                  CHROME/CHROMIUM
                          ↓
              PERFIL AUTENTICADO
                          ↓
        GitHub / Hugging Face / otras webs

Pero no pondría tu correo + contraseña de GitHub dentro del prompt del agente. Para GitHub tienes métodos mejores: GitHub recomienda OAuth/GitHub App y, para uso personal de API, un fine-grained PAT. También existe el Device Flow, donde el agente inicia el proceso pero eres tú quien autoriza en GitHub. 

Para trabajar específicamente con la página web de GitHub, puedes autenticarte una vez tú mismo en un perfil dedicado del navegador:

TÚ
 ↓
LOGIN GitHub + 2FA/passkey
 ↓
Chrome profile / sesión
 ↓
WEB OPERATOR
 ↓
agente usa la sesión existente
 ↓
NO conoce tu contraseña

Playwright soporta precisamente reutilizar estados autenticados. Ese estado puede contener cookies, local storage, IndexedDB e incluso información relacionada con autenticación WebAuthn. Playwright advierte que ese archivo es altamente sensible porque puede permitir suplantar la sesión, por lo que nunca debe subirse al repositorio. 

Ahí entra muy bien el Secret Bank que acabamos de diseñar:

SECRET BANK
AES-256-GCM
     │
     ├── GitHub OAuth token
     ├── GitHub PAT fine-grained
     ├── Browser session/state
     └── cookies sensibles
              ↓
       solo se descifra
       durante ejecución

Yo lo construiría con estas piezas:

1. open-browser-use → capa MCP para que cualquier agente pueda pedir acciones web. 


2. Browser Use + Playwright → navegador, clicks, formularios, screenshots y automatización. 


3. Chromium dedicado → un perfil separado de tu navegador personal.


4. Secret Bank AES-256-GCM → tokens y sesiones cifradas; ningún secreto entra en el contexto del LLM.


5. GitHub App/OAuth/Device Flow → preferido para GitHub; PAT fine-grained cuando realmente necesites API. GitHub recomienda fine-grained frente a classic cuando sea posible. 


6. Policy Gateway → dominios permitidos + permisos READ, CLICK, WRITE, UPLOAD, DELETE; acciones sensibles requieren tu aprobación.



Entonces podrías escribir:

> “Entra en mi GitHub, abre el repositorio agentes, revisa el último commit y descarga el reporte.”



Y el LLM no recibe ninguna contraseña:

PROMPT
  ↓
AGENTE
  ↓
MCP: browser.open("github.com/...")
  ↓
POLICY GATE
  ↓
BROWSER YA AUTENTICADO
  ↓
acción
  ↓
resultado + screenshot + log

Para tu sistema YAIWES, yo lo llamaría WEB-OPERATOR y lo pondría como servicio común del router. Así SOL, Claude, MiniMax, Kimi, Qwen, etc. usan el mismo navegador autorizado, en lugar de almacenar credenciales por agente.

Y para GitHub incluso separaría rutas: GitHub API/MCP para el 90% de operaciones y WEB-OPERATOR solamente cuando haya algo que realmente requiera interfaz gráfica. Eso es más rápido y evita exponer sesiones del navegador innecesariamente.

---FIN DEL DOCUMENTO ADJUNTO---
