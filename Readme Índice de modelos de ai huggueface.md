# Readme Índice de modelos de AI Hugging Face — certificación 20/20

## Regla de verdad
`CATALOG_OBSERVED != TESTED != READY`. Cada slot debe terminar con `PASS` o `FLAG/GAP` explícito y evidencia.

## Estado actual
Core Router=`VERIFIED_CLOSED`; certificación ampliada=`ACTIVE_LOOP_MODEL_CERTIFICATION`.

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

## Slots con FLAG/GAP que deben quedar individualmente resueltos/contabilizados
- M04 `unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF` — dos timeout-state anomalies; `FLAG-HF-M04-COMPUTE-001`.
- M08 `farbodtavakkoli/OTel-2.0-LLM-31B-IT` — flavor/hardware FLAG.
- M09 `openai/gpt-oss-20b` — Job `6aa3a3dd5527934177ec4e80` COMPLETED; `content=null`; response-contract FLAG.
- M13 `openai/gpt-oss-120b` — flavor/hardware FLAG.
- M14 `Qwen/Qwen3-32B` — flavor/hardware FLAG.
- M15 `dphn/dolphin-2.9.1-yi-1.5-34b` — flavor/hardware FLAG.
- M16 `deepseek-ai/DeepSeek-V4-Flash-0731` — flavor/hardware FLAG.
- M17 `ornith-ai/Ornith-1.0-9B-GGUF` — Job `6aa3a24f5527934177ec4e3c` timeout/canceled.
- M18 `ornith-ai/Ornith-1.5-9B-GGUF` — **no alcanzado** por job secuencial anterior; requiere test individual obligatorio.
- M19 `Qwen/Qwen-72B` — flavor/hardware FLAG.

## Jobs/evidencia principal
Catálogo 20=`6aa2513d5527934177ebfaad`; M03 hot-path=`6aa2f8e921047bf1b03732b7`; M05 compute=`6aa3781121047bf1b0374a5c`; M05 integration=`6aa3977e21047bf1b0374e94`; M20=`6aa3a3cd5527934177ec4e7e`; M09=`6aa3a3dd5527934177ec4e80`; M17/M18=`6aa3a24f5527934177ec4e3c`.

## GAP de intento reciente
Batch `6aa3943f21047bf1b0374dc8` para M06/M10/M07 falló por entorno `ModuleNotFoundError: transformers`; no cuenta como test de modelo y no invalida evidencia previa de esos slots.

## Próxima cola
M18 individual -> revisar FLAGS restantes con StrategyDelta/timeout corto -> 20/20 accounted -> regresión E2E final -> ADN final.