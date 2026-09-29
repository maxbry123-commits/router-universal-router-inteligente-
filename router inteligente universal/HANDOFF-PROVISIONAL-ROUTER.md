# HANDOFF PROVISIONAL — Router inteligente universal
Actualizado: 2026-09-29. Provisional: vale hasta que el chat se termine y se mueva a otro repo.
Alcance: SOLO el Router, sus conexiones, sus claves (solo nombres), Hugging Face y Vercel. Nada del chat, de las tareas en curso ni del equipo de agentes: eso vive aparte (`Estado y handoff global/`).
Regla: solo hechos verificados. Lo no verificado dice SIN VERIFICAR.

## 1. Qué es el Router
- Es UNO solo. Todo lo que se construya se conecta a él; no se crean routers nuevos.
- Corre como un Job de Hugging Face (máquina cpu-basic 16 GB), siempre encendido.
- Aplicación: `router inteligente universal/integration/chat_mvp/app.py` (FastAPI).
- Job vivo al 2026-09-29: `6abb1ff352d0dbd7f1da8a58`, encendido desde las 02:18Z.

## 2. Cómo se lanza y dónde está su dirección
- Lanzador: `.github/workflows/riu-router-job-central.yml`. Ejecuta `router inteligente universal/agents-yaiwes/common/router_job_persistent.py`.
- Ese script clona el repo, descifra el banco de claves al arrancar, levanta la aplicación con uvicorn y vuelve a bajar el repo cada 60 segundos.
- Lanzar un Job nuevo APAGA el anterior. No lanzar sin permiso del Director.
- La dirección viva está en `router inteligente universal/agents-yaiwes/ROUTER_JOB_PAUSE.flag` (línea `LIVE_URL`; línea `PAUSED=false`).
- Código que ya se importó no cambia con la bajada de 60 s: para que un cambio de código tome efecto hay que relanzar el Job.

## 3. Cómo se le habla
- Cabeceras: `Authorization: Bearer <HF_TOKEN_1>` y `X-API-Key: <RIU_ROUTER_API_KEY>` (solo nombres; los valores están en tu banco, nunca en el repo).
- Rutas verificadas (smoke run 36513612455 y run 36521693774, 2026-09-29):
  - `/health` → 200
  - `/chat/models` → 200 (lista Kimi K3 `moonshotai/Kimi-K3`, MiniMax, DeepSeek V4 Flash, otros)
  - `/chat/router/status` → 200
  - `/v1/models` → 200 pero solo 2 modelos chicos (Qwen3-8B, gpt2): no sirve para agentes
  - `/chat/send` con provider=hf → 400 `PROVIDER_KEY_MISSING:hf`; `/chat/jev` con provider=hf → 503 (error 401 aguas arriba). No usar provider=hf.
- También montadas (sin probar): `/chat/route`, `/chat/jobs/run`, `/memoria/*`, `/gh/*`, `/control/*`.
- Prueba de solo lectura: `.github/workflows/riu-router-smoke.yml` (botón manual). El resultado se lee en las anotaciones de la corrida.

## 4. Ruta de modelos (orden del Director)
NVIDIA (hasta 4 claves; Kimi K3 o el más nuevo) → Groq → DeepSeek V4 Flash al final. Sin APIs de Anthropic. Cerebras y OmniRoute eliminados.
Estado real hoy (`/chat/router/status`): la cadena por defecto y la g2 son solo NVIDIA `nvidia/nemotron-3-super-120b-a12b`. DeepSeek V4 Flash se salta en hora pico. Groq no está en ninguna cadena todavía.
Resto de Cerebras en el código, por quitar: `integration/chat_mvp/providers.py`, `resilience.py` (cadena g2) y `vault_bridge.py`. Ya está excluido del enrutado de agentes (`common/routes.py`, `EXCLUIDOS`).

## 5. Claves (solo nombres, nunca valores)
- Banco de claves: código en `router inteligente universal/Banco de claves/` (antes "Chat Mvp"). El Job lo descifra al arrancar; las claves reales viven en tu banco de secretos.
- Nombres vistos: `HF_TOKEN_1`, `HF_WRITE_TOKEN`, `HF_TOKEN_MAXBRY123`, `RIU_ROUTER_API_KEY`, `RIU_AGENT_API_KEYS` (autenticación que anuncia `/health`), `NVIDIA_API_KEY_1..4`, `GROQ_API_KEY_1`, y para GitHub `GH_CLASSIC_FULL_1`, `GH_CLASSIC_FULL_2`, `RIU_GITHUB_PAT_FULL_ACCESO`, `GH_JOB_PUSH_TOKEN`.
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
- Regla: no instalar nada hasta que todo esté listo; un único deploy final, solo con su orden.
- Documento: `Vercel/HANDOFF-VERCEL.md`.

## 8. Incidente que no debe repetirse
El 2026-09-29 un vigilante (`riu-hf-jobs-audit-32gb.yml`) cancelaba cualquier Job que no fuera cpu-upgrade y mató al Router a las 02:15Z (run 36511703509). Ya está borrado. Regla: ningún workflow puede cancelar ni relanzar el Job del Router salvo el lanzador único y por orden del Director.

## 9. Para llevarse el Router a otro repo
- Copiar la carpeta `router inteligente universal/` completa (incluye el banco de claves y este archivo).
- Llevar también el lanzador `.github/workflows/riu-router-job-central.yml` y `riu-router-smoke.yml`.
- El lanzador y `router_job_persistent.py` clonan ESTE repo: al mover hay que cambiar esa dirección. Dónde está escrita exactamente: SIN VERIFICAR (buscarlo antes de mover).
- Nombres de secretos de GitHub Actions: hay que recrearlos en el repo nuevo.
