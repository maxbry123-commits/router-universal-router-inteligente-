# CHECKLIST WATCHDOG RIU / OpenClaw / Yaiwes
Ciclo: 2026-11-04 ~18:07 UTC
Health: OK (status=ok, commit=9ac9fd673d441ba008adb1de4d3afd1c85f60cd3, autoactualizacion=AL_DIA, banco_abierto=true, checkpoint_coda_disponible=true)
MCP salud: OK (initialize + tools/list + tools/call salud responde; modelos Groq/Nvidia visibles; deepseek=0)

Tests /chat/send:
- groq/openai/gpt-oss-120b: OK (reply pong, harness, ~0.75s)
- groq/qwen/qwen3.8-27b: OK (reply, harness, ~0.58s)
- nvidia/minimaxai/minimax-m3.1-flash: OK (reply, harness, ~0.70s)

MCP chat: OK (qwen3.8-27b responde via tools/call mensajes)
github_leer: GAPS (404 path o acceso; no listado este ciclo)

Estados:
I01 Checkpoint/reinicio MVP: CERRADO (health estable, commit visible, banco_abierto=true, checkpoint_coda=true)
I02 5 agentes cableados + harness DeepSeek: VALIDACION (harness funciona para Groq y Nvidia; DeepSeek proveedores_externos=0)
I03 SWE CODE free / SWEN CODE autónomo: PENDIENTE
I04 Modelos selectores: CERRADO
I05 System prompt MVP: VALIDACION
I06 Acceso HF + GitHub: GAPS (HF space OK; GitHub via MCP github_leer falla 404)
I07 Frontend selectores: CERRADO
I08 Yaiwes + OpenClaw UI: CERRADO (UI riu-jev-bridge.vercel.app responde HTML)
I09 HTTP + MCP: VALIDACION (HTTP /chat/send OK; MCP initialize/tools/call chat OK; github_leer GAPS)
I10 Tarea 1: PENDIENTE
I11 Tarea 2: PENDIENTE
I12 Watchdog: CERRADO (ciclo ejecutado, checklist actualizada)

Siguiente: I03 SWE CODE free / SWEN CODE autónomo.
