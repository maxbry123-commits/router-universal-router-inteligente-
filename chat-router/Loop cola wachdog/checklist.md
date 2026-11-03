# CHECKLIST WATCHDOG RIU / OpenClaw / Yaiwes
Ciclo: 2026-11-03 21:10 UTC
Health: INTERMITENTE (status=ok, commit=caeeb1e98b cuando responde; frecuentemente 503 "space is in error")
MCP salud: BLOQUEADO (endpoints /mcp y /v1/models no responden consistentemente)

Tests /chat/send:
- groq/qwen/qwen3.8-27b: BLOQUEADO (space error, no se pudo POST)
- groq/openai/gpt-oss-120b: BLOQUEADO
- nvidia/minimaxai/minimax-m3.1-flash: BLOQUEADO

MCP chat: BLOQUEADO
github_leer: OK (leído checklist.md via GitHub API)

Estados:
I01 Checkpoint/reinicio MVP: GAPS (health intermitente, commit visible a veces)
I02 5 agentes cableados + harness DeepSeek: VALIDACION (previo OK, ahora no re-testeado)
I03 SWE CODE free / SWEN CODE autónomo: PENDIENTE
I04 Modelos selectores: CERRADO
I05 System prompt MVP: VALIDACION
I06 Acceso HF + GitHub: GAPS (HF space error frecuente; GitHub OK)
I07 Frontend selectores: CERRADO
I08 Yaiwes + OpenClaw UI: CERRADO (UI carga cuando space responde)
I09 HTTP + MCP: GAPS (health OK intermitente; MCP/chat no verificados este ciclo)
I10 Tarea 1: PENDIENTE
I11 Tarea 2: PENDIENTE
I12 Watchdog: CERRADO (ciclo ejecutado, checklist actualizada)

Siguiente: I03 / reiniciar space HF para desbloquear tests de modelos y MCP.
