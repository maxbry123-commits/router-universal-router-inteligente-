# HANDOFF PROVISIONAL — Router inteligente universal
Actualizado: 2026-09-29. Provisional: vale hasta que el chat se termine y se mueva a otro repo.
Alcance: SOLO el Router, sus conexiones, sus claves (solo nombres), Hugging Face y Vercel. Nada del chat, de las tareas en curso ni del equipo de agentes: eso vive aparte (`Estado y handoff global/`).
Regla: solo hechos verificados. Lo no verificado dice SIN VERIFICAR.
Guía para conectar otros repos/MCP: `CONECTAR-ROUTER.md` (misma carpeta).

## 0. Tareas del Router (todas las que tienen que ver con el Router viven aquí)
| # | Tarea | Estado |
|---|---|---|
| T-00 | Auditar el Router y dejar uno solo | PASS |
| T-01 | Limpieza de Hugging Face (la parte de Vercel queda para después, por orden del Director) | PASS (HF) · Vercel pendiente |
| T-03 | Quitar Cerebras del Router y poner Groq | PASS · Router relanzado con el código nuevo y Groq Qwen 3.8 en la cadena g2 (smoke run 36528065394) |
| T-10 | Conectar cualquier repo/MCP al Router único sin crear otro Router | DOCUMENTADO (`CONECTAR-ROUTER.md`) · sin probar desde otro repo |

### T-00 — Auditar el Router y dejar uno solo (PASS)
Un solo Router vivo: un Job de Hugging Face. Rutas probadas con el smoke (secciones 2 y 3). Incidente del vigilante de 32 GB en la sección 8. Evidencia: BITACORA B-0001, B-0002, B-0003, B-0007.

### T-01 — Limpieza de Hugging Face (PASS; Vercel pendiente)
Borrados `omniroute-1..5` (run 36518718390). Queda el Space del conector MCP (protegido), el Job del Router y el dataset de memoria. Sentinelas y mini-router pausados/borrados. Pendiente solo Vercel: las variables del proyecto no se borraron (son secretas e irrecuperables); "después borramos lo de Vercel" es decisión del Director. Evidencia: B-0003…B-0008, B-0011.

### T-03 — Quitar Cerebras y poner Groq (PASS)
Hecho, con pruebas (commits 7fa21739 y 3744d9b4):
- Cerebras quitado de: `integration/chat_mvp/providers.py`, `resilience.py` (cadena g2), `vault_bridge.py`; `agents-yaiwes/common/{routes,probe_keys,boot}.py`; `agent-microkernel/kernel/{dag_loader,dispatcher}.py`; `gateway/hf_chat_mvp/app.py`; `Banco de claves/{accounts,groups}.yaml`; 68 archivos `chain.yaml`/`workflow.dag.yaml` de agentes; los workflows `deploy-chat-space`, `riu-chat-mvp-verify`, `riu-dag-run`, `riu-validate-provider-keys`. Tests ajustados (Cerebras → Groq).
- Se dejó a propósito: el patrón `csk-` en `riu-secret-scan.yml` (detecta filtraciones), las notas textuales del Director y el historial/evidencias.
- Modelo de Groq: Qwen 3.8 (decisión del Director 2026-09-29). Id exacto verificado en vivo: `qwen/qwen3.8-27b` (respondió "OK"). Se fija con la variable `RIU_G2_GROQ_MODEL` en las dos llamadas `run_job` de `riu-router-job-central.yml` (commit 62e1bf74).
- Router relanzado: Job `6abb503a6b030d633f6a2dca`, dirección en el archivo de dirección (`LIVE_URL`, `PAUSED=false`). El lanzador escribió la dirección nueva y solo después canceló el Job viejo `6abb1ff352d0dbd7f1da8a58`.
- Verificado con el smoke (run 36528065394): `/health` 200; `/chat/models` 200; `/chat/router/status` 200 con cadena g2 = NVIDIA `nvidia/nemotron-3-super-120b-a12b` → Groq `qwen/qwen3.8-27b`; sin ninguna mención de Cerebras.
Pendiente / decisión del Director:
1. La cadena por defecto (no g2) sigue siendo solo NVIDIA: Groq no está en ella. ¿Se quiere ahí?
2. Vercel: `RIU_ROUTER_URL` quedó vieja con el relanzamiento (dirección fija).
3. El smoke prueba `/chat/send` y `/chat/jev` con provider=hf, que falla siempre (`PROVIDER_KEY_MISSING:hf` / 401): no es un fallo del cambio. Falta una prueba de chat real por NVIDIA/Groq (SIN VERIFICAR que responda).

### T-10 — Conectar cualquier repo/MCP al Router único (documentado)
Hecho: `CONECTAR-ROUTER.md` (cómo hallar la dirección, cabeceras, secretos que necesita cada repo, cliente existente `RouterCliente`, qué hacer si el Router se mueve).
Falta: probarlo de verdad desde otro repo (una corrida corta que lea el archivo de dirección y llame `/health`). Y decidir si hace falta un envoltorio MCP del Router (SIN VERIFICAR que exista; si se hace, se cablea lo descargado, no se escribe desde cero).

### Arreglo hecho tras la reorganización
El puente del banco (`integration/chat_mvp/vault_bridge.py`) buscaba la carpeta vieja `Chat Mvp`. Ahora busca `Banco de claves` (commit 3744d9b4). Pruebas antes: 162 pasan, 8 fallan, 6 errores; después: 168 pasan, 8 fallan, 0 errores (run 36526076292).
Los 8 fallos que quedan existían antes de este cambio (no verificado si vienen de la reorganización): `test_conector_gitlab_v6` (acción desconocida), `test_conector_interno_webhook_v6` (2), `test_conector_mcp_app_v6` (2), `test_conector_vps_v6`, `test_fast_close_global_e2e` (502), `test_huggingface_openai_chat_registry` (conjunto de modelos).
Rutas viejas que quedan sin importancia: un comentario en `resilience.py` que menciona `Chat Mvp/router_policy/peak.py`, y `riu-agent11-canonical-download.yml` (mira `hermes-agent/` en la raíz).

## 1. Qué es el Router
- Es UNO solo. Todo lo que se construya se conecta a él; no se crean routers nuevos.
- Corre como un Job de Hugging Face (máquina cpu-basic 16 GB), siempre encendido.
- Aplicación: `router inteligente universal/integration/chat_mvp/app.py` (FastAPI).
- Job vivo al 2026-09-29: `6abb503a6b030d633f6a2dca` (`https://6abb503a6b030d633f6a2dca--8000.hf.jobs`; la dirección cambia en cada relanzamiento: leerla siempre del archivo de dirección).

## 2. Cómo se lanza y dónde está su dirección
- Lanzador: `.github/workflows/riu-router-job-central.yml`. Ejecuta `router inteligente universal/agents-yaiwes/common/router_job_persistent.py`.
- Ese script clona el repo, descifra el banco de claves al arrancar, levanta la aplicación con uvicorn y vuelve a bajar el repo cada 60 segundos.
- Relanzar es seguro: el lanzador arranca el Job nuevo, espera `/health`, escribe la dirección nueva y solo entonces cancela el viejo. Aun así, se hace solo con orden del Director.
- La dirección viva está en `router inteligente universal/agents-yaiwes/ROUTER_JOB_PAUSE.flag` (línea `LIVE_URL`; línea `PAUSED=false`).
- Código que ya se importó no cambia con la bajada de 60 s: para que un cambio de código tome efecto hay que relanzar el Job.

## 3. Cómo se le habla
- Cabeceras: `Authorization: Bearer <HF_TOKEN_1>` y `X-API-Key: <RIU_ROUTER_API_KEY>` (solo nombres; los valores están en tu banco, nunca en el repo).
- Rutas verificadas (smoke runs 36513612455, 36521693774 y 36528065394):
  - `/health` → 200
  - `/chat/models` → 200 (lista Kimi K3 `moonshotai/Kimi-K3`, MiniMax, DeepSeek V4 Flash, otros)
  - `/chat/router/status` → 200
  - `/v1/models` → 200 pero solo 2 modelos chicos (Qwen3-8B, gpt2): no sirve para agentes
  - `/chat/send` con provider=hf → 400 `PROVIDER_KEY_MISSING:hf`; `/chat/jev` con provider=hf → 503 (401 aguas arriba). No usar provider=hf.
- También montadas (sin probar): `/chat/route`, `/chat/jobs/run`, `/memoria/*`, `/gh/*`, `/control/*`.
- Prueba de solo lectura: `.github/workflows/riu-router-smoke.yml` (botón manual). El resultado se lee en las anotaciones de la corrida.

## 4. Ruta de modelos (orden del Director)
NVIDIA (hasta 4 claves; Kimi K3 o el más nuevo) → Groq (Qwen 3.8) → DeepSeek V4 Flash al final. Sin APIs de Anthropic. Cerebras y OmniRoute eliminados.
Estado del Router VIVO (verificado 2026-09-29): cadena g2 = NVIDIA `nvidia/nemotron-3-super-120b-a12b` → Groq `qwen/qwen3.8-27b` (DeepSeek V4 Flash al final, se salta en hora pico). La cadena por defecto sigue solo NVIDIA.

## 5. Claves (solo nombres, nunca valores)
- Banco de claves: código en `router inteligente universal/Banco de claves/` (antes "Chat Mvp"). El Job lo descifra al arrancar; las claves reales viven en tu banco de secretos.
- Nombres vistos: `HF_TOKEN_1`, `HF_WRITE_TOKEN`, `HF_TOKEN_MAXBRY123`, `RIU_ROUTER_API_KEY`, `RIU_AGENT_API_KEYS`, `NVIDIA_API_KEY_1..4`, `GROQ_API_KEY_1..7` (la 1 dio 401; el lanzador pasa la 2..7), y para GitHub `GH_CLASSIC_FULL_1`, `GH_CLASSIC_FULL_2`, `RIU_GITHUB_PAT_FULL_ACCESO`, `GH_JOB_PUSH_TOKEN`.
- Cerebras: ya no se usa `CEREBRAS_API_KEY_1`; el secreto puede seguir existiendo en GitHub, ningún código lo lee (decisión del Director si se borra).
- El repo es PÚBLICO: jamás poner valores de claves aquí.
- Pendiente tuyo: rotar las 7 llaves de Groq que se pegaron en un chat.

## 6. Hugging Face (cuenta `COMAND-CENTER-1`)
- Jobs vivos: 1 (el Router).
- Spaces: 1 — `claude-github-mcp-backup`, el conector MCP de Claude. PROTEGIDO: no tocar, no reiniciar, no borrar. `keep-mcp-space-awake` sigue desactivado. Según Opus (SIN VERIFICAR por mí): sin OAuth, dirección secreta `/<MCP_SECRET_PATH>/mcp`, un webhook dispara el lanzador único.
- Datasets: `yaiwes-hf-memoria` (privado, memoria).
- Borrados el 2026-09-29: `omniroute-1..5`.
- Documentos de Hugging Face: carpeta `Huggingface/` (incluye `README-HUGGINGFACE.md`).

## 7. Vercel (solo pantalla)
- Cuenta `maxbry123@gmail.com` · usuario `maxbry123-8833` · plan Hobby · team `maxbry123-8833s-projects` (`team_hG9df7zIgfZFY0oxFFsIRr1u`).
- Proyecto `riu-jev-bridge` (`prj_m8Lk3iaB3eN6dwlIq1ND2un8FWTD`). Sin despliegue vivo; despliegue automático apagado (cada push deja un intento CANCELED, es normal).
- Variables (solo nombres): `RIU_CHAT_PASSWORD`, `RIU_ROUTER_API_KEY`, `RIU_ROUTER_URL`, `HF_JOB_FLAVOR`, `HF_TOKEN_1`. NO se borraron: son secretas e irrecuperables. Decisión de borrarlas: del Director, más adelante.
- `RIU_ROUTER_URL` es una dirección fija: tras el relanzamiento del 2026-09-29 quedó vieja (ver `CONECTAR-ROUTER.md`, sección 1).
- Regla: no instalar nada hasta que todo esté listo; un único deploy final, solo con su orden.
- Documento: `Vercel/HANDOFF-VERCEL.md`.

## 8. Incidente que no debe repetirse
El 2026-09-29 un vigilante (`riu-hf-jobs-audit-32gb.yml`) cancelaba cualquier Job que no fuera cpu-upgrade y mató al Router a las 02:15Z (run 36511703509). Ya está borrado. Regla: ningún workflow puede cancelar ni relanzar el Job del Router salvo el lanzador único y por orden del Director.

## 9. Para llevarse el Router a otro repo
- Copiar la carpeta `router inteligente universal/` completa (incluye el banco de claves, `CONECTAR-ROUTER.md` y este archivo).
- Llevar también el lanzador `.github/workflows/riu-router-job-central.yml` y `riu-router-smoke.yml`.
- La dirección del repo está escrita en: `REPO_URL` de `agents-yaiwes/common/router_job_persistent.py` (línea 20), en el `git clone` y en la URL de la API del archivo de dirección dentro de `riu-router-job-central.yml` (líneas 62 y 102), y en `FLAG_URL` de `chat router/05-AGENTES/colmena/router_cliente.py`. Verificado leyendo esos archivos.
- Nombres de secretos de GitHub Actions: hay que recrearlos en el repo nuevo.
