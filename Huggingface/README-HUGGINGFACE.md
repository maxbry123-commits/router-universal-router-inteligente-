# README DEL ROUTER (Hugging Face) — estado real
Actualizado: 2026-09-29. Solo lo verificado. Sin claves: solo nombres de secretos.
Registro detallado: `Estado y handoff global/` (ESTADO.json, CRAZY_WALL.json, BITACORA.jsonl, HANDOFF.md y fichas de tareas).

## Un solo Router
| Pieza | Dónde vive | Notas |
|---|---|---|
| Router (FastAPI) | Job HF cpu-basic 16 GB, siempre encendido | Lo lanza `.github/workflows/riu-router-job-central.yml`, que corre `router inteligente universal/agents-yaiwes/common/router_job_persistent.py` (clona el repo, descifra el banco, levanta `integration.chat_mvp.app`, se actualiza cada 60 s). Lanzar uno nuevo apaga el anterior. Dirección: `router inteligente universal/agents-yaiwes/ROUTER_JOB_PAUSE.flag` (`LIVE_URL`). |
| Conector MCP de Claude | Space `COMAND-CENTER-1/claude-github-mcp-backup` | PROTEGIDO, no tocar ni reiniciar. Hecho por Opus (documentado, no verificado por mí): sin OAuth, dirección secreta `/<MCP_SECRET_PATH>/mcp`, webhook al lanzador único, keep-awake desactivado. |
| Memoria | Dataset privado `COMAND-CENTER-1/yaiwes-hf-memoria` | Puente pendiente (tarea T-08). |
| Chat | Vercel `riu-jev-bridge` | Solo pantalla. Auto-deploy apagado. Un único deploy final solo cuando el Director lo ordene (tarea T-09). Ver `Vercel/HANDOFF-VERCEL.md`. |
| Banco de claves | `router inteligente universal/Banco de claves/` | Antes "Chat Mvp". Solo el código del banco cifrado; las claves viven en tu banco, nunca en el repo. |

## Cómo llamar al Router
Cabeceras: `Authorization: Bearer <HF_TOKEN_1>` + `X-API-Key: <RIU_ROUTER_API_KEY>`.
Verificado 2026-09-29 (smoke 36513612455): `/health` 200, `/chat/models` 200, `/chat/router/status` 200. `/v1/models` solo lista 2 modelos chicos (no sirve para agentes). `/chat/send` con provider=hf da 400 y `/chat/jev` con provider=hf da 503: no usar provider=hf.
También montadas: `/chat/route`, `/chat/jobs/run`, `/memoria/*`, `/gh/*`, `/control/*`.

## Rutas de IA (orden del Director)
NVIDIA (hasta 4 claves; Kimi K3 o el más nuevo) → Groq → DeepSeek V4 Flash al final. Sin APIs de Anthropic. **Cerebras eliminado por orden del Director** (aún queda en el código: `providers.py`, `resilience.py`, `vault_bridge.py`; pendiente quitarlo, tarea T-03). OmniRoute eliminado.
Estado hoy: la cadena por defecto usa NVIDIA `nvidia/nemotron-3-super-120b-a12b`; DeepSeek se salta en hora pico; Groq aún no está en ninguna cadena (T-03).

## Cuenta HF `COMAND-CENTER-1`
Secretos (nombres): `HF_TOKEN_1`, `HF_WRITE_TOKEN`, `HF_TOKEN_MAXBRY123`.
Inventario 2026-09-29: 1 Job vivo (el Router), 1 Space (el conector MCP), 1 dataset de memoria. `omniroute-1..5` borrados el 2026-09-29 (run 36518718390).

## Incidente 2026-09-29
El workflow `riu-hf-jobs-audit-32gb.yml` cancelaba cualquier Job que no fuera cpu-upgrade y mató al Router a las 02:15Z (run 36511703509). Se desactivó y se borró. Se relanzó el Router (02:18Z).

## Historial
- 2026-09-25: GPT añade OAuth al conector (causa de desconexiones).
- 2026-09-26: OAuth quitado, dirección secreta; Router a 16 GB de pago.
- 2026-09-29: auditoría, limpieza del repo y de HF, reorganización de `main` en raíces, sentinelas y mini-router en pausa, sistema de estado nuevo.
