# WATCHDOG CHECKLIST RIU / OpenClaw / Yaiwes
Ciclo: 2026-11-03 10:09 EST
Commit router: 507ffbc0cfb1686fae6a211f1107420c88a1bcd8
Rama: reorganizacion

## Estado Ixx
- I01 Checkpoint/reinicio MVP: CERRADO (health ok, latido/autoactualizacion AL_DIA, commit presente, checkpoint_coda_disponible)
- I02 5 agentes cableados + harness DeepSeek: GAPS (permisos.agentes no confirmados; deepseek proveedores limitados en plan personal)
- I03 SWE CODE free / SWEN CODE autónomo: BLOQUEADO (modelos swecode-* listados pero no permitidos en plan personal; error "modelo no permitido")
- I04 Modelos selectores: CERRADO (v1/models OK; /chat/send groq/openai/gpt-oss-120b, groq/qwen/qwen3.8-27b y nvidia/minimaxai/minimax-m3.1-flash OK)
- I05 System prompt MVP: VALIDACION (permisos.system_prompt implícito en harness; no test explícito de override)
- I06 Acceso HF + GitHub: CERRADO (github_leer OK en reorganizacion; HF health + MCP salud OK)
- I07 Frontend selectores: VALIDACION (UI https://riu-jev-bridge.vercel.app 200 OK, título YAIWES · Organización, shell.css cargado)
- I08 Yaiwes + OpenClaw UI: PENDIENTE (UI responde pero /openclaw/health binario no analizado; integración no verificada E2E)
- I09 HTTP + MCP: CERRADO (/chat/send 200, /mcp initialize + tools/list + tools/call chat/github_leer/salud OK)
- I10 Tarea 1: PENDIENTE
- I11 Tarea 2: PENDIENTE
- I12 Watchdog: CERRADO (este ciclo ejecutado y checklist actualizada)

## Tests ciclo
1. Health: OK (status ok, commit 507ffbc0, banco_abierto true)
2. MCP salud: OK (herramientas 14+, status ok)
3. /chat/send groq/openai/gpt-oss-120b: OK (pong, ~666ms)
4. /chat/send groq/qwen/qwen3.8-27b: OK (pong, ~644ms)
5. /chat/send nvidia/minimaxai/minimax-m3.1-flash: OK (pong, ~11s)
6. MCP chat + github_leer: OK
7. UI Vercel: 200 OK

Siguiente: I03 / I08 verificación de permisos de modelos swecode y OpenClaw UI E2E.
