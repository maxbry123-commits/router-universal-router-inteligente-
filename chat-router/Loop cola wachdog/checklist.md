# CHECKLIST WATCHDOG RIU / OpenClaw / Yaiwes

Ciclo: 2026-11-07 ~07:11 UTC
Health: OK ({"status":"ok","commit":"4722f1dffcf25a2ecf2b63b36fc847fbc922115f","banco_abierto":true,"clave_qwen_presente":false,"modelo_defecto":"qwen3.8-max","autoactualizacion":"GIT_PULL_FALLIDO","cpu":16.4})
MCP salud: OK (JSON-RPC /mcp initialize OK, tools/list OK, tools: chat,github_leer,salud,github_escribir,... )

Tests /chat/send:
- groq/openai/gpt-oss-120b: OK (harness "Pong", ms~1144)
- groq/qwen/qwen3.8-27b: OK (harness "Pong", ms~879)
- nvidia/z-ai/glm-5.3: BLOQUEADO (HTTP 502/410 PROVEEDOR_NVIDIA_HTTP_410 peticion_invalida)

MCP chat:
- groq/openai/gpt-oss-120b: OK (texto "Pong")
- groq/qwen/qwen3.8-27b: OK (texto "Pong")
- nvidia/z-ai/glm-5.3: BLOQUEADO (PROVEEDOR_NVIDIA_HTTP_410)

github_leer: OK (lista raíz: .claude, .github, .gitignore, AGENTS.md, chat-router, ops, etc.)

UI: riu-jev-bridge.vercel.app OK

Estados:
I01 Checkpoint/reinicio MVP: CERRADO (space up, health + MCP OK, commit 4722f1d)
I02 5 agentes cableados + harness DeepSeek: VALIDACION (harness funciona en Groq; DeepSeek proveedores=0)
I03 SWE CODE free / SWEN CODE autónomo: PENDIENTE
I04 Modelos selectores: GAPS (Groq OK con 6 credenciales; Nvidia 410 invalid request; DeepSeek 0; qwen clave false)
I05 System prompt MVP: VALIDACION
I06 Acceso HF + GitHub: CERRADO (HF up, github_leer OK)
I07 Frontend selectores: CERRADO
I08 Yaiwes + OpenClaw UI: CERRADO (UI responde)
I09 HTTP + MCP: CERRADO (salud + tools + chat OK)
I10 Tarea 1: PENDIENTE
I11 Tarea 2: PENDIENTE
I12 Watchdog: CERRADO (ciclo ejecutado, checklist actualizada)

Siguiente: I04 (investigar/arreglar Nvidia HTTP 410 peticion_invalida; configurar clave Qwen si falta; re-probar modelos Nvidia y DeepSeek). Posible: revisar autoactualizacion GIT_PULL_FALLIDO.
