# SWE CODE — mini-router en cascada

Cascada de 4 agentes de código manejados por modelos locales baratos (HF CPU, cap $0.30/M tokens). Cada agente ejecuta de verdad; el modelo solo piensa.

## Arquitectura

```
chat ──► plugins ──► deepseek_harness ──► HTTP router ──► plugins/swe_code ──► esta carpeta
                                                       (nada habla directo al router)

objetivo ──► [1] codex     (Qwen2.5-Coder-1.5B)  escribe el code
         ──► [2] opencode  (Qwen3.5-0.8B)        revisa + refactoriza
         ──► [3] swe-agent (LFM2.5-350M)         ejecuta / despliega
         ──► [4] openhands (LFM2.5-350M)         revisa lo desplegado
         ──► veredicto_final + recibos por paso

Paralelo: 2+ secciones por conv_id — tabs web separadas o slots S1/S2/S3.
Espejo: cualquier modelo se clona a otro conv_id/slot para dividir trabajo.
```

- **Cola HF**: S1/S2/S3 = slots intercambiables — cualquier Space sirve cualquier modelo vía `model=`, GGUF bajo demanda desde dataset `swe-code-hf-gguf`, 1 vivo por Space, unload tras 5 min idle, encola al siguiente libre (máx 3).
- Un paso FAIL → cascada para y devuelve recibo del paso que cayó.
- En HF solo vive el código mínimo (serving); lógica, manuales y fichas están en GitHub.

## Uso

```bash
# Cola HF: cada slot carga el GGUF que pida el model= del request
export SWECODE_URL_S1="https://<s1>/v1"
export SWECODE_URL_S2="https://<s2>/v1"
export SWECODE_URL_S3="https://<s3>/v1"
# o una sola para todo: export SWECODE_BASE_URL="http://<server>/v1"
python3 mini_router.py "arregla el bug de login en app.py"
```

## Handoff / enlaces

| Pieza | Ubicación |
|---|---|
| Ficha de la cascada (DSL) | `chat-router/SWE CODE/cascada.json` |
| Config de motores | `chat-router/SWE CODE/motores.json` |
| Puente web (cuentas Qwen/DeepSeek) | `chat-router/SWE CODE/web-bridge/` |
| Manual compartido (2 chats) | `chat-router/SWE CODE free/INSTRUCCIONES.md` |
| Agentes descargados | `chat-router/agentes/agentes-listos/` (codex, opencode, SWE-agent, openhands-software-agent-sdk) |
| Motor descarga/extracción | `chat-router/motores/motores-descarga/` |
| Inputs verbatim | `chat-router/SWE CODE/INPUTS_VERBATIM.md` |
| Modelos en HF | jobs de grockbot → llama-server (OpenAI-compatible) |
| Cara del chat | OpenClaw → provider OpenAI-compatible → este mini-router |
