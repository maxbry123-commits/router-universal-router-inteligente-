# BITÁCORA CRAZY WALL — ROUTER INTELIGENTE UNIVERSAL

**Contrato:** `tel.workflow/v3`
**Modo:** `FAIL_CLOSED_LOOP`

## RIU-0001..0043
Trazabilidad previa preservada: catálogo 20, HF-M01 compute/hot-path/dataset RO + FLAG provider-auth 403; HF-M02 compute/integración + FLAG storage RW 403.

## RIU-0044 — HF-M03 REAL GPU COMPUTE
Fuentes de verdad releídas antes del delta. Investigación de HF/Qwen confirmó `Qwen/Qwen3-8B`, transformers/Qwen3 y benchmark BF16 ~15.9 GB GPU a contexto mínimo; se eligió `a10g-small`.
HF Job `6aa2ecbb21047bf1b037318e` terminó `COMPLETED` el 2026-09-10T17:49:24Z.
Read-back logs: `MODEL_CLASS Qwen3ForCausalLM`; `PARAMS 8190735360`; `LOAD_SECONDS 140.803`; `REPLY 'RIU_HF_M03_OK'`; `GEN_SECONDS 0.986`; `MAX_MEMORY_ALLOCATED 16396255232`; `HF_M03_REAL_COMPUTE_OK True`.
Registry V7 tenía deriva para HF-M02; se reconcilió a V8 preservando integración verificada y storage RW auth FLAG.
Decisión: HF-M03 compute real PASS solamente; adapter/dataset/storage/FastAPI siguen PENDING; HF-M03 NO READY.
3 refutaciones: compute != hot-path; GPU inference != storage persistence; HF-M03 success != cierre de FLAGs HF-M01/HF-M02.
Council12 PASS; cross-check PASS; CODA `PERSIST_HF_M03_COMPUTE_KEEP_NO_READY_QUEUE_INTEGRATION`; verify_final=`PASS_HF_M03_REAL_COMPUTE_ONLY`.

## NEXT
Cola 1×1: HF-M03 adapter + dataset/storage + FastAPI→Enchufe→Router en Job real. P02/P03 siguen PENDING.