# WATCHDOG CHECKLIST RIU / OpenClaw / Yaiwes
Ciclo: 2026-11-04 03:15 EST
Commit router: d82217f15ee29c1fca56a936ef8970320d69c827
Rama: reorganizacion

## Estado Ixx
- I01 Checkpoint/reinicio MVP: CERRADO (health ok, latido/autoactualizacion AL_DIA, commit d82217f, checkpoint_coda_disponible)
- I02 5 agentes cableados + harness DeepSeek: GAPS (permisos.agentes no confirmados; deepseek proveedores limitados en plan personal)
- I03 SWE CODE free / SWEN CODE autónomo: BLOQUEADO (modelos swecode-* listados pero no permitidos en plan personal; error "modelo no permitido")
- I04 Modelos selectores: CERRADO (v1/models OK; /chat/send groq/openai/gpt-oss-120b, groq/qwen/qwen3.8-27b y nvidia/minimaxai/minimax-m3.1-flash OK)
- I05 System prompt MVP: VALIDACION (permisos.system_prompt implícito en harness; no test explícito de override)
- I06 Acceso HF + GitHub: CERRADO (github_leer OK en reorganizacion; HF health + MCP salud OK)
- I07 Frontend selectores: VALIDACION (UI https://riu-jev-bridge.vercel.app 200 OK)
- I08 Yaiwes + OpenClaw UI: PENDIENTE (UI responde pero /openclaw/health no analizado; integración no verificada E2E)
- I09 HTTP + MCP: CERRADO (/chat/send 200, /mcp initialize + tools/list + tools/call chat/github_leer OK)
- I10 Tarea 1: PENDIENTE
- I11 Tarea 2: PENDIENTE
- I12 Watchdog: CERRADO (este ciclo ejecutado y checklist actualizada)

## Tests ciclo
1. Health: OK (status ok, commit d82217f, banco_abierto true, AL_DIA)
2. MCP initialize + tools/list: OK
3. /chat/send groq/openai/gpt-oss-120b: OK (pong, ~599ms)
4. /chat/send groq/qwen/qwen3.8-27b: OK (pong, ~652ms)
5. /chat/send nvidia/minimaxai/minimax-m3.1-flash: OK (pong, ~713ms)
6. MCP chat + github_leer: OK
7. UI Vercel: 200 OK

Siguiente: I03 / I08 verificación de permisos de modelos swecode y OpenClaw UI E2E.
