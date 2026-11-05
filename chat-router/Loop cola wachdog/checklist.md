# CHECKLIST WATCHDOG RIU / OpenClaw / Yaiwes
Ciclo: 2026-11-05 ~22:15 UTC
Health: OK ({"status":"ok","commit":"5c2091f5601bd344fba46b750cee12c78abd9c85","banco_abierto":true,...})
MCP salud: OK (status ok, modelos listados, herramientas incluyendo github_leer; proveedores_externos groq/nvidia/deepseek=0)

Tests /chat/send:
- groq/openai/gpt-oss-120b: BLOQUEADO (GROQ_NVIDIA_REINTENTOS / sin GROQ_API_KEY)
- groq/qwen/qwen3.8-27b: BLOQUEADO (sin clave)
- nvidia/z-ai/glm-5.3: BLOQUEADO (sin NVIDIA_API_KEY)

MCP chat:
- groq/*: BLOQUEADO (Groq sin clave)
- qwen3.8-max: BLOQUEADO (QWEN_API_KEY no disponible en banco)
- nvidia: BLOQUEADO

github_leer: OK (lista raíz del repo correctamente)

UI: riu-jev-bridge.vercel.app OK (interfaz cargada, recuperando historial)

Estados:
I01 Checkpoint/reinicio MVP: CERRADO (space recuperado, health + MCP OK)
I02 5 agentes cableados + harness DeepSeek: VALIDACION (no re-probado fully; keys missing)
I03 SWE CODE free / SWEN CODE autónomo: PENDIENTE
I04 Modelos selectores: GAPS (proveedores externos sin claves en banco; tests fallan)
I05 System prompt MVP: VALIDACION
I06 Acceso HF + GitHub: CERRADO (HF up, github_leer OK)
I07 Frontend selectores: CERRADO
I08 Yaiwes + OpenClaw UI: CERRADO (UI responde)
I09 HTTP + MCP: CERRADO (salud + tools OK)
I10 Tarea 1: PENDIENTE
I11 Tarea 2: PENDIENTE
I12 Watchdog: CERRADO (ciclo ejecutado, checklist actualizada)

Siguiente: I04 (configurar claves GROQ/NVIDIA/QWEN en el banco del Space para desbloquear tests de modelos prioritarios; luego re-probar /chat/send y MCP chat).
