# README — Conexión del chat y el harness DeepSeek a las fichas (para el equipo de la UI)

Fecha: 2026-10-04 (Bogotá). Escrito por Opus por orden del Director (Hy). Todo lo de aquí está **probado en vivo**.
Sin claves en este archivo: todos los tokens viven en el banco del Router (se dan los nombres de referencia).

---

## 0. RESPUESTA AL EQUIPO DE LA UI (2026-10-04 20:15) — leer primero

### 0.1 `harnessUrl`: hoy el harness NO tiene dirección HTTP
- El harness DeepSeek (`dsh`) es un **programa de terminal**: se ejecuta con `dsh headless ... "tarea"` y termina. Hoy **nadie lo tiene publicado como servidor**, así que no existe una URL de harness que poner en `config.js`. No es un dato que falte en el handoff: ese servidor no existe todavía.
- **Para probar el chat YA (sin harness):** el lado servidor del chat (funciones de Vercel, **nunca** el navegador) hace exactamente las mismas llamadas que haría el harness. Son llamadas tipo OpenAI, ya probadas:
  - modelos individuales → `POST https://comand-center-1-claude-github-mcp-backup.hf.space/v1/router/chat/completions` con el token de la ficha elegida y `model: "auto"` (sección 3);
  - respaldo → encender el L4, esperar `/health` y llamar a `<url>/v1/chat/completions` (sección 4).
- En `config.js` se puede poner `harnessUrl` = la ruta del propio servidor del chat que hace ese puente (por ejemplo `/api/chat`), hasta que el harness tenga dirección propia.
- **Pendiente (decide el Director):** publicar el harness como servicio HTTP con el cómputo del Router. Cuando exista, su URL se agrega aquí.

### 0.2 Llamadas desde la dirección de Vercel (CORS)
- Si las llamadas salen del **lado servidor** del chat (funciones de Vercel), **no hace falta CORS**: el navegador nunca llama directo a la puerta del Router ni al L4.
- **Los tokens NO pueden ir en `config.js` ni en el navegador**: cualquiera que abra la página los vería. Van como variables de entorno del servidor del chat.
- Dirección del chat registrada: `https://riu-jev-bridge-maxbry123-8833s-projects.vercel.app`.

### 0.3 Nombres del selector — CONFIRMADOS
| Nombre en el selector del chat | Qué hace el servidor del chat |
|---|---|
| `ficha-kimi-k3` | chat a la puerta con el token `router/harness-ficha-1-kimi-k3`, `model: "auto"` |
| `ficha-glm-5` | ídem con `router/harness-ficha-1-glm-5` |
| `ficha-nemotron-super` | ídem con `router/harness-ficha-1-nemotron` |
| `ficha-groq-qwen` | ídem con `router/harness-ficha-1-groq-qwen-3-8` |
| `ficha-nemotron-lightning` | ídem con `router/harness-ficha-1-nemotron-lightning` |
| `respaldo-27b` | encender L4 `start 27b`, luego chat a `<url>/v1/chat/completions` con `model: "qwen3.8-27b"` y token de HF |
| `respaldo-35b` | encender L4 `start 35b`, luego chat a `<url>/v1/chat/completions` con `model: "qwen3.6-35b"` y token de HF |

Ojo con los nombres exactos: son `ficha-nemotron-super` (no `ficha-nemotron`) y `ficha-groq-qwen` (no `ficha-groq-qwen-3-8`). Estos son los mismos nombres que usa el patch del harness.

### 0.4 Encender el L4 desde el servidor del chat (sin Python)
Lo mismo que hace `respaldo_hf.py start`, por la API de Hugging Face (token `huggingface/token-1-new`):
```
POST https://huggingface.co/api/jobs/COMAND-CENTER-1
Authorization: Bearer <HF_TOKEN>
```
El cuerpo exacto (imagen, comando de arranque con apagado automático, disco del almacenamiento, puerto 8080) está en `respaldo_hf.py`; si el equipo prefiere no rearmarlo, puede ejecutar ese archivo en el servidor. Apagar: `POST https://huggingface.co/api/jobs/COMAND-CENTER-1/<job>/cancel`.

---

## 1. Cómo funciona (en palabras)

```
Chat (UI en Vercel, solo pantalla)
   │ HTTP
   ▼
Harness DeepSeek  = terminal central: todo llega aquí   (hoy: el servidor del chat hace este papel, ver 0.1)
   │ HTTP (tipo OpenAI)
   ├──▶ Fichas de modelos individuales ──▶ puerta fija del Router ──▶ banco (clave) ──▶ NVIDIA / Groq
   │
   └──▶ Router de respaldo HF (L4) ── directo por HTTP, NO pasa por el Router de GitHub
            ▲ se enciende en HF cuando llega un pedido (con tu almacenamiento conectado como disco)
            ▼ se apaga solo al terminar la respuesta, a los 5 min sin uso, o con el botón del chat
```

- El Router da cómputo y almacenamiento al harness (ficha 0). No se toca ni se relanza.

---

## 2. Datos fijos

| Qué | Valor |
|---|---|
| Dirección del chat | `https://riu-jev-bridge-maxbry123-8833s-projects.vercel.app` (funciona después del despliegue) |
| Puerta fija del Router (no cambia nunca) | `https://comand-center-1-claude-github-mcp-backup.hf.space` |
| Entrada tipo OpenAI de las fichas | `<puerta>/v1/router` (chat: `POST /v1/router/chat/completions`, `model: "auto"`) |
| Token de cómputo y almacenamiento del harness (ficha 0) | banco: `router/ficha-0` (permisos: memoria, almacenamiento, cómputo) |
| Token de HF (encender el L4 y hablar con él) | banco: `huggingface/token-1-new` |
| Tokens de GitHub (acceso total) | banco: `github/full-acceso`, `github/acceso-total-pat` |

Los valores de los tokens los entrega el Director (el banco no los devuelve por HTTP). Van solo en variables de entorno del servidor, nunca en archivos ni en el navegador.

---

## 3. Fichas de modelos individuales (ficha 1) — LISTAS

Cada modelo es una ficha del Router con **su propio token amarrado**: todo lo que se pida con ese token pasa por esa ficha y **solo responde ese modelo**. Si se agota una clave, el Router usa otra clave del mismo modelo; nunca cambia de modelo.

| Modelo | Ficha | Token en el banco | Prueba 2026-10-04 |
|---|---|---|---|
| Kimi K3 (NVIDIA) | `ficha-1-kimi-k3` | `router/harness-ficha-1-kimi-k3` | OK, 8 s |
| GLM 5.3 (NVIDIA) | `ficha-1-glm-5` | `router/harness-ficha-1-glm-5` | OK, 8 s |
| Nemotron 3 Super 120B (NVIDIA) | `ficha-1-nemotron` | `router/harness-ficha-1-nemotron` | OK, 2 s |
| Qwen 3.8 (Groq) | `ficha-1-groq-qwen-3-8` | `router/harness-ficha-1-groq-qwen-3-8` | OK, 0,1 s |
| Nemotron 3.5 Lightning (NVIDIA) | `ficha-1-nemotron-lightning` | `router/harness-ficha-1-nemotron-lightning` | OK (responde `model: seccion/ficha-1-nemotron-lightning`) |

**Cómo llamarla (cualquier cliente tipo OpenAI, desde el servidor):**
```bash
curl -s https://comand-center-1-claude-github-mcp-backup.hf.space/v1/router/chat/completions \
  -H "Authorization: Bearer $FICHA_GROQ_TOKEN" -H "Content-Type: application/json" \
  -d '{"model":"auto","messages":[{"role":"user","content":"hola"}]}'
```

**Harness DeepSeek:** patch listo (el harness no se edita): `router inteligente universal/fichas/individuales/harness-individuales.cordis.yml`.
Variables: `FICHA_KIMI_TOKEN`, `FICHA_GLM_TOKEN`, `FICHA_NEMOTRON_TOKEN`, `FICHA_GROQ_TOKEN`, `FICHA_LIGHTNING_TOKEN`.
```bash
dsh headless --patch 'router inteligente universal/fichas/individuales/harness-individuales.cordis.yml' "tarea"
```

---

## 4. Router de respaldo HF (L4) — LISTO, directo al harness

Un L4 de Hugging Face con llama.cpp. Los modelos ya están en tu almacenamiento de HF y se conectan como disco al encender. Cada encendido sirve **un** modelo:

| Selector | Clave | Modelo (`model` en la llamada) | Rol | Velocidad medida |
|---|---|---|---|---|
| `respaldo-27b` | `27b` | `qwen3.8-27b` (Qwen3.8-27B UD-Q3_K_XL) | arquitectura, plan, diseño, revisión | ~35 tokens/s |
| `respaldo-35b` | `35b` | `qwen3.6-35b` (Qwen3.6-35B-A3B + MTP UD-Q3_K_XL) | código, debug, ejecución | 89–115 tokens/s |

Parámetros del Director: solo texto, sin proyector de visión, MTP activo (`--spec-type draft-mtp`, `--spec-draft-n-max 2`), Flash Attention, `parallel 1`, `batch 128`, contexto 16K, temp 0, top-k 20, top-p 0,95, sin razonamiento (`--reasoning-budget 0`).

### 4.1 Disparador (encender al llegar un pedido)
```bash
HF_TOKEN=$HF_TOKEN python3 'router inteligente universal/fichas/respaldo-hf/respaldo_hf.py' start 35b    # o 27b
# -> {"job_id": "...", "url": "https://<job>--8080.hf.jobs", "modelo": "qwen3.6-35b"}
```
Esperar a que `GET <url>/health` (con `Authorization: Bearer $HF_TOKEN`) responda `{"status":"ok"}`. **Probado: listo en 73 s.** Luego mandar el pedido a `<url>/v1/chat/completions` con `model` = `qwen3.8-27b` o `qwen3.6-35b`.

### 4.2 Apagado (2 métodos + seguro)
1. **Automático al terminar la salida:** 30 s después de la última respuesta, el L4 se apaga solo. Probado: se apagó 42 s después de responder.
2. **Botón remoto del chat:** `python3 respaldo_hf.py stop <job>` (o la llamada `cancel` de 0.4). Probado: `CANCELED` al instante.
3. **Seguro:** si nunca llega un pedido, se apaga solo a los 5 min. Tope absoluto: 2 h.

Costo: L4 = 0,80 USD/h, solo mientras está encendido.

### 4.3 Harness DeepSeek
Patch listo: `router inteligente universal/fichas/respaldo-hf/harness-respaldo.cordis.yml`.
```bash
RESPALDO_HF_URL=https://<job>--8080.hf.jobs HF_TOKEN=$HF_TOKEN \
  dsh headless --patch 'router inteligente universal/fichas/respaldo-hf/harness-respaldo.cordis.yml' "tarea"
```
La URL cambia en cada encendido: se toma de lo que devuelve el disparador.

---

## 5. Lo que falta (no bloquea al equipo de la UI)
- Harness DeepSeek publicado como servicio HTTP (ver 0.1).
- Tope total de 90 s por llamada en NVIDIA (hoy 90 s por clave).
- Respaldo: DeepSeek V4 Flash por HF, equipo 27B → 35B → 27B, y comandos `razona` / `ejecuta` / `refactoriza`.
- Ficha 2 (consejo) con la configuración nueva y los saltos GLM → Lightning → muse-glimmer.

## 6. Archivos
- Este README: `router inteligente universal/fichas/README-CONEXION-CHAT-HARNESS.md`
- Respaldo: `router inteligente universal/fichas/respaldo-hf/` (`ficha.json`, `respaldo_hf.py`, `harness-respaldo.cordis.yml`)
- Individuales: `router inteligente universal/fichas/individuales/harness-individuales.cordis.yml`
- Notas del Director y plan: `Claude notas/claude notas 1.md`
