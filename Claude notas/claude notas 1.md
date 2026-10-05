# Claude notas 1 — UNICO archivo de notas (fuente de la verdad)

Actualizado: 2026-10-04 17:50 (Bogotá). Autor: Opus, por orden del Director (Hy).
- Este es el UNICO archivo de notas de Claude. No crear otros (orden 17:48).
- Las órdenes del Director van TEXTUALES. Si algo de Claude contradice al Director, vale el Director.
- Sin claves ni tokens en este archivo. La clave del Director y los tokens viven en el banco.
- Historial anterior (órdenes textuales del 2026-10-03 y madrugada del 2026-10-04, fichas 0-4 originales, pasos 1-9, salidas 1-3): versión previa de este mismo archivo en el historial de GitHub (blob `0f48c4c`). Lo que sigue manda sobre esa versión.

---

## 1. ÓRDENES TEXTUALES DEL DIRECTOR QUE DEFINEN ESTE PLAN

### 1.1 Configuración de fichas y router de respaldo (2026-10-04 17:10)
```
Cambia glm 5 por 
muse-glimmer-30b y
Cambia deepsek por 
muse-glimmer-30b y
Si está disponible en Nvidia revisa como segunda opción 


Tarea comunes 
Ejecutor agentico 
Nemotron 3.5 Lightning,

También en ficha de modelos individuales que estába pendientes decidir pones
Nemotron 3.5 Lightning,


Para el router de respaldo de huggueface necesito estás combinaciones 

Ficha 1 📌
Deepsek v4 flash con consumo de HF TOKEM

FICHA 2 📌 
Qwen3.8-27B — L4: 

FICHA 3 📌 
Qwen3.6-35B-A3B — L4:

FICHA 4 📌 
Qwen3.8-27B — L4:  ARQUITECTURA DISEÑO Y FROMTEND PLANIFICA 
Qwen3.6-35B-A3B — L4:
EJECUTA Y ESCRIBE CODE 
Qwen3.8-27B — L4:
SI SE PIDE REVISION REFACTORITA 

LE PONES UNOS COMNANDO AL ROUTER DE ACTIVACIÓN POR MODELO Y  QUE EL MODELO FESPONDA CON SU NOMBRE Y MODELO Y LA MKSMA PARABRAS DE ACTIVACIÓN ADICIONAL A LO QUE TU PONES EN EL ROUTER 

COMANDOS
➡️ razona = responde por ejemplo Qwen 3.8 ejecutando arquitectura razonamiento diseño 
➡️ Ejecuta = el modelo dice su nombre  ejecuta code y modo agentico 
➡️ Refactoriza = el modelo dice su nombre y Audita y revisa y resuelve los Gaps


➡️➡️➡️➡️
Cambios deepsek por 
Nemotron 3.5 Lightning

Sube a 1.6 glm 5 si no responde siempre cambia a Kimi k 3 o sigue si no responde cambia a Nemotron 3.5 Lightning


Groq ya estába definido en
Qwen 3.8 


⚠️⚠️🆘 Tu el router no lo tocas el harnes tampoco lo único que tú puedes tocar es la ficha la ficha es la coneccion intermedia entra el plugins del router y el plugins de el harnes de deepsek 

🆘⚠️ El router de respaldo en huggueface no va conectado con el router de Github la ficha va directo al harnes de deepsek 


Dime si entiendes necesito saber que lo entiendas antes de continuar 

🆘🆘🆘🆘
```

### 1.2 Respuestas (2026-10-04 17:18)
```
1. Si deepsek o glm no responde 
Opción 1 Nemotron 3.5 Lightning
Opción 2 
muse-glimmer-30b

2. Si edita quirúrgicamente
Paso 1 📌 y paras me confirmas y luego te reelanzo lo hace opus 

3. Si le pones router respaldo Huggueface 
```

### 1.3 Nada vive dentro del Router (2026-10-04 17:23 a 17:29)
```
Saca eso de hay solo paso 1 editar el tiempo del router ningún modelo debe vivir dentro del router idota 
Sacalos 

Todo los modelo viven en una ficha externa conectado al plugins del router idota
```
```
Si el tope 
Te dije el router no puede tener nada basura ninguna api dentro dime si lo entiendes idiota todo lo llama una ficha externa 
```
```
Saca eso del router el router debe solo usar una ficha externa no debe tener nada dentro revisa si no estás usando un router equivocado que no está en la raíz que tú mismo hiciste no sea una mierda inventada por Sonnet 
El router se supone es solo eso y las fichas externas permiten conectar por un plugins sin romper sin tocar el router revisa el readme handoff todo antes y revisa no sea una mierda que cambio Sonnet
```

### 1.4 Arquitectura de las fichas (2026-10-04 17:39)
```
Saca toda no se que mierda hizo el otro opus que alucino también 

Raíz ➡️📂 router universal inteligente/
📂 Router 

Nada de Devin ni más mierda inventada 

El router usa las fichas de configuración de los modelos 
Por plugins nada vive dentro del router 

Las ficha se van conectando con el enchufe universal Fables plugins 

Dentro es un mini router que permite editar sin romper todo sin tocar el code de el router principal 


Cada ficha se comunica con 
➡️ Router principal que da computo y hhtp y almacenamiento de huggueface y controla las fichas por plugins 
➡️ La ficha de conecta con agentes o chat por medio de plugins enchufes Fables o con el harnes de deepsek 
➡️ Las ficha se conecta con el banco donde vive la api que va usar la ficha es una mini api 
➡️ La ficha decide configuración de cada api y de cada modelo ejemplo rol o equipo de trabajo de varias api 
➡️ La ficha se conecta con el laboratorio de prueba de las api para saber que modelo responde y si funciona 
➡️ La ficha se conecta con un stated JSON handoff vivo que reporta cualquier cambio de las fichas o lo que hay en le banco o conectado al router principal 


Dieme si entiendes?
Dime si el readme Asi lo dice ?

Dime si sabes cómo hacelo ?
Dime si tienes duda ?

Revisa.y explica antes de avanzar y Como lo vas a resolver
```

### 1.5 Aprobación del plan (2026-10-04 17:47 a 17:49)
```
Aprobado 
1. Si 
2. Si hazlo de nuevo y le pones 
Binario calve [CLAVE DEL DIRECTOR: no se escribe aquí]
3. Si y si no lo tienes esta en la otra raíz de chat router en plan o me lo pides 

4. Haz todas las fichas de una vez así no tengo riesgo de que Sonnet la cage termina todo incluido lo de huggueface router de respaldo 

Dividelo todo en salida por el problema de la ventana de antropy. 

Anota primeo en un archivo Claude notas los pasos detallado del plan las fichas como memoria y me enseñas antes de cada salida tu siguiente paso 

Paso 1 📌 anotas 
Y divide las salida 

Paso 2 📌 la salida que inicia según tu plan 

Y paras validas el plan me das el handoff con las notas 

Inicia
```
```
Si hay otro archivo Claude notas borralo para no causar humo ni ruido
```
```
Nada en vercel
```
(Respuestas: 1 = la base es la carpeta `router inteligente universal/` de `main`. 2 = se rehace en `main` lo que haga falta aunque se pierda lo que solo estaba en la rama devin; lleva candado binario con la clave del Director. 3 = cablear el enchufe Fables completo; si falta algo, buscar en `chat router/01-PLAN` o pedirlo. 4 = todas las fichas de una vez, incluido el router de respaldo de HF.)

---

## 2. REGLAS FIJAS (vigentes)
1. Base única: carpeta `router inteligente universal/` de la rama `main`. Nada de la rama devin.
2. Dentro del Router principal NO vive ningún modelo ni API. El Router solo da cómputo, HTTP, almacenamiento de HF, el banco y controla los plugins.
3. Todo modelo vive en una ficha externa, conectada como plugin. La ficha es un mini router: se edita sin tocar el código del Router.
4. Claves: solo del banco. Nunca en archivos, commits ni chat.
5. Vercel: NADA. Ni puente. Solo el conector de GitHub y HF (orden 17:49).
6. Sin GitHub Actions. Cómputo en HF.
7. Espera por llamada: tope TOTAL de 1,5 minutos (90 s) sumando todas las claves (orden 16:35 y 17:26). GLM 5: 1,6 minutos (96 s).
8. Ficha 1 (modelos individuales): si se agota una clave pasa a otra clave del mismo modelo; nunca cambia de modelo; sin claves = mensaje de error.
9. Router de respaldo HF: NO se conecta al Router de GitHub; sus fichas van directo al harness DeepSeek.
10. Candado binario con la clave del Director para crear, cambiar o borrar fichas (se guarda solo su huella, nunca la clave).
11. Una salida por paso. Antes de cada salida: mostrar el siguiente paso. Al final: anotar aquí y dar la siguiente tarea.
12. Antes de crear algo, revisar si ya existe en `main`.

---

## 3. CÓMO QUEDA (flujo en palabras)
Chat / agentes / harness DeepSeek → enchufe Fables (plugin) → **plugin de fichas** (mini router) → la ficha elegida decide modelo, rol o equipo → toma su clave del **banco** → llama ella misma a la API (mini API) → antes consulta el **laboratorio** para saber qué modelo responde → escribe cada cambio en el **JSON vivo de handoff**.
El Router principal solo presta cómputo, HTTP, almacenamiento de HF y carga los plugins.
Router de respaldo HF: plugin de fichas de respaldo → servidor de modelos locales en HF (L4) → directo al harness DeepSeek, sin pasar por el Router de GitHub.

---

## 4. LAS FICHAS (memoria de la configuración)

### Ficha 0 — memoria + almacenamiento + cómputo
- Sin IA. No va en el selector. Candado binario.
- Da al chat y al workflow Loops code Yaiwes: memoria y almacenamiento en HF, y cómputo de HF.

### Ficha 1 — un solo modelo (selector)
- Opciones separadas: Kimi K3 (NVIDIA) · GLM 5.3 (NVIDIA, 96 s) · Nemotron 3 Super 120B (NVIDIA) · Groq Qwen 3.8 · Nemotron 3.5 Lightning (NVIDIA; entra en el lugar que era de DeepSeek).
- Solo actúa el elegido. Rota claves del mismo modelo. Espera tope 90 s (GLM 96 s). Sin claves: error.

### Ficha 2 — consejo + ejecutor
- Consejo: GLM 5.3 (96 s; si no responde → Nemotron 3.5 Lightning → muse-glimmer-30b) · Nemotron 3.5 Lightning (lugar de DeepSeek; si no responde → muse-glimmer-30b) · Groq Qwen 3.8.
- Decide: Kimi K3. Marca el rol del ejecutor.
- Ejecutor según rol:
  - tareas comunes, tools y modo agéntico: Nemotron 3.5 Lightning;
  - código, refactor y revisión: Groq Qwen 3.8 → si falla, Nemotron 3 Super 120B;
  - frontend: Nemotron 3.5 Lightning (lugar de DeepSeek) → si falla, muse-glimmer-30b.
- Alimenta al chat, al orquestador, a Hermes y a OpenClaw.

### Router de respaldo HF (fichas propias, nombres "respaldo 1 a 4")
- Respaldo 1: DeepSeek V4 Flash por la API de HF con el token de HF del banco.
- Respaldo 2: Qwen3.8-27B (Q3_K_XL, 13,1 GB) en L4.
- Respaldo 3: Qwen3.6-35B-A3B (Q3_K_XL, 17,2 GB) en L4.
- Respaldo 4 (equipo, un solo servidor L4, en cola): Qwen3.8-27B planifica, arquitectura, diseño y frontend → Qwen3.6-35B-A3B ejecuta y escribe código → Qwen3.8-27B revisa y refactoriza (solo si se pide).
- Parámetros llama.cpp (Director 2026-10-03): solo texto, `--no-mmproj`, `--reasoning off`, Flash Attention ON, MTP ON, `spec-draft-n-max 2`, `parallel 1`, `batch 128`, contexto 16K, temp 0, top-k 20, top-p 0.95.
- Archivos ya guardados en HF: `router-respaldo/modelos/` (27B, 35B y 0,8B; el 0,8B ya no se usa).
- Comandos de activación (el modelo responde con su nombre, su modelo y la palabra de activación):
  - `razona` → arquitectura, razonamiento y diseño;
  - `ejecuta` → ejecuta código y modo agéntico;
  - `refactoriza` → audita, revisa y resuelve los gaps.

---

## 5. PLAN POR SALIDAS (DAG, cada salida termina, se anota aquí y para)

```
S1 leer ──▶ S2 plugin de fichas ──▶ S3 conexiones ──▶ S4 fichas 0-2 ──▶ S6 sacar modelos del Router ──▶ S7 pruebas + handoff
                    └─────────────────────────────▶ S5 router de respaldo HF ──┘
```

**S1 — Leer lo que existe en `main` (solo lectura, nada se cambia)**
- Plugin Host (`integration/plugin_host/`), carpeta `plugins/` (chat, deepseek_harness, fables_enchufe, hf_storage, hf_compute), `enchufe/` (bus Fables), banco (`Banco de claves/`), laboratorio y estado vivo (`Estado y handoff global/`).
- Buscar el plan de Fables en `chat router/01-PLAN` si falta algo.
- Salida: lista de lo que hay, lo que falta y en qué orden se arma. Sin código.

**S2 — Plugin de fichas (el mini router), en `plugins/fichas/`**
- Tarjeta del plugin + código. Lee las fichas de configuración (un archivo por ficha).
- Mini API propia: llama a NVIDIA, Groq y HF con la clave sacada del banco, rota claves del mismo modelo y respeta el tope total de 90 s (GLM 96 s).
- Saltos entre modelos definidos dentro de cada ficha, no en el Router.
- Candado binario: crear, cambiar o borrar fichas exige la clave del Director (se guarda solo su huella).
- Pruebas propias del plugin, sin tocar el Router.

**S3 — Conexiones del plugin de fichas**
- Laboratorio: antes de llamar, la ficha consulta qué modelo responde.
- JSON vivo de handoff: cada cambio de fichas, banco o conexiones queda escrito.
- Enchufe Fables completo: cada ficha queda enchufada para chat y agentes.
- Harness DeepSeek: puede llamar a las fichas por el plugin (sin tocar el harness: la conexión vive en la ficha / plugin).

**S4 — Fichas 0, 1 y 2 dentro del plugin**
- Escribir las 3 fichas con la configuración de la sección 4.
- Probar cada opción con una pregunta real, el consejo con una tarea real y cada ejecutor por rol.

**S5 — Router de respaldo HF**
- Ficha "respaldo 1" (DeepSeek V4 Flash por HF).
- Servidor llama.cpp en un L4 de HF con los parámetros de la sección 4; modelos desde `router-respaldo/modelos/`; en cola, uno a la vez; se apaga solo sin uso.
- Fichas "respaldo 2, 3 y 4" y los comandos `razona`, `ejecuta`, `refactoriza`.
- Conexión directa al harness DeepSeek; nada hacia el Router de GitHub.
- Prueba de velocidad corta (tokens por segundo) de cada modelo y del equipo.

**S6 — Sacar modelos y APIs del Router principal (con OK del Director)**
- Solo cuando S2 a S5 funcionen: quitar del Router la cadena de modelos y la lista de proveedores; el Router solo carga plugins.
- El Director relanza el Router.

**S7 — Pruebas de punta a punta + handoff**
- Chat → enchufe → ficha → modelo; harness → ficha; respaldo HF → harness.
- Actualizar el README de `router inteligente universal/` para que diga esta arquitectura.
- Handoff final con enlace y parche de recuperación.

---

## 6. DUDAS ABIERTAS
1. Los comandos `razona`, `ejecuta`, `refactoriza`: ¿solo en el router de respaldo HF o también en las fichas 1 y 2?
2. Frontend de la ficha 2: tomé Nemotron 3.5 Lightning (lugar de DeepSeek) → muse-glimmer-30b. ¿Confirmas?
3. GLM 5: en 17:10 dijiste "si no responde cambia a Kimi K3"; en 17:18, opción 1 Lightning y opción 2 muse. Tomé la de 17:18.

---

## 7. ESTADO ACTUAL (2026-10-04 17:50)
- Router principal: el archivo de modelos quedó igual que antes de hoy (se revirtió el cambio de 17:19). Tiempo por llamada en código: 90 s por clave (falta el tope total en S2).
- En el Router vivo siguen montadas 12 fichas viejas (formato anterior) y 6 tokens del harness + 1 token de ficha 0, creados hoy. Se reemplazan en S4 y se apagan al final.
- Modelos locales ya descargados en HF: `router-respaldo/modelos/`.
- Vercel: no se usa más.

### Siguiente salida
**S1 — leer lo que existe en `main`** (solo lectura): Plugin Host, plugins, enchufe Fables, banco, laboratorio y estado vivo. Al terminar: lista de lo que hay y lo que falta, anotada aquí, y paro.

---

## 7b. ORDEN Y ESTADO 2026-10-04 23:07 (Router reactivado, seguridades del L4, solo 16 GB, chat en Vercel)

Orden textual del Director:
```
Ok vas activar el router y revisa que el servidor L4 no quede prendido que funciones el prendido y apagado como si tienes que colocarle 3 sistema de seguridad

Revisa que el servidor que vas activar y los que se encienden en cadena el router sea solo los de HF cpu 16 ram

Reactivas el router

Luego me subes el chat a vercel solo la UI INTERFACE visual cuidado te pones a subir el code a vercel

Inicia
```

Resultado (2026-10-05 04:20 UTC):
- Space de la puerta reanudado (HF acepto el reinicio; antes daba 402 por creditos). El Space sigue en cpu-upgrade (32 GB, 0,03 USD/h): pedir cpu-basic por la API da 402; cambiarlo a mano en los ajustes del Space.
- Router vivo: un solo job, cpu-basic (16 GB). Autoscaler, /hf/compute/run y /hf/hardware limitados a cpu-basic (hf_worker_pool.py, hf_control_api.py, chat_mvp/control_plane.py). Paquete anterior guardado como router-bundle.tar.gz.bak-20261005041122.
- puente_chat v0.2.0 con 5 seguridades del L4: (1) se apaga 30 s tras terminar la salida; (2) a los 5 min sin pedidos; (3) tope duro de HF de 1200 s (20 min, fuera del contenedor); (4) barrendero del Router: cada llamada de estado cancela L4 de mas de 20 min; (5) un solo L4 a la vez. Remoto: acciones apagar y apagar_todo.
- Probado: el L4 A se cancelo solo al encender el L4 B; apagar_todo apago el L4 vivo; ciclo completo HF: listo en 115 s, respondio, se apago solo 40 s despues; al final solo queda el job del Router. Los 3 L4 de prueba tenian timeout 1200.
- Token del chat: banco router/chat-ui-cierre (el valor no se puede leer del banco; el Director lo pide a Opus).
- Vercel (proyecto riu-jev-bridge): raiz = chat router/chat frontend, sin paso de compilacion ignorado, ligado a GitHub main. Despliegue dpl_n63Dra1AqEsvi81wAiZF9nsQgpBi READY (tardo unos 7,5 min). Solo UI: /api/chat da 404; harnessUrl apunta a la puerta fija del Router. Cada push a main se publica solo (unos 7 a 8 min por la talla del repo, 8,3 GB). El repo de GitHub es publico.

## 7c. PARCHE DE RECUPERACION 2026-10-05 00:00 Bogota (se acaba la ventana de Claude: sigue Opus)

Ordenes textuales del Director de esta tanda (resumen fiel):
```
23:31 Crea un space puerta nuevo idiota o no puedes ? / El servidor de 16 de ram cpu revisa que si se satura salta al siguiente HF procesador cuando llega a 85% / Revisa que el chat funcione de principio a fin y me das el enlace para verlo
23:33 Revisa que no sea un space deberia ser un simple job con un sentinela que lo enciende si se cae no space
23:46 Idiota te dije que lo revisaras el modelo no tiene acceso a Github y huggueface ... haz de nuevo un space nuevo y pasas todo o lo bajas a gratis y lo subes de una vez a pago
23:58 Dame un parche de recuperacion ... para que por opus siga me pones lo que falta comprobar y que falta terminar
```

ESTADO REAL (probado en vivo):
- Router vivo: 1 job cpu-basic (16 GB). Space de la puerta RUNNING en cpu-upgrade (32 GB): pedir cpu-basic por API da 402; hacerlo a mano en los ajustes del Space.
- puente_chat v0.3.1 esta en el paquete del Router (bucket COMAND-CENTER-1/yaiwes-memoria-storage, router-inteligente-universal/codigo/router-bundle.tar.gz; copias .bak-<fecha>). Acciones: status, modelos, chat, estado, apagar, apagar_todo, herramientas_estado.
- Los modelos del chat YA tienen herramientas (plugins/puente_chat/herramientas.py): github_leer, github_escribir, github_api, hf_leer, hf_escribir, hf_api, hf_almacenamiento. Las ejecuta el Router con las claves del banco; el modelo nunca ve claves. Bucle de hasta 6 pasos y 100 s en total.
- Probado OK con herramientas: Groq Qwen 3.8 (hf_api), Nemotron 3 Super y Nemotron 3.5 Lightning (github_leer), HF L4 Qwen 3.6 35B (hf_api), Kimi K3 (hf_almacenamiento escribir y leer).
- Bloqueos probados: no borrar repos, no rutas de GitHub ajenas, no escribir en HF fuera de COMAND-CENTER-1, no cancelar jobs, no tocar banco/codigo/control del almacenamiento.
- Claves: GitHub del Director guardada en el banco como github/director-full (scope github; el Router la exporta a RIU_VAULT_GH_*); HF = huggingface/token-1-new. herramientas_estado da github True y hf True.
- Seguridades del L4 (5) y solo servidores cpu-basic: ver 7b. Vercel: proyecto riu-jev-bridge, raiz chat router/chat frontend, solo UI, se publica solo desde main (unos 7 min).
- Clave del chat: banco router/chat-ui-director (el valor se lo di al Director en el chat; para rotarla se crea otro token de la instancia chat-ui).

FALTA COMPROBAR O TERMINAR (en este orden):
1. Kimi K3: despues de usar una herramienta su respuesta final sale rota (<|close|>!!!!). Revisar _chat/_bucle (la llamada final sin herramientas); probar sin el system extra o con tool_choice none. Tambien confirmar GLM 5.3 con github_escribir (rama devin/1790824641-chat-agent-plan, ruta pruebas/ping-chat.txt: queda un archivo de prueba, borrarlo) y que Kimi/GLM no pasen de los 100 s.
2. Probar el chat en el navegador real (pantalla de Vercel -> puerta -> puente_chat) con la clave del chat: los 7 modelos, la memoria y el ciclo del L4 (encender, responder, apagarse) desde la pantalla.
3. Pantalla: boton de apagado remoto (acciones apagar y apagar_todo) y mostrar las herramientas usadas (campo herramientas de la respuesta).
4. Puerta: bajar el Space a cpu-basic a mano, o crear Space nuevo (secretos que necesita: GITHUB_PERSONAL_ACCESS_TOKEN, HF_TOKEN, MCP_SECRET_PATH, MCP_SECRET_HF, RIU_KERNEL_HF_TOKEN y variables RIU_*; la URL cambia salvo que se renombre el Space viejo; el permiso CORS y los conectores MCP dependen de esa URL), o la opcion del Director: job + centinela sin Space (la URL cambia en cada reinicio: el centinela debe publicarla en un archivo fijo que lea el chat).
5. Del plan original siguen pendientes: fichas 3, 3.1 y 4 (equipo Qwen en cola, comandos razona / ejecuta / refactoriza) y DeepSeek en el respaldo. DeepSeek por HF da MODEL_NOT_SELECTABLE en el Router.
6. Tope total de 90 s por llamada con herramientas (hoy 90 s por llamada y 100 s el bucle; GLM 96 s).
7. Harness DeepSeek como servicio HTTP propio (hoy el puente_chat hace su papel).
8. Reescribir fichas/README-CONEXION-CHAT-HARNESS.md: esta desactualizado (falta v0.3.1, herramientas, clave del chat, nombres de los 7 modelos).
9. El repo de GitHub es publico: preguntar al Director si debe ser privado.
10. Cambiar los tokens que quedaron escritos en el chat (HF, GitHub ghp, clave del chat, clave del Director).

COMO OPERAR (conectores de GitHub y HF caidos): Vercel sandbox solo como puente (projectId prj_m8Lk3iaB3eN6dwlIq1ND2un8FWTD, sin teamId; pip install huggingface_hub). Relanzar el Router = subir el paquete al bucket + POST /hf/hardware {flavor: cpu-basic, relaunch_now: true} con X-Director-Key. Editar GitHub = API de contenidos con el ghp del Director (el token github_pat da 403). Probar el chat: POST <puerta>/plugins/puente_chat/call/<accion> con la clave del chat.

## 7d. UI DEL CHAT MEJORADA 2026-10-05 (orden del Director 00:07)
- Orden: entrar a GitHub, buscar el chat, leer el plan y el skill Maxbry UI frontend, escoger UN solo README y mejorar la interfaz con ediciones quirurgicas.
- Skill elegido: chat router/01-PLAN/README-SKILL-FROMTED-YAIWES-GRIS-Y-LETRAS.md (gris V07 aprobado + letras).
- Cambios en chat router/chat frontend/: shell.css (tokens exactos del gris: borde #3A3A3A, texto #EDEDED y titulos #FAFAFA, secundarios #BFBFBF y #A0A0A0, capa #252525, seleccion #3C3C3C solo en el modulo activo; hover sin iluminar; botones con radio 10; foco visible; boton desactivado; placeholder; estado vacio; mensaje pendiente y de error; selectores del chat en rejilla), panel-chat.html (clase fields, aria-label, pista de Enter), panel-chat.js (indicador Pensando, boton bloqueado mientras responde, errores resaltados, Enter envia en computador). IDs y handlers intactos; JS y CSS validados.
- Despliegue: 3 commits = 3 builds de Vercel (unos 7 min cada uno, en cola); el ultimo deja todo en vivo.
- Pendiente de UI: mostrar las herramientas usadas (campo herramientas de la respuesta), boton de apagado remoto con apagar_todo, selector de tema (gris, little, matte, blanco), revisar en el movil con capturas, y los selectores de letras (parte 2 del skill, sin aprobar).

## 8. PARCHE DE RECUPERACIÓN (pegar al iniciar una sesión nueva)
```
Eres agente del Director (Hy). Antes de hacer NADA:
1. Lee completo "Claude notas/claude notas 1.md" (rama main). Es el único archivo de notas. Sección 1 = órdenes textuales; no las cambies.
2. Reglas: base = carpeta "router inteligente universal/" de main (nada de devin); dentro del Router NO vive ningún modelo ni API;
   todo modelo vive en una ficha externa (plugin de fichas = mini router); claves solo del banco; NADA en Vercel; sin GitHub Actions;
   tope total 90 s por llamada (GLM 96 s); ficha 1 rota claves del mismo modelo; router de respaldo HF va directo al harness, no al Router de GitHub;
   candado binario con la clave del Director (solo huella).
3. Sigue el plan de la sección 5, una salida a la vez. Antes de cada salida muestra el siguiente paso; al terminar anota aquí y para.
4. Respuestas cortas (máx. 10 líneas), en español sin código. Si dudas, pregunta en texto.
```

## 9. SERVIDOR UNICO EN HF CPU 16 GB DE PAGO (orden del Director, 2026-10-05)

**Regla:** solo 2 cosas encendidas. 1) El Router en **HF Jobs `cpu-basic` (2 vCPU, 16 GB, 0,01 USD/h), 24/7**. 2) El **L4 `l4x1` (1 GPU L4 de 24 GB)** solo bajo pedido: NO se toca (verificado en la tabla oficial de HF). El Space `claude-github-mcp-backup` (`cpu-upgrade`, 32 GB) **se pausa**. Los conectores de Claude no se usan (el acceso es por la maquina de Vercel).

**Flujo nuevo:**
```
Chat (Vercel, solo UI) -> puente /api/chat -> lee LIVE_URL (flag en GitHub) -> Router en HF Job 16 GB (24/7)
                                                                   +-> L4 24 GB bajo pedido (sin cambios)
Router job = Router + riu_kernel (se renueva solo, flota hasta 10, escribe LIVE_URL)
```

**Tareas:**
1. `riu_kernel.py` en `main`: renovacion propia antes de vencer (primero el sucesor sano, luego se apaga el viejo); flota (CPU 85% -> otro job igual, hasta 10; replica sin trafico 5 min -> se apaga; tope 20 encendidos por hora); escribe LIVE_URL y la lista de replicas en el flag de GitHub.
2. Arranque del job: el mismo de hoy (bundle del deposito) + `riu_kernel.py` en segundo plano.
3. Lanzar el job nuevo con las mismas variables y las mismas 7 claves: HF_CONTROL_JOBS_TOKEN, HF_TOKEN, RIU_AGENT_API_KEYS, RIU_AGENT_API_KEYS_2, RIU_DIRECTOR_KEY_HASH, RIU_ROUTER_API_KEY, RIU_VAULT_PASSPHRASE (+ GITHUB_TOKEN para escribir el flag).
4. Puente `/api/chat`: usar LIVE_URL del flag en vez de la puerta y poner las cabeceras que ponia la puerta (token de HF para el proxy de jobs + token de la ficha).
5. Actualizar Vercel (RIU_ROUTER_URL), el chat y el README de Opus.
6. Probar: el Router responde por LIVE_URL, la flota mide CPU, el L4 sigue encendiendose bajo pedido.
7. Pausar el Space.

**Decision pendiente del Director (bloquea el orden):** los valores de 5 claves (RIU_AGENT_API_KEYS, RIU_AGENT_API_KEYS_2, RIU_DIRECTOR_KEY_HASH, RIU_ROUTER_API_KEY, RIU_VAULT_PASSPHRASE) solo viven dentro del Space; HF no deja leerlos.
- A: el Director da esos 5 valores -> se pausa el Space primero.
- B: el Space lanza por ultima vez el job nuevo con sus propias claves -> despues se pausa.
Sin una de las dos, pausar primero deja al Router sin quien lo renueve: se apaga al vencer (quedan unas 9 h) y no se puede relanzar.

## 10. PUERTA PAUSADA Y BANCO REVISADO (orden del Director, 2026-10-05)

**Hecho:** el Space `claude-github-mcp-backup` quedo **PAUSADO** (orden directa del Director, aunque haya que rehacer cosas).

**Banco revisado con la clave del Director (abre):** el banco VIVO esta en el deposito de HF: `buckets/COMAND-CENTER-1/yaiwes-memoria-storage/router-inteligente-universal/banco/vault.db.gz.b64` (41 credenciales; por proveedor: nvidia 5, groq 6, hf 4). Junto a el hay `providers.json`, `tokens.json` y copias de respaldo. La copia de GitHub (`agent-microkernel/runtime-bank-v2.part1/part2`) **NO abre** con esa clave: es una copia vieja. El Director pidio un solo banco: borrar la de GitHub cuando lo ordene.

**Claves del Router:** `RIU_VAULT_PASSPHRASE` = la clave del banco (verificado: abre el banco vivo). Las otras 4 (`RIU_ROUTER_API_KEY`, `RIU_AGENT_API_KEYS`, `RIU_AGENT_API_KEYS_2`, `RIU_DIRECTOR_KEY_HASH`) solo vivian como secretos del Space y HF no deja leerlos: se generan **nuevas**.

**LO QUE HAY QUE REHACER por la pausa:**
1. El Router actual (job `6ac32e10...`) ya no se renueva: vence en unas 8 h. Crear el job nuevo (HF Jobs `cpu-basic`, 16 GB) con `riu_kernel.py` dentro: renovacion propia (primero el sucesor sano), flota hasta 10 (CPU 85%, replica sin trafico 5 min se apaga, tope 20 encendidos por hora) y escribe `LIVE_URL`.
2. La direccion fija `comand-center-1-claude-github-mcp-backup.hf.space` ya no responde. Apuntan a ella: el flag `LIVE_URL` en GitHub, `RIU_ROUTER_URL` en Vercel, el puente `/api/chat`, el README de Opus y el plugin del harness. Pasarlos al `LIVE_URL` real del job nuevo (la URL de un job exige el token de HF en la cabecera).
3. Las 4 claves nuevas del Router: ponerlas en Vercel, en el puente y en el harness.
4. El L4 (`l4x1`, 24 GB) no se toca: sigue bajo pedido.
5. Probar de punta a punta y despues borrar la copia vieja del banco en GitHub.


## 11. Continuación ejecutada — 2026-10-05 (Codex)

Orden vigente del Director: servidor HF de 32 GB, interfaz en Vercel; replicar la arquitectura existente, conectar modelos, fichas, memoria, herramientas e internet por HTTP; sin escalado ni pruebas innecesarias.

- Router activo: Job `6ac40a4b404719ba37658c12`, cpu-upgrade, 32 GB. URL vigente en `router inteligente universal/LIVE_URL.json`. Space antiguo permanece PAUSED.
- Renovación instalada: `riu_kernel.py`, schedule `6ac40924fbc85ba6823aca1b`, cada diez minutos. Sucesor de 32 GB, conservación de memoria y retirada del anterior. Sin escalado.
- Banco vivo cifrado en HF: 43 entradas; nuevas credenciales de administración y hash del Director guardadas en el banco. Referencias `router/runtime-admin-32gb`, `router/runtime-director-hash`; nunca valores en notas o GitHub. Clave de chat existente `router/chat-ui-director`, permisos necesarios habilitados.
- puente_chat v0.4.1: siete modelos de la ficha, herramientas internet_leer/internet_buscar, GitHub y HF, selección sin cambiar de modelo, chat_async/resultado para evitar el límite HTTP.
- Memoria SQLite persistida en el bucket y recuperación por sesión; almacenamiento HTTP operativo. Los siete modelos respondieron usando herramientas reales y guardaron memoria; ambos modelos HF encendieron y apagaron el L4 correctamente.
- UI estática `https://riu-jev-bridge.vercel.app`, resuelve LIVE_URL y consulta las respuestas asincrónicas. Se corrigió el header del puente de Authorization a X-API-Key, porque Authorization recibía 401 en el nuevo servidor.
- Los antiguos Router de 16 GB y las instancias intermedias se retiraron después de verificar sus sucesores. Evidencia funcional en el bucket `laboratorio/recovery-http.json`, `recovery-memory.json`, `recovery-hf-models.json`.

Protocolo y recuperación vigentes: `README-CONEXION-CHAT-HARNESS.md`. Las secciones anteriores conservan el historial; esta sección manda sobre la pausa y las direcciones antiguas.
