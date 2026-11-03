# CHECKLIST WATCHDOG RIU / OpenClaw / Yaiwes
Ciclo: 2026-11-03 12:09 UTC
Health: OK (status=ok, commit=9e2c7d194692b8eabf695130897fcebb01c06f6c, banco_abierto=true)
MCP salud: OK (herramientas: chat, github_leer, github_escribir, salud, etc.; commit visible)

Tests /chat/send:
- groq/qwen/qwen3.8-27b: OK (reply Hola, via harness)
- groq/openai/gpt-oss-120b: OK (via harness, tokens)
- nvidia/minimaxai/minimax-m3.1-flash: OK (reply OK)

MCP chat: OK (mismo modelos, param mensajes)
github_leer: OK (leyó checklist.md)

Estados:
I01 Checkpoint/reinicio MVP: CERRADO (health + commit visible, autoactualizacion AL_DIA)
I02 5 agentes cableados + harness DeepSeek: VALIDACION (harness path OK en tests; DeepSeek modelos listados en /v1/models y salud)
I03 SWE CODE free / SWEN CODE autónomo: PENDIENTE (modelos swecode-* visibles en /v1/models; no probados aún)
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
