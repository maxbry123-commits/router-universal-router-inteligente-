# CHECKLIST WATCHDOG RIU / OpenClaw / Yaiwes
Ciclo: 2026-11-05 ~05:10 UTC
Health: CERRADO (status ok, commit 40c8d591abaa7ff6e008e9e0801dc022a968fc6a, banco_abierto true, autoactualizacion AL_DIA, checkpoint_coda_disponible true)
MCP salud: CERRADO (status ok, herramientas incluyen chat/github_leer/pendientes/archivos, proveedores_externos groq:6 nvidia:5)

Tests /chat/send:
- groq/openai/gpt-oss-120b: CERRADO (reply OK, modelo_respuesta openai/gpt-oss-120b)
- groq/qwen/qwen3.8-27b: CERRADO (reply OK, modelo_respuesta qwen/qwen3.8-27b)
- nvidia/z-ai/glm-5.3: BLOQUEADO (HTTP 410 PROVEEDOR_NVIDIA_HTTP_410: peticion_invalida credenciales_configuradas)

MCP chat:
- groq/qwen/qwen3.8-27b: CERRADO (texto OK)
- nvidia: BLOQUEADO (mismo 410)

github_leer: CERRADO (leyó LIVE_URL.json correctamente con repo+rama)

UI: riu-jev-bridge.vercel.app y HF space HTML OK.

Estados:
I01 Checkpoint/reinicio MVP: CERRADO (health + checkpoint disponible)
I02 5 agentes cableados + harness DeepSeek: VALIDACION (no re-probado este ciclo; DeepSeek proveedores 0)
I03 SWE CODE free / SWEN CODE autónomo: PENDIENTE
I04 Modelos selectores: CERRADO (Groq selectores responden; Nvidia gap)
I05 System prompt MVP: VALIDACION
I06 Acceso HF + GitHub: CERRADO (HF space vivo, github_leer MCP OK)
I07 Frontend selectores: CERRADO
I08 Yaiwes + OpenClaw UI: CERRADO (UI responde)
I09 HTTP + MCP: CERRADO (ambos funcionales; Nvidia externo fallido)
I10 Tarea 1: PENDIENTE
I11 Tarea 2: PENDIENTE
I12 Watchdog: CERRADO (ciclo ejecutado, checklist actualizada)

Siguiente: I03 SWE CODE free / SWEN CODE autónomo (Nvidia gap a investigar: 410 credenciales/petición inválida).
