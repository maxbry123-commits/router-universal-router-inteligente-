# Readme Índice de modelos de AI Hugging Face — certificación 20/20

## Regla de verdad
`CATALOG_OBSERVED != TESTED != READY`. Cada slot debe terminar con `PASS` o `FLAG/GAP` explícito y evidencia.

## Estado actual
Core Router=`VERIFIED_CLOSED`; certificación ampliada=`ACTIVE_LOOP_MODEL_CERTIFICATION`; 19/20 contabilizados antes del resultado terminal M18.

## Slots con evidencia previa PASS/ejecución verificada
- M01 `Qwen/Qwen3-0.6B` — compute/hot-path/dataset RO verificados; provider hosted auth mantiene FLAG 403.
- M02 `openai-community/gpt2` — compute + integración real verificados; RW storage mantiene FLAG 403.
- M03 `Qwen/Qwen3-8B` — GPU + FastAPI→Enchufe→Router→adapter + dataset RO verificados; RW persistente pendiente.
- M05 `Qwen/Qwen2.5-7B-Instruct` — GPU compute + integración previa verificados.
- M06 `facebook/opt-125m` — evidencia previa válida preservada.
- M07 `Qwen/Qwen2.5-1.5B-Instruct` — evidencia previa válida preservada.
- M10 `Qwen/Qwen2.5-0.5B-Instruct` — evidencia previa válida preservada.
- M11 `Qwen/Qwen3-4B` — evidencia previa válida preservada.
- M12 `Qwen/Qwen2.5-3B-Instruct` — evidencia previa válida preservada.
- M20 `Qwen/Qwen2.5-7B-Instruct-AWQ` — Job `6aa3a3cd5527934177ec4e7e`, response OK, PASS.

## Slots FLAG/GAP contabilizados
- M04 `unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF` — `FLAG-HF-M04-COMPUTE-001`.
- M08 `farbodtavakkoli/OTel-2.0-LLM-31B-IT` — flavor/hardware FLAG.
- M09 `openai/gpt-oss-20b` — Job `6aa3a3dd5527934177ec4e80` COMPLETED; `content=null`; response-contract FLAG.
- M13 `openai/gpt-oss-120b` — flavor/hardware FLAG.
- M14 `Qwen/Qwen3-32B` — flavor/hardware FLAG.
- M15 `dphn/dolphin-2.9.1-yi-1.5-34b` — flavor/hardware FLAG.
- M16 `deepseek-ai/DeepSeek-V4-Flash-0731` — flavor/hardware FLAG.
- M17 `ornith-ai/Ornith-1.0-9B-GGUF` — Job `6aa3a24f5527934177ec4e3c` timeout/canceled.
- M19 `Qwen/Qwen-72B` — flavor/hardware FLAG.

## M18 — único slot terminal pendiente
Model ID confirmado: `ornith-ai/Ornith-1.5-9B-GGUF`; GGUF 9B, llama.cpp compatible.
Attempt 1 `6aa475605527934177eca1cb`: `a10g-small`, llama.cpp CUDA, `Q3_K_S`, timeout 480s; terminó `ERROR exit 1`, NO PASS; log remoto visible sólo `HF_M18_START` por redirección stderr + `set -e`.
StrategyDelta diagnóstico `6aa475e721047bf1b0378e13`: `a10g-small`, `Q3_K_S`, ctx 128, n=1, timeout 180s, sin redirección. Último estado: `SCHEDULING / Pulling container image`.

## Jobs/evidencia principal
Catálogo 20=`6aa2513d5527934177ebfaad`; M03=`6aa2f8e921047bf1b03732b7`; M05 compute=`6aa3781121047bf1b0374a5c`; M05 integration=`6aa3977e21047bf1b0374e94`; M20=`6aa3a3cd5527934177ec4e7e`; M09=`6aa3a3dd5527934177ec4e80`; M18 diag=`6aa475e721047bf1b0378e13`.

## Próxima cola
M18 terminal -> 20/20 accounted -> regresión E2E final -> ADN final.