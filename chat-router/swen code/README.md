# SWE CODE — mini-router en cascada

Cascada de 4 agentes de código manejados por modelos locales baratos (HF CPU 32GB, ~$0.19-0.31/M tokens). Cada agente ejecuta de verdad; el modelo solo piensa.

## Flujo

```
objetivo ──► [1] codex     (Qwen2.5-Coder-1.5B)  escribe el code
         ──► [2] opencode  (Qwen3.5-0.8B)        revisa + refactoriza
         ──► [3] swe-agent (Qwen3-0.6B)          ejecuta / despliega
         ──► [4] openhands (DeepSeek-Coder-1.3B) revisa lo desplegado
         ──► veredicto_final + recibos por paso
```

Un paso FAIL → cascada para y devuelve recibo del paso que cayó.

## Uso

```bash
# URLs de los 3 servidores existentes (llama-server mirror del storage HF):
export SWECODE_URL_S1="http://<s1>:8080/v1"   # codex escribe
export SWECODE_URL_S2="http://<s2>:8080/v1"   # opencode + openhands
export SWECODE_URL_S3="http://<s3>:8080/v1"   # swe-agent ejecuta
# o una sola para todo: export SWECODE_BASE_URL="http://<server>/v1"
python3 mini_router.py "arregla el bug de login en app.py"
```

## Handoff / enlaces

| Pieza | Ubicación |
|---|---|
| Ficha de la cascada (DSL) | `chat-router/swen code/cascada.json` |
| Config de motores | `chat-router/swen code/motores.json` |
| Agentes descargados | `chat-router/agentes/agentes-listos/` (codex, opencode, SWE-agent, openhands-software-agent-sdk) |
| Motor descarga/extracción | `chat-router/motores/motores-descarga/` |
| Inputs verbatim | `chat-router/swen code/INPUTS_VERBATIM.md` |
| Modelos en HF | jobs de grockbot → llama-server (OpenAI-compatible) |
| Cara del chat | OpenClaw → provider OpenAI-compatible → este mini-router |
