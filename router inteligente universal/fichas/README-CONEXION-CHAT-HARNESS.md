# README — Conexión del chat y el harness DeepSeek a las fichas (para el equipo de la UI)

Fecha: 2026-10-04 (Bogotá). Escrito por Opus por orden del Director (Hy). Todo lo de aquí está **probado en vivo**.
Sin claves en este archivo: todos los tokens viven en el banco del Router (se dan los nombres de referencia).

---

## 1. Cómo funciona (en palabras)

```
Chat (UI en Vercel, solo pantalla)
   │ HTTP
   ▼
Harness DeepSeek  = terminal central: todo llega aquí
   │ HTTP (tipo OpenAI)
   ├──▶ Fichas de modelos individuales ──▶ puerta fija del Router ──▶ banco (clave) ──▶ NVIDIA / Groq
   │
   └──▶ Router de respaldo HF (L4) ── directo por HTTP, NO pasa por el Router
            ▲ se enciende con el cómputo del Router (ficha 0) cuando llega un pedido
            ▼ se apaga solo al terminar la respuesta, a los 5 min sin uso, o con el botón del chat
```

- El chat **no** necesita hablar con el Router: habla con el harness. El harness habla con las fichas.
- La URL de Vercel del chat solo hace falta para darle permiso a esa pantalla (CORS) en el lado del harness.
- El Router da cómputo y almacenamiento a todo (por la ficha 0). No se toca ni se relanza.

---

## 2. Datos fijos

| Qué | Valor |
|---|---|
| Puerta fija del Router (no cambia nunca) | `https://comand-center-1-claude-github-mcp-backup.hf.space` |
| Entrada tipo OpenAI de las fichas | `<puerta>/v1/router` (chat: `POST /v1/router/chat/completions`, `model: "auto"`) |
| Cómputo (encender / estado / apagar) | `POST <puerta>/hf/compute/run`, `GET <puerta>/hf/compute/<job>`, `DELETE <puerta>/hf/compute/<job>` |
| Token de cómputo y almacenamiento (ficha 0) | banco: `router/ficha-0` (permisos: memoria, almacenamiento, cómputo) |
| Token de HF para hablar con el L4 | banco: `huggingface/token-1-new` |
| Tokens de GitHub (acceso total) | banco: `github/full-acceso`, `github/acceso-total-pat` |

Los valores de los tokens los entrega el Director (el banco no los devuelve por HTTP). Van solo en variables de entorno, nunca en archivos.

---

## 3. Fichas de modelos individuales (ficha 1) — LISTAS

Cada modelo es una ficha del Router con **su propio token amarrado**: todo lo que el harness pida con ese token pasa por esa ficha y **solo responde ese modelo**. Si se agota una clave, el Router usa otra clave del mismo modelo; nunca cambia de modelo.

| Modelo | Ficha | Token en el banco | Prueba 2026-10-04 |
|---|---|---|---|
| Kimi K3 (NVIDIA) | `ficha-1-kimi-k3` | `router/harness-ficha-1-kimi-k3` | OK, 8 s |
| GLM 5.3 (NVIDIA) | `ficha-1-glm-5` | `router/harness-ficha-1-glm-5` | OK, 8 s |
| Nemotron 3 Super 120B (NVIDIA) | `ficha-1-nemotron` | `router/harness-ficha-1-nemotron` | OK, 2 s |
| Qwen 3.8 (Groq) | `ficha-1-groq-qwen-3-8` | `router/harness-ficha-1-groq-qwen-3-8` | OK, 0,1 s |
| Nemotron 3.5 Lightning (NVIDIA) | `ficha-1-nemotron-lightning` | `router/harness-ficha-1-nemotron-lightning` | OK (por el token del harness: responde `model: seccion/ficha-1-nemotron-lightning`) |

**Cómo llamarla (cualquier cliente tipo OpenAI):**
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
En el selector del chat, cada opción = un proveedor de ese patch (`ficha-kimi-k3`, `ficha-glm-5`, `ficha-nemotron-super`, `ficha-groq-qwen`, `ficha-nemotron-lightning`).

---

## 4. Router de respaldo HF (L4) — LISTO

Un L4 de Hugging Face con llama.cpp. Cada encendido sirve **un** modelo:

| Clave | Modelo | Rol | Velocidad medida |
|---|---|---|---|
| `27b` | Qwen3.8-27B (UD-Q3_K_XL), nombre `qwen3.8-27b` | arquitectura, plan, diseño, revisión | 34,6 tokens/s |
| `35b` | Qwen3.6-35B-A3B + MTP (UD-Q3_K_XL), nombre `qwen3.6-35b` | código, debug, ejecución | 115 tokens/s |

Parámetros del Director: solo texto, sin proyector de visión, MTP activo (`--spec-type draft-mtp`, `--spec-draft-n-max 2`), Flash Attention, `parallel 1`, `batch 128`, contexto 16K, temp 0, top-k 20, top-p 0,95, sin razonamiento (`--reasoning-budget 0`).

### 4.1 Disparador (encender al llegar un pedido)
Cuando el chat manda un input para el respaldo y no hay L4 encendido, el lado del harness hace:
```bash
curl -s -X POST <puerta>/hf/compute/run -H "Authorization: Bearer $FICHA0_TOKEN" -H "Content-Type: application/json" -d @cuerpo.json
```
con el cuerpo que arma `router inteligente universal/fichas/respaldo-hf/respaldo_hf.py` (función `encender`). Más fácil:
```bash
RIU_TOKEN=$FICHA0_TOKEN python3 respaldo_hf.py start 35b    # o 27b
# -> {"job_id": "...", "url": "https://<job>--8080.hf.jobs", "modelo": "qwen3.6-35b"}
```
Esperar a que `GET <url>/health` (con `Authorization: Bearer $HF_TOKEN`) responda `{"status":"ok"}`. **Tarda unos 3–4 min** (descarga el modelo y lo carga). Luego mandar el pedido a `<url>/v1/chat/completions` con `model` = `qwen3.8-27b` o `qwen3.6-35b`.

### 4.2 Apagado (2 métodos + seguro)
1. **Automático al terminar la salida:** 30 s después de la última respuesta, el L4 se apaga solo. Probado: se apagó 20–35 s después de responder.
2. **Botón remoto del chat:** `DELETE <puerta>/hf/compute/<job>` con el token de la ficha 0 (o `python3 respaldo_hf.py stop <job>`). Probado: estado `CANCELED` al instante.
3. **Seguro:** si nunca llega un pedido, se apaga solo a los 5 min. Tope absoluto: 2 h.

Costo: L4 = 0,80 USD/h, solo mientras está encendido.

### 4.3 Harness DeepSeek
Patch listo: `router inteligente universal/fichas/respaldo-hf/harness-respaldo.cordis.yml`.
```bash
RESPALDO_HF_URL=https://<job>--8080.hf.jobs HF_TOKEN=$HF_TOKEN \
  dsh headless --patch 'router inteligente universal/fichas/respaldo-hf/harness-respaldo.cordis.yml' "tarea"
```
La URL cambia en cada encendido: el harness la toma de lo que devuelve el disparador.

---

## 5. Lo que falta (no bloquea al equipo de la UI)
- Tope total de 90 s por llamada en NVIDIA (hoy 90 s por clave; el total puede pasar si fallan varias claves).
- Respaldo: DeepSeek V4 Flash por HF, equipo 27B → 35B → 27B, y comandos `razona` / `ejecuta` / `refactoriza`.
- Ficha 2 (consejo) con la configuración nueva y los saltos GLM → Lightning → muse-glimmer.
- Más adelante: mover el encendido automático del L4 dentro de un plugin de fichas del Router, para que el harness no tenga que llamar al disparador.

## 6. Archivos
- Este README: `router inteligente universal/fichas/README-CONEXION-CHAT-HARNESS.md`
- Respaldo: `router inteligente universal/fichas/respaldo-hf/` (`ficha.json`, `respaldo_hf.py`, `harness-respaldo.cordis.yml`)
- Individuales: `router inteligente universal/fichas/individuales/harness-individuales.cordis.yml`
- Notas del Director y plan: `Claude notas/claude notas 1.md`
