# Readme Índice de modelos de AI Hugging Face — certificación 20/20

## Regla de verdad
`CATALOG_OBSERVED != TESTED != READY`. Cada slot termina con `PASS` o `FLAG/GAP` explícito y evidencia.

## Estado final
Core Router=`VERIFIED_CLOSED`; `MODEL_CERTIFICATION_20_OF_20_ACCOUNTED`; regresión global final=`PASS`.

## PASS/ejecución verificada
M01 `Qwen/Qwen3-0.6B`; M02 `openai-community/gpt2`; M03 `Qwen/Qwen3-8B`; M05 `Qwen/Qwen2.5-7B-Instruct`; M06 `facebook/opt-125m`; M07 `Qwen/Qwen2.5-1.5B-Instruct`; M10 `Qwen/Qwen2.5-0.5B-Instruct`; M11 `Qwen/Qwen3-4B`; M12 `Qwen/Qwen2.5-3B-Instruct`; M20 `Qwen/Qwen2.5-7B-Instruct-AWQ`.

## FLAG/GAP contabilizados
M04 `unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF` compute timeout; M08 `farbodtavakkoli/OTel-2.0-LLM-31B-IT` flavor/hardware; M09 `openai/gpt-oss-20b` response-contract content=null; M13 `openai/gpt-oss-120b` flavor/hardware; M14 `Qwen/Qwen3-32B` flavor/hardware; M15 `dphn/dolphin-2.9.1-yi-1.5-34b` flavor/hardware; M16 `deepseek-ai/DeepSeek-V4-Flash-0731` flavor/hardware; M17 `ornith-ai/Ornith-1.0-9B-GGUF` timeout; M18 `ornith-ai/Ornith-1.5-9B-GGUF` runtime/timeout; M19 `Qwen/Qwen-72B` flavor/hardware.

## M18 evidencia individual
`6aa475605527934177eca1cb` ERROR exit 1; `6aa475e721047bf1b0378e13` diagnosticó `no GGUF files found` con selector Q3_K_S y `--model is required`; StrategyDelta canónico Q4_K_M `6aa4769b5527934177eca24b` alcanzó RUNNING pero no terminó en la ventana corta de 240s y fue cancelado. Final=`FLAG-HF-M18-RUNTIME-TIMEOUT-001`; no PASS/READY.

## Gate final
20/20 slots contabilizados. Regresión `RIU FAST-CLOSE` run `34582284615`, job `103434377312`: success, `2 passed, 2 warnings in 6.75s`.
Estado=`VERIFIED_CLOSED`.