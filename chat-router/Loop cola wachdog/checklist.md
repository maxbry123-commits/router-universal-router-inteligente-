# CHECKLIST WATCHDOG RIU / OpenClaw / Yaiwes
Ciclo: 2026-11-03 02:09 UTC
Health: OK (status=ok, commit=e0586093ed789ae1e28ef95b603ce103d48c5a3b, banco_abierto=true)
MCP salud: OK (herramientas incluyen chat, github_leer, etc.)

Tests /chat/send:
- groq/qwen/qwen3.8-27b: OK (reply OK, via harness)
- groq/openai/gpt-oss-120b: OK
- nvidia/minimaxai/minimax-m3.1-flash: OK

MCP chat: OK (mismo modelos)
github_leer: OK (leyó INSTRUCCIONES_ANTONIO.md)

Estados:
I01 Checkpoint/reinicio MVP: CERRADO (health + commit visible)
I02 5 agentes cableados + harness DeepSeek: VALIDACION (harness path OK en tests; DeepSeek modelos listados)
I03 SWE CODE free / SWEN CODE autónomo: PENDIENTE (modelos swecode-* visibles en /v1/models)
I04 Modelos selectores: CERRADO (selectores en modelos y UI shell)
I05 System prompt MVP: VALIDACION (permisos system_prompt true)
I06 Acceso HF + GitHub: CERRADO (github_leer OK; HF space activo)
I07 Frontend selectores: CERRADO (UI riu-jev-bridge y shell del router con selectores)
I08 Yaiwes + OpenClaw UI: CERRADO (UI YAIWES Organización carga, /openclaw path existe)
I09 HTTP + MCP: CERRADO (health, /chat/send, /mcp tools/call OK)
I10 Tarea 1: PENDIENTE
I11 Tarea 2: PENDIENTE
I12 Watchdog: CERRADO (ciclo ejecutado, checklist actualizada)

Siguiente: I03 / I10 según prioridad de tareas.

