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
