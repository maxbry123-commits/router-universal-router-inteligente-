# CHECKLIST WATCHDOG RIU / OpenClaw / Yaiwes
Ciclo: 2026-11-05 ~03:10 UTC
Health: BLOQUEADO (HF space comand-center-1-riu-router.hf.space paused: "The space is paused, ask a maintainer to restart it")
MCP salud: BLOQUEADO (no se pudo alcanzar backend por space paused)

Tests /chat/send:
- groq/openai/gpt-oss-120b: NO EJECUTADO (space paused)
- groq/qwen/qwen3.8-27b: NO EJECUTADO (space paused)
- nvidia/minimaxai/minimax-m3.1-flash: NO EJECUTADO (space paused)

MCP chat: NO EJECUTADO (space paused)
github_leer: NO EJECUTADO (space paused)

UI: riu-jev-bridge.vercel.app responde HTML pero backend no disponible.

Estados:
I01 Checkpoint/reinicio MVP: BLOQUEADO (space paused, health no alcanzable)
I02 5 agentes cableados + harness DeepSeek: VALIDACION (previo OK, este ciclo no re-probado)
I03 SWE CODE free / SWEN CODE autónomo: PENDIENTE
I04 Modelos selectores: CERRADO
I05 System prompt MVP: VALIDACION
I06 Acceso HF + GitHub: GAPS (HF space paused; GitHub MCP no testeable este ciclo)
I07 Frontend selectores: CERRADO
I08 Yaiwes + OpenClaw UI: VALIDACION (UI HTML OK, backend paused)
I09 HTTP + MCP: BLOQUEADO (space paused)
I10 Tarea 1: PENDIENTE
I11 Tarea 2: PENDIENTE
I12 Watchdog: CERRADO (ciclo ejecutado, checklist actualizada con fallo de space)

Siguiente: Reiniciar space HF y re-ejecutar Health + tests (I01/I09), luego I03 SWE CODE free / SWEN CODE autónomo.
