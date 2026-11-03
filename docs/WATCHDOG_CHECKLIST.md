# WATCHDOG CHECKLIST RIU / OpenClaw / Yaiwes
Ciclo: 2026-11-03 03:09 EST
Commit router: c4e04b80d10daf49d9047ee8d38c2f8954740e23
Rama: reorganizacion

## Estado Ixx
- I01 Checkpoint/reinicio MVP: CERRADO (health ok, latido ok, commit presente)
- I02 5 agentes cableados + harness DeepSeek: GAPS (permisos.agentes=false; proveedores deepseek=0)
- I03 SWE CODE free / SWEN CODE autónomo: PENDIENTE (modelos swecode-* listados, no testeados E2E)
- I04 Modelos selectores: CERRADO (v1/models + /chat/send Groq OK)
- I05 System prompt MVP: VALIDACION (permisos.system_prompt=true)
- I06 Acceso HF + GitHub: CERRADO (github_leer OK en reorganizacion; HF health OK)
- I07 Frontend selectores: PENDIENTE (UI Vercel no verificada en este ciclo)
- I08 Yaiwes + OpenClaw UI: PENDIENTE
- I09 HTTP + MCP: CERRADO (/chat/send 200, /mcp tools/list + tools/call OK, salud OK)
- I10 Tarea 1: PENDIENTE
- I11 Tarea 2: PENDIENTE
- I12 Watchdog: CERRADO (este ciclo ejecutado)

## Tests ciclo
1. Health: OK
2. MCP salud: OK (herramientas 14, proveedores groq=6 nvidia=5)
3. /chat/send groq/openai/gpt-oss-120b: OK1 (921ms)
4. /chat/send groq/qwen/qwen3.8-27b: OK2 (615ms)
5. /chat/send qwen3.8-max: OK3 (via lfm2.5-350m, 19s)
6. github_leer: OK (lista raíz reorganizacion)

Siguiente: I03 / I07 verificación frontend y agentes.