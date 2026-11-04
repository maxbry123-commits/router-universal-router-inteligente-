# CHECKLIST WATCHDOG RIU / OpenClaw / Yaiwes
Ciclo: 2026-11-04 ~12:10 UTC
Health: OK (status=ok, commit=976a4df595cfe36abcb52e9b64225412e1f801bb, autoactualizacion=ESPERANDO_PRIMER_CICLO, banco_abierto=true)
MCP salud: OK (tools/list + tools/call responden; chat y github_leer OK)

Tests /chat/send:
- groq/openai/gpt-oss-120b: OK (reply, harness, ~1.1s)
- groq/qwen/qwen3.8-27b: OK (reply, harness, ~0.8s)
- nvidia/minimaxai/minimax-m3.1-flash: OK (reply, harness)

MCP chat: OK (qwen3.8-27b responde via tools/call)
github_leer: OK (responde via MCP)

Estados:
I01 Checkpoint/reinicio MVP: CERRADO (health estable, commit visible, banco_abierto=true)
I02 5 agentes cableados + harness DeepSeek: VALIDACION (harness funciona para Groq y Nvidia; DeepSeek no re-testeado este ciclo)
I03 SWE CODE free / SWEN CODE autónomo: PENDIENTE
I04 Modelos selectores: CERRADO
I05 System prompt MVP: VALIDACION
I06 Acceso HF + GitHub: CERRADO (HF space responde; GitHub via MCP OK)
I07 Frontend selectores: CERRADO
I08 Yaiwes + OpenClaw UI: CERRADO (UI riu-jev-bridge.vercel.app 200 OK)
I09 HTTP + MCP: CERRADO (HTTP /chat/send + MCP initialize/tools/call/github_leer OK)
I10 Tarea 1: PENDIENTE
I11 Tarea 2: PENDIENTE
I12 Watchdog: CERRADO (ciclo ejecutado, checklist actualizada)

Siguiente: I03 SWE CODE free / SWEN CODE autónomo.
