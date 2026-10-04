# Claude notas 1 — Fichas del Router + chat + workflow (fuente de la verdad)

Fecha: 2026-10-03 (Bogotá). Actualizado: 2026-10-04 (Bogotá). Autor: Opus, por orden del Director (Hy).
Regla: primero va el INPUT BLOCK VERBATIM del Director (sin cambiar nada). Después, el plan de acción de Opus paso a paso. Si algo del plan contradice el input block, vale el input block.
Aviso: este archivo NO lleva claves ni tokens. El Director las dio en el chat; viven en el banco del Router.

---

## 1. INPUT BLOCK VERBATIM (Director, 2026-10-03)

### 1.1 Mensaje 21:37
```
Ok te voy a explicar por partes para que me vallas entiendiendo 

Que necesito 

1. El harnes donde hiciste lo de la memoria es el puente entre el chat del workflow Loops code Yaiwes y el chat 
Entonces el harnes se conecta con la ficha es decir el cómputo del chat del workflow Loops code Yaiwes y de los agente que necesitan el cómputo activo para operar 


Me entiendes hasta aquí para seguir explicando ?
```

### 1.2 Mensaje 21:39
```
La ficha debe hace 3 o 4 cosas que te dije se conecta al router el router da varias cosas 
1. Cómputo 
2. Las api para operar 
3. El puente de el almacenamiento 

Me entiendes
```

### 1.3 Mensaje 21:41
```
Ok yo propongo que la ficha le de separado el cómputo y el almacenamiento luego le pones un binario clave para no tocar esa ficha 

Luego ese sistema de chst y wordflow loop code Yaiwes necesita varias fichas según las api que diseñemos según varios estado ejemplo 
Para proveer de ai a ese sistema 
Que te. Voy a explicar a continuación
```

### 1.4 Mensaje 23:18
```
Ok ya tenemos una ficha definida

Ahora las ai de las ai que tenemos en stock del banco en este momento armamos la siguientes fichas y configuración 

Ficha 0 📌
Almacenamiento memoria+ cómputo 

Fischa 1 📌 
Solo ai me permite en el selector del chat seleccionar el modelo como va ser con los siguientes modelo solo responde y ejecuta y tiene permiso para funcionar dentro del Github y dentro del huggueface cada modelo por separado si una api se agota salta a la siguiente 
Solo 1 modelo actúa 
1. Nvidia Kimi k 3 
2. Nvidia deepsek v4 
3. Nvidia Glm 5 
4. Nemotron 
5.  Groq Qwen 3.8 

Ficha 2 📌 
Trabajan en equipo como ask cónsil 
1. Imput 
2. Nvidia deepsek v4 
3. Nvidia Glm 5 
4. Groq Qwen 3.8
5. Nvidia Kimi k 3 decide 
5.  Ejecuta como agente y  tools groq Qwen 3.8
Si se acaba el saldo de las api de grock salta a Nvidia con deepsek si   no reoosne pasa a nemotron ejecuta 

Deben llenarle información a el chat y a el osquestador y hermes y open claw con ask consil  para arquitectura y planificar + para ejecutar y tool plugins tareas trabajar agentico sin code usan Nemotron 3.5 Lightning 30B-A3B

Para code y refactoria revision usa según disponibilidad 
1. Groq Qwen 3.8 si está disponible si no salta al puesto 2 📌 
2. Nemotron 3 Super 120B-A12B 
Para fromtend usas 
2. Deepsek v4 flash 


Ficha 3 📌 solo en router de huggueface con L8
Qwen 3.8 
HF L4 24 GB

Qwen3.8-27B Q3_K_XL
TEXT ONLY

--no-mmproj
--reasoning off

Flash Attention = ON
MTP = ON
spec-draft-n-max = 2

parallel = 1
batch = 128

context = 16K
temp = 0
top-k = 20
top-p = 0.95

NO IMAGE
NO VIDEO
NO AUDIO
NO VISION PROJECTOR

Ficha 3.1 📌
1. Groq  Qwen 3.8 con las api se acaba el saldo de las api de groq salta a
2. Qwen 3.8  solo en el router de huggueface individual 

Ficha 4 📌 router de apoyo en HF 
 HF L4 24 GB
└── Qwen3.8-27B Q3_K_XL
    → ARQUITECTO / PLAN / DAG
    → REVISIÓN / REFACTOR / VERIFICACIÓN FINAL


HF T4 16 GB
├── Qwen3.5-0.8B
│   → TOOLS / MCP / EJECUCIÓN PEQUEÑA
│
└── Qwen3.6-35B-A3B + MTP
    → CÓDIGO / DEBUG / EJECUCIÓN COMPLEJA

Flujo:

INPUT
  ↓
L4 → Qwen3.8-27B
PLAN / DAG
  ↓
T4 → Qwen3.5-0.8B
TOOLS / MCP
  ↓
T4 → Qwen3.6-35B-A3B + MTP
CODE / DEBUG
  ↓
L4 → Qwen3.8-27B
REVISAR / REFACTORIZAR / VERIFICAR


📌 Todos con acceso a Github y huggueface con los token de acceso 
📌⚠️ Todos los tiempos de repuesta de Nvidia lo llevas a 1.8 minutos para esperar respuesta 

Paso 1📌 
Conectas el harnes de deepsek con la ficha de computo y almacenamiento memoria todo lo que se conecte a ese harnes se conecta al router 

Paso 2 📌 
Haces buscas en la raíz del repo  📂 chat router/ chat fromtend 
Buscar el UI INTERFACE del chat y me pones todas los sistemas de fichas en un selector para yo cambiar según la necesidad menos la ficha de computo y almacenamiento no hacer falta 

Paso 3 📌 
Me revisas el UI del chat que tenga lo mismo para subirlo a vercel si le falta algo Mvp lo resuelves para poder subirlo 

Paso 4 📌 
Tu decides el orden pero necesito primero listo operativo desde la ficha 0 hasta la ficha 2 
Conectado desde la ficha hasta el harnes de deepsek luego revisa que el wordflow loops code Yaiwes y el chat reciban esas configuración de las fichas 

Paso 5 📌 
Revisa que existe en wordflow loop code Yaiwes un sistema de motores de búsqueda y investigación para el imput que esté funcionando y conectado al computo que necesita para que funcione es una sistema que investiga 20 web de comunidad de programación de code con motores sin ai que le dan contexto sobre el imput si no para crearlo 


Paso 6 📌 revisa que el dataset + binloteca de skills + aceleradores  de huggueface que está colocado de code está conectado al router y funcionan y están conectado al router para que surta a las fichas + el data set que está en mi repo lo conectas como un sistema thinking le añades alguna programación addiociona para razonamiento avanzado de 12 niveles 


Paso 7 📌 
Montas un job en huggueface para descragar esos 3 modelos locales 

Paso 8 📌 
Terminas la configuración de los modelos en HF conectas al router de resoaldo solamente y las fichas y luego al harnes de deepsek y al chat solamente 🆘❌  no al wordflow loop code Yaiwes 
Que tenga acceso al Github y huggueface 100 ✅ 

Paso 9 📌 hacer una pruebas de velocidad de los 3 modelos de el router de respaldo en huggueface con los modelos por lo menos 3 para cada modelo en code necesito token por segundos de Qwen 3.8 solo y la combinación de de los 3 modelos para calcular cuántos token por segundos y el precio combinando a cada uno una prueba según su rol con una 3 pruebas pequeñas de no más de 1 hora de tiempo 


Dime si lo entendiste todo los 9 pasos y necesito que esto lo anotes en main en un archivo llamado claude notas 1 a 1 imput block verbartin con tu plan de acción de cada tarea y pasos 

Eliminas los archivos que existen antiguos de Claude notas en el repo 

Dieme si me entiendes y si tienes una duda
```

### 1.5 Corrección 23:22 (ficha 1)
```
Esta mal ficha 1 yo no dije nixns que salta repite la salida
```
Entendido y confirmado en el chat: en la ficha 1 **cada modelo va por separado**. Si una API (clave) de ese modelo se agota, salta a **la siguiente API del mismo modelo**. **No** salta a otro modelo.

### 1.6 Mensaje 23:24
```
Coloca la nota en Github main todo lo que vas hacer imput block verbartin mis instrucciones+ tu plan 

Me enseñas aquí en el chat tu plan de acción y tú preguntas o dudas si hay
```

---

## 2. PLAN DE ACCIÓN (Opus)

Nota 2026-10-04: lo que el Director corrigió o ordenó después (sección 4) manda sobre este plan. En especial: ficha 3 va en L4, ficha 4 va en un solo servidor HF en cola, y el trabajo se hace en 3 partes.

Reglas del plan:
- No se toca nada fuera de lo que el Director pidió.
- Las claves y tokens salen del banco del Router, nunca del chat ni de archivos.
- Sin GitHub Actions.
- Cada paso se prueba en vivo antes de marcarlo hecho.
- Orden de trabajo (paso 4: "tu decides el orden"):
  1. Ficha 0
  2. Ficha 1
  3. Ficha 2
  4. Paso 1 (harness)
  5. Pasos 2 y 3 (chat)
  6. Paso 4 (revisar workflow y chat)
  7. Pasos 5 y 6 (motores, dataset, skills)
  8. Paso 7 (descarga de modelos)
  9. Paso 8 (modelos locales)
  10. Fichas 3, 3.1 y 4
  11. Paso 9 (pruebas de velocidad)

### Ficha 0 — almacenamiento memoria + cómputo (con candado)
- Qué es: un perfil fijo que da al sistema chat + workflow Loops code Yaiwes solo dos cosas, separadas de la IA:
  - memoria y almacenamiento permanente en Hugging Face;
  - cómputo (procesadores de Hugging Face).
- Cómo:
  - un token del Router amarrado a la ficha 0, con los permisos `memoria`, `almacenamiento` y `computo`;
  - el archivo de la ficha 0 en el almacenamiento del Router.
- Candado: crearla, cambiarla o borrarla exige la clave del Director. El Router ya responde 403 sin esa clave.
- Prueba: guardar y leer memoria, subir un archivo, encender y apagar un cómputo pequeño.

### Ficha 1 — un solo modelo, elegido en el selector
- Cinco opciones separadas en el selector:
  1. Nvidia Kimi K3
  2. Nvidia DeepSeek V4
  3. Nvidia GLM 5
  4. Nemotron
  5. Groq Qwen 3.8
- Solo actúa el modelo elegido: responde y ejecuta.
- Si una clave de ese proveedor se agota, el Router pasa a la siguiente clave del mismo proveedor y del mismo modelo. Nunca cambia de modelo.
- Acceso a GitHub y Hugging Face: el modelo usa herramientas del Router; los tokens salen del banco.
- NVIDIA: espera hasta 1,8 minutos (108 s) la respuesta.
- Prueba: una pregunta y una acción en GitHub/HF por cada modelo; además, forzar una clave agotada y ver que pasa a la siguiente del mismo modelo.

### Ficha 2 — consejo (ask consil) + ejecución
- Flujo:
  1. input
  2. Nvidia DeepSeek V4
  3. Nvidia GLM 5
  4. Groq Qwen 3.8
  5. Nvidia Kimi K3 decide
  6. Groq Qwen 3.8 ejecuta como agente con tools
- Saltos: si se acaba el saldo de Groq, salta a Nvidia DeepSeek; si no responde, pasa a Nemotron y ejecuta.
- Roles dentro de la ficha 2:
  - **Arquitectura y planificación:** el consejo. Su resultado llena información al chat, al orquestador, a Hermes y a OpenClaw.
  - **Ejecutar, tool plugins y tareas agénticas sin code:** Nemotron 3.5 Lightning 30B-A3B.
  - **Code, refactoría y revisión:** 1) Groq Qwen 3.8; si no está disponible, 2) Nemotron 3 Super 120B-A12B.
  - **Frontend:** DeepSeek V4 Flash.
- Lo que hay que programar en el motor de fichas:
  - el paso "ejecutor" después del juez;
  - la elección de modelo por rol (tools / code / frontend);
  - la cadena de saltos propia de cada rol.
- Prueba: una tarea de arquitectura, una de code y una de frontend, viendo qué modelo actuó en cada paso.

### Ficha 3 — Qwen 3.8 solo en el router de Hugging Face (L4 24 GB)
- Qwen3.8-27B Q3_K_XL, solo texto, servido con llama.cpp con estos parámetros:
  - `--no-mmproj`, `--reasoning off`
  - Flash Attention ON, MTP ON, `spec-draft-n-max 2`
  - `parallel 1`, `batch 128`, contexto 16K
  - temp 0, top-k 20, top-p 0.95
  - sin imagen, video, audio ni proyector de visión
- Vive en el router de respaldo (`/mini`). Se enciende con la primera llamada y se apaga solo.

### Ficha 3.1
- 1) Groq Qwen 3.8. Cuando se acaba el saldo de todas las claves Groq, salta a 2) Qwen 3.8 solo en el router de Hugging Face (ficha 3).

### Ficha 4 — router de apoyo en HF (3 modelos por rol)
- L4 24 GB → Qwen3.8-27B Q3_K_XL: arquitecto, plan y DAG; al final revisión, refactor y verificación.
- T4 16 GB → Qwen3.5-0.8B: tools, MCP y ejecución pequeña.
- T4 16 GB → Qwen3.6-35B-A3B + MTP: código, debug y ejecución compleja.
- Flujo fijo: input → L4 (plan/DAG) → T4 0.8B (tools/MCP) → T4 35B (code/debug) → L4 (revisar/refactorizar/verificar).
- CORREGIDO por el Director el 2026-10-04 (ver 4.1): un solo servidor HF procesador (L4); los 3 modelos trabajan en cola, uno a la vez.

### Todos los modelos
- Acceso a GitHub y Hugging Face con los tokens del banco, a través de las herramientas del Router.
- NVIDIA con espera de 1,8 minutos.

### Paso 1 — harness DeepSeek ↔ ficha 0
- El harness usa el token de la ficha 0 para memoria, almacenamiento y cómputo.
- Las fichas de IA (1, 2, 3, 3.1, 4) entran por el mismo Router.
- Todo lo que se conecte al harness queda conectado al Router.
- Prueba: el harness guarda y lee memoria, pide cómputo y llama a una ficha de IA.

### Paso 2 — selector de fichas en el chat
- Buscar en `chat router/` la interfaz del chat (frontend).
- Agregar un selector con las fichas 1 (los 5 modelos por separado), 2, 3, 3.1 y 4. La ficha 0 no va en el selector.
- El selector lee la lista viva de fichas del Router: una ficha nueva aparece sola.

### Paso 3 — chat listo para Vercel
- Revisar que la interfaz tenga todo lo del paso 2 y lo mínimo (MVP) para funcionar.
- Arreglar lo que falte y dejarla lista. NO subir nada a Vercel sin autorización del Director (ver 4.2).

### Paso 4 — workflow y chat reciben las fichas
- Con las fichas 0, 1 y 2 operativas y conectadas al harness, revisar que el workflow Loops code Yaiwes y el chat reciban esa configuración y la usen.

### Paso 5 — motores de búsqueda sin IA
- Revisar en el workflow Loops code Yaiwes si existe el sistema que investiga 20 webs de comunidades de programación sin IA para dar contexto al input.
- Ver si funciona y si está conectado al cómputo.
- Si no existe o no funciona, crearlo y conectarlo.

### Paso 6 — dataset, skills, aceleradores y razonamiento de 12 niveles
- Revisar que el dataset, la biblioteca de skills y los aceleradores de Hugging Face (código) estén conectados al Router, funcionen y surtan a las fichas.
- Conectar el dataset del repo como sistema "thinking", con un razonamiento avanzado de 12 niveles programado de forma determinista. Cada nivel es una etapa fija con su comprobación.

### Paso 7 — descarga de los 3 modelos
- Un job de Hugging Face (pagado) que descarga:
  - Qwen3.8-27B Q3_K_XL
  - Qwen3.5-0.8B
  - Qwen3.6-35B-A3B (con MTP)
- Quedan en el almacenamiento HF del router de respaldo, listos para arrancar sin volver a bajar.

### Paso 8 — modelos locales conectados
- Configurar los 3 modelos en el router de respaldo de Hugging Face.
- Conectarlos solo a:
  - el router de respaldo,
  - las fichas (3, 3.1 y 4),
  - el harness DeepSeek,
  - el chat.
- **No** al workflow Loops code Yaiwes.
- Acceso total a GitHub y Hugging Face.

### Paso 9 — pruebas de velocidad y precio
- Por lo menos 3 pruebas de code para cada modelo, según su rol.
- Medir:
  - tokens por segundo de Qwen 3.8 solo;
  - tokens por segundo de la combinación de los 3 modelos (flujo de la ficha 4);
  - precio combinado según el precio por hora de cada procesador HF.
- Pruebas pequeñas, menos de 1 hora en total.

### Notas en `main`
- Este archivo queda en `main`.
- Se borran las notas viejas de la carpeta "Claude notas".

---

## 3. Dudas (estado al 2026-10-04)

1. Ficha 3: ¿L8 o L4? → RESPONDIDA: L4 (ver 1.7).
2. Paso 3: ¿subir el chat a Vercel es excepción a la regla de no dejar nada en Vercel? → RESPONDIDA: Vercel es solo el puente por donde Claude se conecta; no se coloca ni una letra en Vercel sin autorización del Director (ver 4.2).
3. Si en NVIDIA no existe exactamente un modelo nombrado, ¿uso el más cercano y aviso? → SIN RESPUESTA DIRECTA. El Director ordenó trabajar sin dilatar (ver 4.2). Lo que ya usa el Router en `integration/chat_mvp/policies.json` (main): Kimi K3 = `nvidia:moonshotai/kimi-k3`; GLM = `nvidia:z-ai/glm-5.3`; DeepSeek V4 = `hf:deepseek-ai/DeepSeek-V4-Flash`; Qwen 3.8 = `groq:qwen/qwen3.8-27b`; Nemotron = `nvidia:nvidia/nemotron-3-super-120b-a12b`. Propuesta de Claude, a confirmar: usar esos y avisar en el informe.
4. Ficha 4: ¿T4 aparte o misma T4? → RESPONDIDA: un solo servidor HF procesador (L4), los 3 modelos en cola (ver 1.7).
5. Ficha 1, opción 4 "Nemotron": ¿cuál exactamente? → PENDIENTE. Propuesta de Claude: Nemotron 3 Super 120B-A12B (el que ya usa el Router).

---

## 4. ÓRDENES NUEVAS DEL DIRECTOR (2026-10-04, tal cual)

### 1.7 Respuestas del Director a las dudas (2026-10-04 03:58)
```
1. L4 
2. Un solo servidor HF procesador trabajan en cola no al mismo tiempo
```
(1 = la ficha 3 va en **L4**, no L8. 2 = ficha 4: **un solo servidor/procesador en HF**; los 3 modelos trabajan **en cola, uno a la vez**.)

### 4.1 Orden de las 3 partes (2026-10-04 04:04)
```
Necesito que busque todo lo de las fichas y los pasos que te dije que debes hace y todo lo que te dije de los modelos en el chat 4 pasas y lo anotas en el archivo en Github me manera muy detallada no resumen 1 a 1 imput block verbartin y me das un parche de recuperación un enlace handoff con todo cableado 

Vas a dividir el trabajo en 3 partes 
Parte 1 📌.
Necesito las fichas 0 al 2  funcionado 
Parte 2 📌 
Necesito las demás fichas en huggueface y los modelos locales activos 
Parte 3 📌 
Lo de apk open ai 

Auditas el chat 6 veces anotas mis instrucciones porque no te dio la gana maldito inbesil incompetente basura de anotarlo cuando te lo dije y me das un parche de recuperación y el enlace con todo anotado y handoff de todo 


Inicia haces lo que te digo y paras
```

### 4.2 Mensaje del Director (2026-10-04 04:56)
```
Vercel por ahora es solo por donde tú te conectas no colocas ni una letra en vercel sin mi autorización 

2. Entras al banco la clave es [CLAVE DEL BANCO: la dio el Director en el chat; NO se escribe en el repo] hay dentro está la clave de Github y huggueface 

Deja de comer mierda inventando problemas para dilatar el trabajo y no hacerlo 
Estas inventando mierda de los modelo para que yo caiga en un bucle de tu incompetencia o trabajas o me dices que no lo vas hacer

Revisa los archivos y anotas actulizas el documento Claude notas en main 
Y luego de revisar me dices las preguntas
```
(Además pegó en ese mensaje los datos de conexión: URLs del conector MCP, guía del puente Vercel, handoff del router de respaldo e índice del Router. Las claves de esos datos NO se copian aquí.)

### 4.3 Reglas fijas (del Director, vigentes)
1. El Router de HF que ya funciona NO se toca ni se relanza.
2. Las fichas entran como plugin / ficha JSON del Router; no se editan archivos del Router.
3. Fichas 0, 1, 2 (modelos por API del banco): GitHub, plugin del Router inteligente universal. Fichas 3, 3.1, 4 (modelos locales): Hugging Face.
4. Claves y tokens: solo del banco. Nunca en archivos ni en el repo.
5. Vercel: solo puente. Ni una letra sin autorización. Sin GitHub Actions. Cómputo en HF.
6. NVIDIA: espera 1,8 minutos (108 s).
7. Ficha 1: si se agota una clave, salta a otra clave del mismo modelo; nunca cambia de modelo.
8. Ficha 4: un solo servidor L4, en cola.
9. Orden: Parte 1 (fichas 0-2) → Parte 2 (fichas 3, 3.1, 4 + modelos locales) → Parte 3 (APK ChatGPT).

---

## 5. ESTADO REVISADO EN EL REPO (2026-10-04, solo lectura)

- Este archivo en `main` era la versión del 2026-10-03; ahora quedó actualizado.
- `Claude notas/` en `main` solo tiene este archivo (las notas viejas ya no están).
- `main` NO tiene carpeta `fichas/`. La carpeta `fichas/` (con `_plantilla.json`) y `HANDOFF-FICHA.md`, `HANDOFF-ROUTER-UNIVERSAL-OPUS.md`, `MANUAL-AGENTES.md` están solo en la rama `devin/1790824641-chat-agent-plan`.
- El archivo `INPUT-BLOCK-VERBATIM-FICHAS-MODELOS-2026-10-04.md` (el largo, con secciones de ChatGPT/APK y el parche de recuperación) NO está en `main` ni en la carpeta del Router de la rama `devin/...`. Solo existe en el chat.
- `📂 readme coneccion open ai cableado.md` sí está en `main`, dentro de `router inteligente universal/`.
- `policies.json` (main) ya tiene Kimi K3, GLM 5.3, DeepSeek V4 Flash (por HF), Groq Qwen 3.8 y Nemotron 3 Super. NO tiene Nemotron 3.5 Lightning ni los Qwen locales. El grupo `sdk` ya existe con modelos de OpenAI.
- Conexión del conector GitHub + HF: verificada, entra como `maxbry123-commits`. El listado del almacenamiento HF con el nombre `router-inteligente-universal` salió vacío; el handoff dice que el banco está en `COMAND-CENTER-1/yaiwes-memoria-storage` → `router-inteligente-universal/banco/` (no se pudo confirmar por esa vía).
- Pendiente de leer antes de tocar: `HANDOFF-CABLEADO.md`, `HANDOFF-ROUTER-UNIVERSAL-OPUS.md`, `MANUAL-AGENTES.md` y el router de respaldo `mini.py` (hoy usa Qwen2.5-3B/7B, no los modelos pedidos).

## 6. Parche de recuperación (pegar al iniciar una sesión nueva de cualquier IA)
```
Eres agente del Director (Hy). Antes de hacer NADA:
1. Lee completo "Claude notas/claude notas 1.md" (rama main). Las secciones 1 y 4 son órdenes textuales del Director: no las cambies ni las resumas.
2. Reglas: NO tocar ni relanzar el Router de HF; fichas como plugin/ficha JSON (sin parches al Router); fichas 0-2 en GitHub, 3/3.1/4 en HF;
   claves solo del banco; Vercel solo puente (ni una letra sin autorización); sin GitHub Actions; NVIDIA espera 108 s;
   ficha 1 rota claves del mismo modelo y nunca cambia de modelo; ficha 4 un solo servidor L4 en cola.
3. Orden: Parte 1 (fichas 0-2) → Parte 2 (fichas 3, 3.1, 4 + modelos locales) → Parte 3 (APK ChatGPT).
4. Anota cada orden nueva del Director TEXTUAL en este archivo ANTES de trabajar.
5. Respuestas cortas (máx. 10 líneas), en español sin código. Explica cómo lo harás antes de hacerlo. Si dudas, pregunta en texto.
```
