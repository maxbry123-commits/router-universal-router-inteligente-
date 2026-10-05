# README — Conexión del chat a las fichas (para el equipo de la UI)

Fecha: 2026-10-04 (Bogotá). Escrito por Opus por orden del Director (Hy). Todo lo de aquí está **probado en vivo**.
Sin claves en este archivo: los tokens viven en el banco del Router (se dan los nombres de referencia).

---

## 0. LO QUE NECESITA EL EQUIPO DE LA UI (leer primero)

### 0.1 `harnessUrl` = `/api/chat` (puente listo)
- El harness DeepSeek (`dsh`) es un programa de terminal: **no tiene dirección HTTP**. Para que el chat funcione ya, el papel del harness lo hace un **puente listo**: `router inteligente universal/fichas/puente-chat/api/chat.js`.
- **Qué hacer:** copiar ese archivo a la carpeta `api/` del proyecto del chat en Vercel y poner en `config.js`: `harnessUrl: '/api/chat'`.
- Corre en el **mismo dominio** del chat (`https://riu-jev-bridge-maxbry123-8833s-projects.vercel.app`), así que **no hay CORS**.
- **Variables de entorno del proyecto Vercel** (valores los da el Director; nunca en `config.js` ni en el navegador):
  `FICHA_KIMI_TOKEN`, `FICHA_GLM_TOKEN`, `FICHA_NEMOTRON_TOKEN`, `FICHA_GROQ_TOKEN`, `FICHA_LIGHTNING_TOKEN`, `HF_TOKEN`.
- **Probado (2026-10-04):** lista de modelos OK; chat por ficha OK; encender L4 OK (202 + job); estado OK; apagar OK (`CANCELED`).

### 0.2 Los 7 modelos del selector (nombres del Director)
| `model` que manda el chat | Nombre visible | Qué hace el puente | Token |
|---|---|---|---|
| `hf-1-qwen-3-8` | HF 1 Qwen 3.8 (27B) | enciende L4 y responde con Qwen3.8-27B | `HF_TOKEN` |
| `hf-2-qwen-3-6` | HF 2 Qwen 3.6 (35B) | enciende L4 y responde con Qwen3.6-35B-A3B + MTP | `HF_TOKEN` |
| `groq-qwen-3-8` | GROQ Qwen 3.8 | ficha `ficha-1-groq-qwen-3-8` | `FICHA_GROQ_TOKEN` (banco: `router/harness-ficha-1-groq-qwen-3-8`) |
| `nv-kimi-k3` | NV Kimi K3 | ficha `ficha-1-kimi-k3` | `FICHA_KIMI_TOKEN` (banco: `router/harness-ficha-1-kimi-k3`) |
| `nv-glm-5-3` | NV GLM 5.3 | ficha `ficha-1-glm-5` | `FICHA_GLM_TOKEN` (banco: `router/harness-ficha-1-glm-5`) |
| `nv-nemotron-super` | NV Nemotron 3 Super | ficha `ficha-1-nemotron` | `FICHA_NEMOTRON_TOKEN` (banco: `router/harness-ficha-1-nemotron`) |
| `nv-nemotron-lightning` | NV Nemotron 3.5 Lightning | ficha `ficha-1-nemotron-lightning` | `FICHA_LIGHTNING_TOKEN` (banco: `router/harness-ficha-1-nemotron-lightning`) |

`GET /api/chat?accion=modelos` devuelve esta lista para llenar el selector.

### 0.3 Cómo usa el chat el puente
**Modelos NV / GROQ (respuesta directa, tipo OpenAI):**
```
POST /api/chat   {"model": "nv-kimi-k3", "messages": [...], "max_tokens": 2048}
-> {"choices": [{"message": {"content": "..."}}], ...}
```
**Modelos HF (L4, en 3 pasos):**
1. `POST /api/chat {"model": "hf-2-qwen-3-6", "messages": [...]}` → `202 {"estado": "encendiendo", "job_id": "...", "url": "https://<job>--8080.hf.jobs"}`. El chat muestra "encendiendo modelo (≈1 min)".
2. Cada 5 s: `GET /api/chat?accion=estado&job=<job_id>&url=<url>` → cuando `listo: true`, seguir.
3. `POST /api/chat {"model": "hf-2-qwen-3-6", "messages": [...], "respaldo_url": "<url>"}` → respuesta tipo OpenAI.
   Mientras el L4 siga encendido, los siguientes mensajes van directo con `respaldo_url` (paso 3).

**Botón de apagado remoto:** `POST /api/chat?accion=apagar&job=<job_id>`.

**Apagado automático (no hace nada el chat):** el L4 se apaga solo 30 s después de terminar la respuesta, o a los 5 min sin pedidos (tope 2 h). Si el L4 ya se apagó (estado `COMPLETED`/`CANCELED`), el chat vuelve al paso 1.

---

## 1. Cómo funciona (en palabras)
```
Chat (Vercel) ──▶ /api/chat (puente = papel del harness)
                     ├──▶ modelos NV / GROQ ──▶ puerta fija del Router ──▶ ficha (token amarrado) ──▶ banco ──▶ NVIDIA / Groq
                     └──▶ modelos HF ──▶ enciende L4 en HF (almacenamiento conectado como disco) ──▶ responde ──▶ se apaga solo
```
- El Router no se toca ni se relanza. El respaldo HF no pasa por el Router de GitHub.

## 2. Datos fijos
| Qué | Valor |
|---|---|
| Dirección del chat | `https://riu-jev-bridge-maxbry123-8833s-projects.vercel.app` |
| Puerta fija del Router | `https://comand-center-1-claude-github-mcp-backup.hf.space` (chat de fichas: `POST /v1/router/chat/completions`, `model: "auto"`) |
| Token de cómputo y almacenamiento (ficha 0) | banco: `router/ficha-0` |
| Token de HF | banco: `huggingface/token-1-new` |
| Tokens de GitHub (acceso total) | banco: `github/full-acceso`, `github/acceso-total-pat` |

## 3. Pruebas de las fichas (2026-10-04)
Kimi K3 OK (8 s) · GLM 5.3 OK (8 s) · Nemotron 3 Super OK (2 s) · Groq Qwen 3.8 OK (0,1 s) · Nemotron 3.5 Lightning OK.
Cada ficha tiene su token amarrado: con ese token solo responde ese modelo; si se agota una clave, el Router usa otra clave del mismo modelo.

## 4. Respaldo HF (L4)
| Modelo | Velocidad medida | Listo en |
|---|---|---|
| HF 1 Qwen 3.8 (27B) | ~35 tokens/s | ~1 min |
| HF 2 Qwen 3.6 (35B) | 89–115 tokens/s | 73 s (probado) |
Parámetros del Director: solo texto, sin visión, MTP (`--spec-type draft-mtp`, `--spec-draft-n-max 2`), Flash Attention, `parallel 1`, `batch 128`, contexto 16K, temp 0, top-k 20, top-p 0,95, sin razonamiento. Costo L4: 0,80 USD/h solo mientras está encendido.
Lanzador en Python (alternativa al puente): `router inteligente universal/fichas/respaldo-hf/respaldo_hf.py start|status|stop`.

## 5. Para el harness DeepSeek (cuando se use en terminal)
- Individuales: `router inteligente universal/fichas/individuales/harness-individuales.cordis.yml`
- Respaldo: `router inteligente universal/fichas/respaldo-hf/harness-respaldo.cordis.yml`

## 6. Lo que falta (no bloquea a la UI)
- Harness DeepSeek publicado como servicio HTTP propio (hoy lo reemplaza `/api/chat`).
- Tope total de 90 s por llamada en NVIDIA.
- Respaldo: DeepSeek V4 Flash, equipo 27B → 35B → 27B, comandos `razona` / `ejecuta` / `refactoriza`.
- Ficha 2 (consejo) nueva.
