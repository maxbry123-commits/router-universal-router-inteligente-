# CHECKLIST WATCHDOG RIU / OpenClaw / Yaiwes
Ciclo: 2026-11-05 ~18:10 UTC
Health: BLOQUEADO (HF Space https://comand-center-1-riu-router.hf.space returning "Preparing Space" HTML; no JSON /health)
MCP salud: BLOQUEADO (mismo, space no disponible)

Tests /chat/send:
- groq/openai/gpt-oss-120b: BLOQUEADO (space down)
- groq/qwen/qwen3.8-27b: BLOQUEADO
- nvidia/z-ai/glm-5.3: BLOQUEADO (previous 410 + space down)

MCP chat:
- groq/*: BLOQUEADO
- nvidia: BLOQUEADO

github_leer: BLOQUEADO (MCP no disponible)

UI: riu-jev-bridge.vercel.app OK (200, muestra "Sin respuesta del servidor"). HF space preparing.

Estados:
I01 Checkpoint/reinicio MVP: BLOQUEADO (space preparing, health no responde)
I02 5 agentes cableados + harness DeepSeek: VALIDACION (no re-probado; space down)
I03 SWE CODE free / SWEN CODE autónomo: PENDIENTE
I04 Modelos selectores: BLOQUEADO (space down; Nvidia gap previo)
I05 System prompt MVP: VALIDACION
I06 Acceso HF + GitHub: GAPS (HF space preparing; github_leer no testeable)
I07 Frontend selectores: CERRADO
I08 Yaiwes + OpenClaw UI: CERRADO (UI responde)
I09 HTTP + MCP: BLOQUEADO (space down)
I10 Tarea 1: PENDIENTE
I11 Tarea 2: PENDIENTE
I12 Watchdog: CERRADO (ciclo ejecutado, checklist actualizada)

Siguiente: I01 (reiniciar HF Space en Hugging Face para recuperar health/MCP; luego re-probar tests Groq).
