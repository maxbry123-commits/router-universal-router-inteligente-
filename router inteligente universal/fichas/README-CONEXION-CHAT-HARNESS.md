# README — Conexión del chat (para el equipo de la UI) — v4

Fecha: 2026-10-04 (Bogotá). Escrito por Opus por orden del Director (Hy). Sin claves en este archivo.

> ⚠️ **Estado 2026-10-04 21:15:** Hugging Face pausó el Space de la puerta por **falta de créditos prepagados** (respuesta `402 Payment Required`). Mientras no se carguen créditos en `https://huggingface.co/settings/billing` (cuenta `COMAND-CENTER-1`), la puerta, el Router y el L4 no responden. Todo lo de abajo quedó **listo y probado antes de la pausa**; al reanudar vuelve solo.

---

## 0. Lo que necesita el equipo de la UI

### 0.1 El puente vive DENTRO del Router (no en Vercel)
- Plugin `puente_chat` del Router: corre en el cómputo del Router (HF), con la **dirección fija** de la puerta.
- **`harnessUrl` (ya puesto en `chat router/chat frontend/config.js`):**
  `https://comand-center-1-claude-github-mcp-backup.hf.space/plugins/puente_chat/call`
- **`api.js` ya adaptado** (`chat router/chat frontend/api.js`): si `harnessUrl` apunta a `/plugins/puente_chat`, la pantalla habla con el puente del Router. No hay que cambiar nada más en la UI.
- **Permiso desde Vercel (CORS):** la puerta ya acepta `https://riu-jev-bridge-maxbry123-8833s-projects.vercel.app` (probado: preflight 200 con `access-control-allow-origin` = esa dirección).
- **Clave del chat:** la pantalla la pide una vez ("Contraseña del chat") y la manda como `Authorization: Bearer <clave>`. Sin clave → 401. La clave es un token del Router de la instancia `chat-ui` (banco: `router/chat-ui-pantalla`); el valor lo entrega el Director.
- **Vercel solo pone la pantalla.** No hacen falta variables de entorno ni `api/chat.js` en Vercel.

### 0.2 Los 7 modelos (nombres del Director)
| `model` | Nombre | Cómo responde |
|---|---|---|
| `hf-1-qwen-3-8` | HF 1 Qwen 3.8 (27B) | enciende L4 en HF y responde |
| `hf-2-qwen-3-6` | HF 2 Qwen 3.6 (35B) | enciende L4 en HF y responde |
| `groq-qwen-3-8` | GROQ Qwen 3.8 | Groq, claves del banco |
| `nv-kimi-k3` | NV Kimi K3 | NVIDIA, claves del banco |
| `nv-glm-5-3` | NV GLM 5.3 | NVIDIA, claves del banco (espera hasta 96 s) |
| `nv-nemotron-super` | NV Nemotron 3 Super | NVIDIA, claves del banco |
| `nv-nemotron-lightning` | NV Nemotron 3.5 Lightning | NVIDIA, claves del banco |
Cada modelo NV/GROQ rota **solo claves del mismo modelo**; nunca cambia de modelo. Tope total de espera: 90 s (GLM 96 s).

### 0.3 Protocolo del puente (por si lo necesitan)
Todas: `POST <harnessUrl>/<accion>` con JSON y `Authorization: Bearer <clave>`. Respuesta: `{"status": "ok", "result": {...}}`.
| Acción | Cuerpo | `result` |
|---|---|---|
| `modelos` | `{}` | `{modelos: [{id, nombre, respaldo}]}` |
| `chat` | `{model, messages, max_tokens, sesion, respaldo_url?}` | NV/GROQ: respuesta tipo OpenAI (`choices[0].message.content`) + `memoria_guardada`. HF sin `respaldo_url`: `{estado: "encendiendo", job_id, url}` |
| `estado` | `{job, url}` | `{etapa, listo}` (cuando `listo: true`, mandar `chat` con `respaldo_url = url`) |
| `apagar` | `{job}` | `{job_id, apagado}` — **solo apaga L4 de respaldo**; cualquier otro job → `SOLO_SE_APAGAN_JOBS_DEL_L4_DE_RESPALDO` |

### 0.4 Memoria
- Cada turno se guarda en la memoria del Router (sesión = `sesion`; `api.js` crea una por pestaña).
- Antes de responder, el puente agrega al modelo los **últimos turnos de esa sesión**.

### 0.5 L4 (modelos HF)
- Se enciende con el primer mensaje HF, **listo en ~75 s** (modelos desde el almacenamiento de HF conectado como disco).
- Se apaga solo **30 s después de terminar la respuesta**, a los **5 min sin pedidos**, o con `apagar`. Tope 2 h. Costo 0,80 USD/h solo mientras está encendido.

---

## 1. Pruebas (2026-10-04, por la puerta fija, con la clave del chat)
- Sin clave → **401**. Con clave: lista de modelos **OK**.
- `groq-qwen-3-8`: **OK en 0,6 s**, memoria guardada.
- `hf-2-qwen-3-6`: encendido → listo en **76 s** → respondió código → memoria guardada → **se apagó solo** (`COMPLETED`).
- `apagar` sobre el job del Router → **rechazado** (protección OK).
- Fichas del Router (5 modelos individuales) siguen montadas.
- Pendiente de comprobar al reanudar: recuerdo de los últimos turnos (cambio subido justo antes de la pausa).

## 2. Cómo se reanuda (Director → Opus)
1. Director carga créditos en HF.
2. Reanudar el Space `COMAND-CENTER-1/claude-github-mcp-backup`. El kernel enciende el Router con el paquete que ya trae `puente_chat`.
3. Comprobar `GET <puerta>/plugins` → `puente_chat: ready`.
4. Crear la clave del chat nueva (si hace falta entregarla) y probar: NV, memoria con recuerdo, ciclo HF completo.

## 3. Archivos
- Puente (código, también dentro del paquete del Router): `router inteligente universal/plugins/puente_chat/`
- Pantalla: `chat router/chat frontend/config.js` y `api.js`
- Respaldo HF (lanzador Python alternativo): `router inteligente universal/fichas/respaldo-hf/`
- `router inteligente universal/fichas/puente-chat/api/chat.js` → **ya no se usa** (el puente vive en el Router).
