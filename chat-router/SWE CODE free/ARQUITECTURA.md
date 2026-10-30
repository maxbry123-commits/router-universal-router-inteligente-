# ARQUITECTURA — SWE CODE y SWEN CODE free

Guía única de cómo funciona, cómo se recupera y cómo se hace el trabajo. Todo lo que dice aquí está en el código de `main`.

## 1. Los dos edificios

| Edificio | Carpeta | Qué hace |
|---|---|---|
| 1 · SWE CODE | `chat-router/SWE CODE/` | Cascada de agentes de código sobre modelos locales baratos de HF (`mini_router.py`, `cascada.json`, `motores.json`) y el **web-bridge** (cuentas web Qwen/DeepSeek → API OpenAI). |
| 2 · SWEN CODE free | `chat-router/SWE CODE free/` | Activador y modos (`activar.js`, `swen.json`), manual del agente (`INSTRUCCIONES.md`, `agente.md`), puente móvil + APK, auto-evolución (`evolucion.py`). |

Los dos son plugins removibles (`ficha.json`, `plugin_host/v1`) enlazados desde `chat-router/plugins/` y registrados en `chat-router/cableado.manifest.json`.

## 2. Camino de una petición (única vía)

```
chat Yaiwes / app OpenClaw ➡️ plugins ➡️ Harness DeepSeek (HTTP) ➡️ Router MVP /chat ➡️ swe.py ➡️ bridge :7870 | cola HF S1-S3
                                                                                          └─ si falla: Groq ➡️ NVIDIA ➡️ HF local
```

- El selector del chat ofrece 2 grupos nuevos: **SWE CODE (local HF)** y **SWEN CODE free (web)**, junto a Qwen, DeepSeek, GLM, imágenes y voz (no se tocaron).
- `router-mvp` ↔ `chat-router/chat/backend/mvp/swe.py` decide el destino por id:
  - `web-qwen38max`, `web-qwen37max`, `web-dsv4-flash`, `swecode-<modo>` → `WEB_BRIDGE_URL/v1/chat/completions`.
  - `lfm2.5-350m`, `qwen2.5-coder-1.5b`, `qwen3.5-0.8b`, `qwen3-0.6b` y los ids del selector (`hf-liquid-lfm25`, `swe-codex-qwen25-15b`…) → `SWECODE_URL_S1..S3` (entra por S1, salta a S2/S3).
- Respaldo (todos los modelos SWE): Groq, luego NVIDIA (mismas claves del banco que el chat con `groq/` y `nvidia/`), y al final `lfm2.5-350m` en HF local. La respuesta trae `via_respaldo` (`groq`, `nvidia` o `hf-local`) y `modelo_respuesta` = el que contestó de verdad.
- Como pasa por el Harness, **cualquier modelo del selector tiene las mismas herramientas del chat Yaiwes**: `github_leer`, `github_escribir`, `github_api`, `archivos` (motor de descarga/extracción/copia/mover/buscar), `memoria`, `almacen` (HF), `pendientes`, `sala`, `agente`, `llm`, `loop`.
- El formato de salida (VEREDICTO/EVIDENCIA/GAP/SIGUIENTE en SWE; checklist + Concluido/Faltante/Validación en el chat) lo pone la capa `prompt.formato()` del Router a **todo** modelo, incluido Liquid.

## 3. Memoria e historial compartidos

- Una sola memoria: bucket HF `COMAND-CENTER-1/yaiwes-memoria-storage`, carpeta `riu-chat/` (herramienta `memoria`, scopes `chat-ui:hist:<sesion>`).
- OpenClaw la usa por la misma herramienta `memoria` del MCP del Router (`POST {ROUTER}/mcp`), no tiene almacén propio.
- Cambiar de modelo en el selector no pierde nada: el chat reenvía el historial de la sesión (`contexto_previo`) y el Router quita solo las frases de identidad de otros modelos (`_sin_identidades`) para que el nuevo no las copie.

## 4. Conectividad y respaldo (de más a menos preferido)

1. web-bridge en el servidor Riu `:7870` (cuentas web Qwen/DeepSeek, métodos 1+4, respaldo 2+3).
2. Rotación de correos dentro del bridge (5–9 cuentas). Las cuentas y la clave **son de OpenClaw** y viajan por llamada (`cuentas`/`clave` del POST); nunca en secrets del Space.
3. Modelos locales S1/S2/S3.
4. Groq ➡️ NVIDIA ➡️ HF local (`swe.py` en el chat, `mini_router.py` en la cascada).
5. APK móvil: Chrome del teléfono (IP residencial) como último eslabón. El móvil **no hace cómputo**, solo conduce Chrome.

## 5. Cómo se recupera cada fallo

Ver `INSTRUCCIONES.md` §7 (tabla) y §7a (runbook de auto-diagnóstico). Resumen: `SESSION_EXPIRED` → `POST /refresh_session`; media tarea → mismo `conv_id` (checkpoint); `cuentas:{}` → faltan las cuentas de OpenClaw; contenido vacío → `GET /debug/tab` (gate "Confirma tu edad" ya manejado); `DEPLOY_STALE` → rebuild del Space; `/v1/queue` 404 → ruta en el proxy.

Recuperar las sesiones de Qwen y DeepSeek con distintos correos: `POST /refresh_session` re-loguea y rota a la siguiente cuenta si la actual murió; `GET /v1/queue` muestra tabs por sitio, `conv_id`s y cuentas (índices, nunca valores).

## 6. Cómo se hace el trabajo

- `SWEN CODE free [modo <m>] [con|solo|modelo <nombre>] [chat <id>] [pipeline code|free] [doc <ruta>] <texto>` (gramática en `activar.js`).
- Dos secciones en paralelo = dos `conv_id` (tab propia, `BRIDGE_MAX_TABS=4`). Espejo = clonar un modelo a otro `conv_id`/slot.
- Pipelines: CODE (liquid 1 recibe y delega → liquid 2 despliega; qwen-coder solo si hay `[GAP]`) y FREE (qwen instruye → swe-agente → liquid despliega).
- Salida larga: `.md`/código a `salidas/` y a GitHub. Un paso FAIL corta la cascada y devuelve recibo. Sin PASS sin evidencia.

## 7. Auto-evolución

`evolucion.py`: el agente registra una lección por cada arreglo (`registrar`); lo que se repite 3 veces con éxito se propone como paso del runbook y lo que falla 3 veces como cambio de estrategia (`proponer`/`md` → `salidas/evolucion/LECCIONES.md` y `PROPUESTAS.md`). Solo propone sobre `SWE CODE/` y `SWE CODE free/`; lo protegido por el manifest y todo lo del chat quedan fuera (`permitido()`).

## 8. Guarda de organización

Dos raíces: `router-mvp/` y `chat-router/`. `python3 chat-router/chat/auditoria/guardia_cableado.py` verifica rutas protegidas, enlaces y plugins; si se cambia algo protegido a propósito, se regenera con `--crear` en el mismo commit.
