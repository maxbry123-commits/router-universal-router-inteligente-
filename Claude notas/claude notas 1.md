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

Nota 2026-10-04: lo que el Director corrigió o ordenó después (sección 4) manda sobre este plan. En especial: ficha 3 va en L4, la ficha 4 va con la configuración de 4.5 (un solo servidor L4 y los 2 modelos chicos en cola en una T4), el trabajo se hace una salida por paso (4.4), Nemotron 3.5 Lightning va por NVIDIA como agente ejecutor, no en HF (4.6), y los modelos que no corren en la GPU se cambian por otros que dará el Director (4.8).

Reglas del plan:
- No se toca nada fuera de lo que el Director pidió.
- Las claves y tokens salen del banco del Router, nunca del chat ni de archivos.
- Sin GitHub Actions.
- Cada paso se prueba en vivo antes de marcarlo hecho.
- Orden de trabajo (paso 4: "tu decides el orden"): ver 4.4 (el Director fijó el orden de las salidas).

### Ficha 0 — almacenamiento memoria + cómputo (con candado) — HECHA el 2026-10-04 (ver 5, salida 2)
- Qué es: un perfil fijo que da al sistema chat + workflow Loops code Yaiwes solo dos cosas, separadas de la IA:
  - memoria y almacenamiento permanente en Hugging Face;
  - cómputo (procesadores de Hugging Face).
- Cómo quedó: un token del Router llamado `ficha-0/principal`, con permisos solo `memoria`, `almacenamiento` y `computo` (sin `chat`, sin `fichas`, sin `terminal`). El token está guardado en el banco como `router/ficha-0`. No va en el selector del chat.
- Candado: crear, listar, apagar o cambiar tokens exige la clave del Director (el Router responde 403 sin ella).
- Orden 05:11: la ficha 0 NO se conecta todavía al harness de DeepSeek.

### Ficha 1 — un solo modelo, elegido en el selector — MONTADA el 2026-10-04 (ver 5, salida 3); 4 de 5 responden
- Cinco opciones separadas en el selector (cada una es una ficha de un solo paso, nombre `ficha-1-<modelo>`):
  1. Nvidia Kimi K3 → `ficha-1-kimi-k3` (responde)
  2. Nvidia DeepSeek V4 (DeepSeek V4 Flash por HF) → `ficha-1-deepseek-v4` (NO responde: el Router contesta `MODEL_NOT_SELECTABLE`)
  3. Nvidia GLM 5 (GLM 5.3) → `ficha-1-glm-5` (responde)
  4. Nemotron (Nemotron 3 Super 120B-A12B, confirmado por el Director 05:01) → `ficha-1-nemotron` (responde)
  5. Groq Qwen 3.8 → `ficha-1-groq-qwen-3-8` (responde)
- Solo actúa el modelo elegido: responde y ejecuta.
- Si una clave de ese proveedor se agota, el Router pasa a la siguiente clave (API) del mismo modelo. Nunca cambia de modelo. Si no queda ninguna clave, sale un mensaje de error (Director 05:11). Comprobado: al pedir un modelo que no existe, el Router da error y NO salta a otro modelo.
- Acceso a GitHub y Hugging Face: el modelo usa herramientas del Router; los tokens salen del banco. (Pendiente de la parte final del plan: asegurar ese acceso en todas las fichas.)
- NVIDIA: espera hasta 1,8 minutos (108 s) la respuesta. NO aplicado todavía: el Router tiene 90 s en su política y cambiarlo exige tocar un archivo del Router (ver duda 11).
- Prueba hecha: una pregunta por modelo, todos mostraron en el informe el modelo que contestó.

### Ficha 2 — consejo (ask consil) + ejecución — MONTADA el 2026-10-04 (ver 5, salida 3)
- Flujo:
  1. input
  2. Nvidia DeepSeek V4
  3. Nvidia GLM 5
  4. Groq Qwen 3.8
  5. Nvidia Kimi K3 decide
  6. Groq Qwen 3.8 ejecuta como agente con tools
- Cómo quedó (el motor de fichas del Router hace consejo + juez pero no un ejecutor después del juez):
  - Tramo 1, ficha `ficha-2` (modo consejo): DeepSeek V4, GLM 5.3 y Groq Qwen 3.8 opinan; Kimi K3 es el juez y escribe en la primera línea `ROL: tools | codigo | frontend | general`.
  - Tramo 2, fichas internas de un paso, que llama el agente (harness, Hermes, OpenClaw) según el ROL: `ficha-2-ejecutor-general` (Groq Qwen 3.8) con respaldo `ficha-2-ejecutor-general-respaldo` (Nemotron 3 Super); `ficha-2-ejecutor-tools` (Nemotron 3.5 Lightning por NVIDIA); `ficha-2-ejecutor-codigo` (Groq Qwen 3.8) con respaldo `ficha-2-ejecutor-codigo-respaldo` (Nemotron 3 Super); `ficha-2-ejecutor-frontend` (DeepSeek V4 Flash).
  - La regla de saltos (si falla Groq, usar el respaldo) la aplica el agente que llama: si la ficha principal responde con error, llama a la de respaldo. El Router no tiene saltos entre fichas.
- Saltos pedidos por el Director: si se acaba el saldo de Groq, salta a Nvidia DeepSeek; si no responde, pasa a Nemotron y ejecuta. El salto por NVIDIA DeepSeek no se usa porque ese modelo no responde (se pasa directo a Nemotron).
- Roles dentro de la ficha 2:
  - **Arquitectura y planificación:** el consejo. Su resultado llena información al chat, al orquestador, a Hermes y a OpenClaw.
  - **Ejecutar, tool plugins y tareas agénticas sin code:** Nemotron 3.5 Lightning 30B-A3B, por NVIDIA (agente ejecutor, no en HF; orden 05:46).
  - **Code, refactoría y revisión:** 1) Groq Qwen 3.8; si no está disponible, 2) Nemotron 3 Super 120B-A12B.
  - **Frontend:** DeepSeek V4 Flash.
- Pruebas hechas: consejo con una tarea real (GLM, Qwen y el juez Kimi respondieron; DeepSeek falló por `MODEL_NOT_SELECTABLE`); cada ejecutor con una pregunta corta (todos responden menos frontend/DeepSeek).

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

### Ficha 4 — router de apoyo en HF (configuración fijada por el Director 05:23, ver 4.5)
- Un solo servidor L4 24 GB con Qwen3.8-27B Q3_K_XL: arquitecto/plan/DAG al inicio; revisión/refactor/verificación final al cierre.
- Dos modelos en cola en una T4 16 GB (no al mismo tiempo): Qwen3.5-0.8B (tools, MCP, ejecución pequeña) y Qwen3.6-35B-A3B + MTP (código, debug, ejecución compleja).
- Flujo fijo: input → L4 (plan/DAG) → T4 0.8B (tools/MCP) → T4 35B (code/debug) → L4 (revisar/refactorizar/verificar).
- OJO (Director 15:31): el archivo del 35B que se bajó no corre en la T4. Los modelos de la T4 se cambiarán por otros que dará el Director.

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
- Agregar un selector con las fichas 1 (los 5 modelos por separado), 2, 3, 3.1 y 4. La ficha 0 no va en el selector. Las fichas internas `ficha-2-ejecutor-*` NO deben aparecer en el selector.
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

### Paso 7 — descarga de los 3 modelos (primera tanda hecha el 2026-10-04, ver 5)
- Un job de Hugging Face (servidor CPU 32 GB de RAM, 0,03 USD/h, `cpu-upgrade`) que descarga uno tras otro y se apaga solo al terminar.
- Primera tanda (ya en el almacenamiento): Qwen3.8-27B Q3_K_XL, Qwen3.5-0.8B Q8_0 y Qwen3.6-35B-A3B Q3_K_XL.
- Destino: almacenamiento permanente HF, bucket `COMAND-CENTER-1/yaiwes-memoria-storage`, carpeta `router-respaldo/modelos/`.
- Nemotron 3.5 Lightning NO va en este job (orden 05:46): va por NVIDIA como agente ejecutor.
- Segunda tanda: cuando el Director dé los modelos que sí corren en la GPU (4.8). Aprovechar para revisar que cada archivo quepa en su GPU antes de bajarlo.

### Paso 8 — modelos locales conectados
- Configurar los modelos en el router de respaldo de Hugging Face.
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
  - tokens por segundo de la combinación de los modelos (flujo de la ficha 4);
  - precio combinado según el precio por hora de cada procesador HF.
- Pruebas pequeñas, menos de 1 hora en total.

### Notas en `main`
- Este archivo queda en `main`.
- Se borran las notas viejas de la carpeta "Claude notas".

---

## 3. Dudas (estado al 2026-10-04)

1. Ficha 3: ¿L8 o L4? → RESPONDIDA: L4 (ver 1.7).
2. Paso 3: ¿subir el chat a Vercel es excepción a la regla de no dejar nada en Vercel? → RESPONDIDA: Vercel es solo el puente por donde Claude se conecta; no se coloca ni una letra en Vercel sin autorización del Director (ver 4.2).
3. Si en NVIDIA no existe exactamente un modelo nombrado, ¿uso el más cercano y aviso? → RESPONDIDA "Sí" (05:01): GLM 5 = `nvidia:z-ai/glm-5.3`; DeepSeek V4 = `hf:deepseek-ai/DeepSeek-V4-Flash`; avisar en el informe.
4. Ficha 4: ¿T4 aparte o misma T4? → RESPONDIDA (ver 1.7 y 4.5): un solo servidor L4 y los 2 modelos chicos en cola en T4.
5. Ficha 1, opción 4 "Nemotron": ¿cuál? → RESPONDIDA "Sí" (05:01): Nemotron 3 Super 120B-A12B.
6. Nemotron 3.5 Lightning en el job → RESPONDIDA (05:46): NO va en el job, va por NVIDIA como agente ejecutor.
7. Token HF de escritura para el job → RESUELTA (05:46): el Director lo dio en el chat (nombre `HF_TOKEN_1_NEW`). No se guarda en archivos; conviene cambiarlo cuando todo esté estable, porque quedó escrito en el chat.
8. Cuantizaciones elegidas por Claude (0.8B en Q8_0, 35B en UD-Q3_K_XL de 17,2 GB) → RESPONDIDA por el Director (15:31): el modelo bajado "no corre". El Director dará otros modelos. Hasta entonces, no se baja nada más.
9. "Ficha 5": en las notas no existe; Claude la toma como la 3.1 (sin respuesta del Director).
10. (NUEVA, PENDIENTE) DeepSeek V4: el Router no deja elegir ningún modelo DeepSeek de forma directa (`MODEL_NOT_SELECTABLE`, probado con 6 modelos de HF); por NVIDIA `deepseek-v4.1-flash` no responde (se queda esperando más de 140 s). Afecta `ficha-1-deepseek-v4`, el miembro DeepSeek de `ficha-2` y `ficha-2-ejecutor-frontend`. Opciones para el Director: (a) permitir DeepSeek elegido de forma directa en el Router (toca un archivo del Router: pide su OK); (b) otro modelo para esos puestos; (c) usar el grupo `minor` del Router, que lleva DeepSeek primero pero puede contestar otro modelo (rompe la regla de "nunca cambia de modelo" en la ficha 1).
11. (NUEVA, PENDIENTE) Espera de NVIDIA a 1,8 minutos (108 s): hoy el Router espera 90 s por modelo (`policies.json`, grupo `chat_nvidia`). Kimi K3 llegó a tardar 64 s en una prueba. Subirlo a 108 s exige cambiar ese archivo del Router.

---

## 4. ÓRDENES NUEVAS DEL DIRECTOR (2026-10-04, tal cual)

### 1.7 Respuestas del Director a las dudas (2026-10-04 03:58)
```
1. L4 
2. Un solo servidor HF procesador trabajan en cola no al mismo tiempo
```
(1 = la ficha 3 va en **L4**, no L8. 2 = ficha 4: **un solo servidor/procesador en HF**; los modelos trabajan **en cola, uno a la vez**.)

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

### 4.3 Respuestas a las preguntas (2026-10-04 05:01)
```
1. Si 
2. Si 

Ya sabes cómo vas hacer la ficha y como va la ficha 0 a la 4 explicame para que no alucines
```

### 4.4 Orden por salidas (2026-10-04 05:11)
```
Ficha 1 no cambia de modelo solo cambia de Api si se agota saldrá mensaje de erro solo cambia de Api 

Haces los siguientes pasos 1 por salida 
Paso 1 📌 salida 1 📌. Monta el Job con los 3 modelos para que se descargue en el almacenamiento de huggueface permanente 
El job se detiene al terminar la descarga en cola en un servidor procesador HF 32 ram de 0.03 $ por hora 


Paso 2 📌 salida 2. Haces la ficha 0 creo que ya
Esta si no la haces .conectado al harnes de deepsek 

Paso 3 📌 salida 3 📌 Luego la ficha 1 al 2 las montas y conectas al routee y al harnes de deepsek 
Revisa y confirmas 

Luego

Paso 4 📌 salida 4 📌 
La ficha 3 y 4 y 5 



📌  Luego 
Asegúrate que todos las fichas tengan acceso a huggueface y Github las claves están en el banco de secreto la clave es [CLAVE DEL BANCO: no se escribe en el repo]

 
Muestra como vas hace la ficha 3 y 4 y 5
```
(Nota de Claude: el Director dio dos claves distintas en 04:56 y 05:11. Al probarlas contra el Router, la del 04:56 es la que funciona como clave del Director; la del 05:11 da 403, parece un error de tecleo. Ninguna se guarda aquí. En las notas no existe "ficha 5": Claude la toma como la 3.1 hasta que el Director diga otra cosa.)

### 4.5 Correcciones y configuración de la ficha 4 (2026-10-04 05:14 a 05:23)
```
La ficha 4 no es así alucinas idiota revisa 

La clave es la que te di
```
```
Vas a mostrar lo que vas a ser en la siguiente salida ejecutas  y escribes en la salida la siguiente tarea 

Confirma que vas hace en salida 1
```
```
Esta es la configuración 

L4 24 GB
Qwen3.8-27B Q3_K_XL
→ ARQUITECTO / PLAN / DAG

T4 16 GB
Qwen3.5-0.8B
→ TOOLS / MCP / EJECUCIÓN PEQUEÑA

T4 16 GB
Qwen3.6-35B-A3B + MTP
→ CODE / DEBUG / EJECUCIÓN COMPLEJA

L4 24 GB
Qwen3.8-27B Q3_K_XL
→ REVISIÓN / REFACTOR / VERIFICACIÓN FINAL

Un solo servidor de L4 y 2 modelos en cola en T4

Inicia salida 1
```

### 4.6 Modelo extra y su corrección (2026-10-04 05:30 y 05:46)
```
Monta en el job también este modelo . 
NVIDIA asegura que Nemotron 3.5 Lightning
```
(El mensaje de las 05:30 llegó cortado.)
```
HF_TOKEN_1_NEW

[TOKEN HF: lo dio el Director en el chat; NO se escribe en el repo]

Correción no va en el job va en Nvidia como agente ejecutor no en HF ❌


Nemotron 3.5 Lightning
```

### 4.8 Modelos que no corren y orden de la ficha 0 (2026-10-04 15:31)
```
Eres idiota descargar modelo que no corre idiota bruto 

Luego te doy otros modelos 

Realiza ficha 0 ya opus hizo lo de la memoria revisa puede que ya esté listo ficha 0 para no Reaver el trabajo revisa primero
```

### 4.9 Fichas 1 y 2 (2026-10-04 15:40 a 15:43)
```
Ya está lista ?
```
```
Sigue con las ficha 1 a la 2 primero explícame cómo la vez hacer la distribución de trabajo simple y corto
```
```
Si aprobado haz las 2 fichas
```
(Claude explicó el plan y el Director lo aprobó: fichas 1 y 2 como fichas del Router, consejo con juez y ejecutor por rol.)

### 4.10 Revisar modelos de NVIDIA (2026-10-04 16:03)
```
Revisa que modelos te responde Nvidia y te digo que hacer para cambiar a deepsek
```

### 4.7 Reglas fijas (del Director, vigentes)
1. El Router de HF que ya funciona NO se toca ni se relanza.
2. Las fichas entran como plugin / ficha JSON del Router; no se editan archivos del Router.
3. Fichas 0, 1, 2 (modelos por API del banco): GitHub, plugin del Router inteligente universal. Fichas 3, 3.1, 4 (modelos locales): Hugging Face.
4. Claves y tokens: solo del banco. Nunca en archivos ni en el repo.
5. Vercel: solo puente. Ni una letra sin autorización. Sin GitHub Actions. Cómputo en HF.
6. NVIDIA: espera 1,8 minutos (108 s).
7. Ficha 1: si se agota una clave, salta a otra clave del mismo modelo; nunca cambia de modelo; si no queda ninguna, mensaje de error.
8. Ficha 4: configuración de 4.5.
9. Orden: una salida por paso (4.4). Antes de cada salida: mostrar qué se va a hacer; al final de la salida: escribir la siguiente tarea.
10. Nemotron 3.5 Lightning: por NVIDIA como agente ejecutor, no se baja a HF.
11. Antes de crear algo, revisar si ya está hecho (no rehacer trabajo de Opus; 4.8).
12. Antes de bajar un modelo local, comprobar que corre en la GPU asignada (4.8).

---

## 5. ESTADO REVISADO EN EL REPO Y SALIDAS (2026-10-04)

### Repo
- `Claude notas/` en `main` solo tiene este archivo.
- `main` NO tiene carpeta `fichas/`. La carpeta `fichas/` y `HANDOFF-FICHA.md`, `HANDOFF-ROUTER-UNIVERSAL-OPUS.md`, `MANUAL-AGENTES.md` están solo en la rama `devin/1790824641-chat-agent-plan`.
- Las copias de las fichas 1 y 2 están en la rama `devin/1790824641-chat-agent-plan`, carpeta `router inteligente universal/fichas/` (12 archivos `.json`, ver salida 3).
- El archivo largo `INPUT-BLOCK-VERBATIM-FICHAS-MODELOS-2026-10-04.md` NO está en el repo; solo existe en el chat.
- `policies.json` (main) ya tiene Kimi K3, GLM 5.3, DeepSeek V4 Flash (por HF), Groq Qwen 3.8 y Nemotron 3 Super. NO tiene Nemotron 3.5 Lightning ni los Qwen locales (Nemotron 3.5 Lightning sí está en el catálogo de NVIDIA y responde: `nvidia:nvidia/nemotron-3.5-lightning-30b-a3b`).
- Memoria (rama `devin/...`): vive en `chat router/memoria/` (antes `chat router/04-MEMORIA`, movida el 2026-10-03); el plugin del harness está en `chat router/harness plugins/memoria`. Flujo: harness → Router `/memoria/*` → motores → almacenamiento HF. Limitaciones conocidas (HANDOFF-MEMORIA-GAPS.json): Graphiti, Graphify, FalkorDB, AgentDB, Memanto, PostgreSQL y Redis siguen sin servicio; SQLite + grafo SQLite cubren como respaldo y están probados.

### Salida 1 — Paso 1 (job de descarga): TERMINADA (2026-10-04, ~05:55)
- Job `6ac22eab404719ba3764cc0e`, servidor `cpu-upgrade` (32 GB), COMPLETED, se apagó solo.
- Quedaron en el almacenamiento permanente (`COMAND-CENTER-1/yaiwes-memoria-storage`, carpeta `router-respaldo/modelos/`):
  - `Qwen3.8-27B-UD-Q3_K_XL.gguf` — 13,1 GB (de `unsloth/Qwen3.8-27B-GGUF`).
  - `Qwen3.5-0.8B-Q8_0.gguf` — 0,8 GB (de `unsloth/Qwen3.5-0.8B-GGUF`).
  - `Qwen3.6-35B-A3B-UD-Q3_K_XL.gguf` — 17,2 GB (de `unsloth/Qwen3.6-35B-A3B-MTP-GGUF`). El Director dice que este no corre (4.8): pesa más que los 16 GB de una T4. Sigue guardado; no se borró porque nadie lo pidió.
  - `LEEME.txt`.
- Cómo funciona el Router con jobs (para el que siga): `POST /hf/compute/run` con clave maestra + `X-Director-Key` (o con un token con permiso `computo`); acepta `flavor cpu-upgrade`; un `env` chico funciona (uno grande dio error 500); los jobs NO reciben ningún token de HF por sí solos, hay que pasarlo por `env`.
- Jobs de prueba y un intento sin token (terminaron solos, costo despreciable): `6ac22a51404719ba3764c680`, `6ac22a51404719ba3764c682`, `6ac22b1f404719ba3764c7a5`, `6ac22a67fbc85ba68239d175`.

### Salida 2 — Paso 2 (ficha 0): TERMINADA (2026-10-04, ~15:45)
- Revisión previa (solo lectura): la memoria ya estaba hecha y viva (`/memoria/health`: SQLite conectado con 1.293 registros y grafo de respaldo conectado). La ficha 0 como tal NO existía: el Router tenía 0 tokens y 0 fichas montadas.
- Lo que se creó (nada más): un token `ficha-0/principal` (instancia `ficha-0`) con permisos exactos `memoria`, `almacenamiento` y `computo`, límite 600 llamadas por minuto. El token quedó guardado en el banco como `router/ficha-0` (banco respondió PERSISTED). No se escribió en ningún archivo ni en el chat.
- Pruebas hechas con ese token (todas pasaron): quién soy; memoria (guardar y leer; queda un registro de prueba 1294, ámbito `ficha-0`); almacenamiento (guardar, leer, borrar); cómputo (job `6ac2b873404719ba37650990` COMPLETED); candado (listar tokens sin clave del Director → 403); sin IA (chat con ese token → 403 `TOKEN_SIN_PERMISO:chat`).
- NO está conectada al harness de DeepSeek (orden 05:11).
- Notas para el que siga: crear un token exige el campo `instancia` (si falta, error 422); el nombre completo queda `instancia/nombre`.

### Salida 3 — Paso 3 (fichas 1 y 2): MONTADAS Y PROBADAS EN EL ROUTER, FALTA HARNESS (2026-10-04, ~16:00)
- Revisión previa: el Router tenía 0 fichas montadas; en GitHub solo existía `_plantilla.json`. El motor de fichas (`secciones.py`) soporta modos cadena, paralelo, consejo (con juez) y único; no tiene "ejecutor después del juez" ni saltos entre fichas.
- Publicadas con la clave del Director (12 fichas, todas `estado: ok` en `GET /secciones`): `ficha-1-kimi-k3`, `ficha-1-deepseek-v4`, `ficha-1-glm-5`, `ficha-1-nemotron`, `ficha-1-groq-qwen-3-8`, `ficha-2`, `ficha-2-ejecutor-general`, `ficha-2-ejecutor-general-respaldo`, `ficha-2-ejecutor-tools`, `ficha-2-ejecutor-codigo`, `ficha-2-ejecutor-codigo-respaldo`, `ficha-2-ejecutor-frontend`. Viven en `router-inteligente-universal/fichas/` del almacenamiento HF; copia en GitHub (rama `devin/...`, `router inteligente universal/fichas/`).
- Respuesta real de cada modelo (prueba "responde OK"): Kimi K3 OK (6 a 64 s); GLM 5.3 OK; Nemotron 3 Super OK; Groq Qwen 3.8 OK; Nemotron 3.5 Lightning OK (NVIDIA); DeepSeek V4 Flash (HF) y todos los DeepSeek de HF: `MODEL_NOT_SELECTABLE`; DeepSeek V4.1 Flash por NVIDIA: sin respuesta tras 140 s.
- Consejo `ficha-2` con una tarea real: GLM y Qwen opinaron, DeepSeek falló, Kimi K3 (juez) entregó la decisión ("# Decisión del consejo ...") en unos 13 s.
- Comprobado: pedir un modelo que no existe da error y no cambia de modelo (cumple la ficha 1).
- NO hecho: conectar al harness de DeepSeek; selector del chat; espera de NVIDIA a 108 s (ver duda 11).
- Router vivo no se tocó. Vercel: solo máquinas temporales de puente, apagadas.

### Salida 3b - modelos que responde NVIDIA hoy (2026-10-04, ~16:10)
- Probados 58 de los 81 modelos del catalogo NVIDIA (se saltaron embeddings, seguridad, vision y similares) con una pregunta corta y hasta 105 s de espera.
- RESPONDEN (13), con su tiempo: google/gemma-4-31b-it 28,6 s; meta/muse-glimmer-30b 1,5 s; moonshotai/kimi-k3 35,7 s; nvidia/ising-calibration-1.5-31b 0,5 s; nvidia/nemotron-3-nano-omni-30b-a3b-reasoning 0,8 s; nvidia/nemotron-3-super-120b-a12b 0,5 s; nvidia/nemotron-3-ultra-550b-a55b 4,4 s; nvidia/nemotron-3.5-lightning-30b-a3b 2,6 s; nvidia/riva-translate-4b-instruct-v1.1 5,5 s; nvidia/riva-translate-4b-instruct-v2 24,1 s; openai/gpt-oss-20b 2,5 s; poolside/laguna-xs-2.1 0,2 s; z-ai/glm-5.3 8,2 s.
- NO RESPONDEN HOY (45): deepseek-ai/deepseek-v4.1-flash, deepseek-ai/deepseek-coder-6.7b-instruct, moonshotai/kimi-k2.6, z-ai/glm-5.3-flash, nvidia/nemotron-nano-3-30b-a3b, nvidia/llama-3.1-nemotron-ultra-253b-v1, nvidia/llama-3.1-nemotron-70b-instruct, nvidia/llama-3.1-nemotron-51b-instruct, nvidia/nemotron-4-340b-instruct, mistralai (large, large-2, codestral, mixtral, 7b), nv-mistralai/mistral-nemo-12b-instruct, writer/palmyra (4 modelos), ibm/granite (4), google (codegemma x2, gemma-2b, gemma-3 x2, recurrentgemma, diffusiongemma), meta/codellama-70b, meta/llama2-70b, 01-ai/yi-large, ai21labs/jamba, aisingapore/sea-lion, bigcode/starcoder2, databricks/dbrx, microsoft/phi-3.5-moe, zyphra/zamba2, nvidia (riva-translate-4b-instruct, vila, cosmos-reason2-8b, llama3-chatqa, mistral-nemo-minitron-8b, ai-synthetic-video-detector).
- Conclusion: DeepSeek no responde por NVIDIA hoy. Esperando que el Director diga como cambiar a DeepSeek (duda 10).

### Siguiente tarea
- Terminar la salida 3: conectar las fichas 1 y 2 al harness de DeepSeek (leer `chat router/harness plugins/deepseek-harness-chat/plugins/router-provider.cordis.yml` y el token que usa el harness), revisar y confirmar. Antes: esperar la decisión del Director sobre DeepSeek (duda 10) y la espera de NVIDIA (duda 11). Después: salida 4 (fichas 3, 3.1 y 4).

## 6. Parche de recuperación (pegar al iniciar una sesión nueva de cualquier IA)
```
Eres agente del Director (Hy). Antes de hacer NADA:
1. Lee completo "Claude notas/claude notas 1.md" (rama main). Las secciones 1 y 4 son órdenes textuales del Director: no las cambies ni las resumas.
2. Reglas: NO tocar ni relanzar el Router de HF; fichas como plugin/ficha JSON (sin parches al Router); fichas 0-2 en GitHub, 3/3.1/4 en HF;
   claves solo del banco; Vercel solo puente (ni una letra sin autorización); sin GitHub Actions; NVIDIA espera 108 s;
   ficha 1 rota claves del mismo modelo y nunca cambia de modelo (sin claves: mensaje de error); ficha 4 como en 4.5;
   Nemotron 3.5 Lightning va por NVIDIA, no se baja a HF; revisar qué ya está hecho antes de crear; no bajar modelos que no corran en su GPU.
3. Orden: una salida por paso (4.4). Parte 1 (fichas 0-2) → Parte 2 (fichas 3, 3.1, 4 + modelos locales) → Parte 3 (APK ChatGPT). Salidas 1 y 2 hechas; salida 3: fichas montadas, falta harness y decisión DeepSeek.
4. Anota cada orden nueva del Director TEXTUAL en este archivo ANTES de trabajar.
5. Respuestas cortas (máx. 10 líneas), en español sin código. Explica cómo lo harás antes de hacerlo. Si dudas, pregunta en texto.
```
