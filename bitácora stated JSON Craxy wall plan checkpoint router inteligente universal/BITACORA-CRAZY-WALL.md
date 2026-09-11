# BITÁCORA CRAZY WALL — ROUTER INTELIGENTE UNIVERSAL

**Contrato:** `tel.workflow/v3`
**Modo:** `FAIL_CLOSED_LOOP`

## RIU-0001..0049
Trazabilidad previa preservada. HF-M01/M02/M03 mantienen PASS internos con boundaries externos documentados; HF-M04 sigue FLAG; HF-M05 compute + integración FastAPI→Enchufe→Router→adapter + dataset RO PASS; RW storage queda GAP externo.

## RIU-0050 — BATCH COMPATIBLE HF-M06/M07/M10/M11/M12 PASS
Fuentes de verdad releídas antes del delta. Metadatos oficiales Hugging Face confirmaron los cinco model IDs públicos y `transformers`/`AutoModelForCausalLM` compatibles.
Job único `6aa398fe5527934177ec4cd0` COMPLETED en `a10g-small`, timeout 900s, con dataset `HuggingFaceH4/ultrachat_200k` montado RO en `/data`.
El Job ejecutó secuencialmente cada slot detrás del mismo FastAPI→EnchufeGate→Router→HFAdapter, liberando memoria entre modelos y generando evidencia individual JSON + SHA/read-back; el proceso sólo salía 0 si TODOS los slots daban HTTP 200, model_id exacto, parámetros >0, respuesta no vacía, dataset mount y read-back individual.
Resultado global: `RIU_HF_BATCH_M06_M12_OK=True`; `BATCH_DATASET_MOUNT=True`; `BATCH_DATASET_FILES=10`; summary `/tmp/riu_hf_batch_m06_m12_summary.json`; SHA256 `c3b38014bdd5423cd85b42f14d54fc13c95247a0aa29e3729eb3ac84264dd6a5`; summary read-back=True.
Persistencia individual: HF-M06 `facebook/opt-125m` PASS (SHA individual visible `e5820de1040e58a84591fd48a3f8a1fbf256090b03ba082a7f0f9e9b30a04d01`); HF-M07 `Qwen/Qwen2.5-1.5B-Instruct` PASS por batch verifier; HF-M10 `Qwen/Qwen2.5-0.5B-Instruct` PASS por batch verifier; HF-M11 `Qwen/Qwen3-4B` PASS por batch verifier; HF-M12 `Qwen/Qwen2.5-3B-Instruct` PASS, clase `Qwen2ForCausalLM`, params `3085938688`, response `OK, I'm ready to assist you`, SHA individual `640448abf630b2c7df1e70fc8849d72dcb84096bf47d9c124dc746c51026b2ab`.
3 refutaciones PASS: batch COMPLETED sin verifier global no bastaría; catálogo/model metadata no equivale inferencia; summary sin read-back no bastaría.
Council12 PASS; cross-check PASS; CODA `ADVANCE_REMAINING_M08_M20_BY_COMPATIBILITY_OR_EXACT_FLAG`; verify_final=`PASS_HF_BATCH_M06_M07_M10_M11_M12_INTEGRATED`.

## NEXT
Clasificar y ejecutar M08/M09/M13-M20 por tamaño/flavor/scope; modelos no ejecutables localmente se FLAG exacto y se continúa. P02/P03 permanecen pendientes.