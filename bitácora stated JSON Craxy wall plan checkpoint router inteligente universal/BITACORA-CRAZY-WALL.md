# BITÁCORA CRAZY WALL — ROUTER INTELIGENTE UNIVERSAL

**Contrato:** `tel.workflow/v3`
**Modo:** `FAIL_CLOSED_LOOP`

## RIU-0001..0045
Trazabilidad previa preservada: catálogo 20; HF-M01 compute/hot-path/dataset RO + FLAG provider-auth 403; HF-M02 compute/integración + FLAG storage RW 403; HF-M03 compute GPU + integración FastAPI→Enchufe→Router→adapter + dataset RO PASS; storage RW PENDING.

## RIU-0046 — HF-M04 TIMEOUT STRATEGYDELTA
Fuentes de verdad releídas antes del delta. HF-M04 model_id observado: `unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF`.
Job `6aa316585527934177ec29ee` seguía `RUNNING` con `timeout_seconds=1800` y sin logs finales útiles; documentación oficial HF indica que Jobs deben detenerse al superar timeout. Se registró `GAP-HF-M04-TIMEOUT-001` y el Job fue cancelado, sin marcar PASS.
StrategyDelta materialmente distinto: relanzamiento con timeout explícito `2h`/7200s, runtime `ghcr.io/ggml-org/llama.cpp:full-cuda`, flavor `a10g-small`, comando `llama-cli -hf unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF:TQ1_0 ... -ngl 99`.
Nuevo Job `6aa34d825527934177ec3d2c`; estado inicial `SCHEDULING`; no existe inferencia final todavía.
3 refutaciones: RUNNING no equivale output; metadata timeout no demuestra cierre automático; SCHEDULING del retry no demuestra compute PASS.
Council12 PASS; cross-check PASS; CODA `KEEP_HF_M04_NO_READY_WAIT_FOR_FINAL_INFERENCE_EVIDENCE`; verify_final=`HF_M04_RETRY_SCHEDULING_NO_PASS_YET`.

## NEXT
Cola 1×1: inspeccionar `6aa34d825527934177ec3d2c`; exigir `COMPLETED` + salida generada + runtime/GPU/log/URL antes de promover HF-M04 compute. P02/P03 siguen PENDING.