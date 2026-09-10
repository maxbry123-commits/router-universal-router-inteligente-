# BITÁCORA CRAZY WALL — ROUTER INTELIGENTE UNIVERSAL

**Contrato:** `tel.workflow/v3`
**Modo:** `FAIL_CLOSED_LOOP`

## RIU-0001..0044
Trazabilidad previa preservada: catálogo 20; HF-M01 compute/hot-path/dataset RO + FLAG provider-auth 403; HF-M02 compute/integración + FLAG storage RW 403; HF-M03 compute GPU real PASS.

## RIU-0045 — HF-M03 INTEGRACIÓN REAL
Fuentes de verdad releídas antes del delta. HF Job `6aa2f8e921047bf1b03732b7` terminó `COMPLETED` el 2026-09-10T18:49:01Z.
Read-back logs: `HTTP_STATUS 200`; cuerpo model=`Qwen/Qwen3-8B`, assistant=`RIU_HF_M03_ROUTE_OK`; `FASTAPI_ENCHUFE_ROUTER_M03_OK True`; `MODEL_CLASS Qwen3ForCausalLM`; `PARAMS 8190735360`; `CUDA_AVAILABLE True`; `MAX_MEMORY_ALLOCATED 16396255232`.
El Job usó `HuggingFaceH4/ultrachat_200k` montado RO en `/data` y ejecutó el gateway FastAPI real del repo -> Enchufe Gate -> RedUniversal/router -> adapter/ejecutor Qwen3.
Decisión: HF-M03 adapter + dataset RO + FastAPI/Enchufe/Router PASS. Storage RW persistente NO certificado; HF-M03 permanece NO READY y hereda el boundary de storage del proyecto.
3 refutaciones: HTTP 200 no demuestra storage persistente; dataset RO no equivale a bucket RW; éxito M03 no cierra FLAGs externos M01/M02.
Council12 PASS; cross-check PASS; CODA `PERSIST_HF_M03_INTEGRATION_KEEP_NO_READY_ADVANCE_SAFE_HF_M04`; verify_final=`PASS_HF_M03_INTEGRATED_HOT_PATH_STORAGE_RW_PENDING`.

## NEXT
Cola 1×1: HF-M04 compute real, manteniendo `FLAG-HF-PROVIDER-AUTH-001`, `FLAG-HF-M02-RW-STORAGE-AUTH-001` y GAP storage abiertos. P02/P03 siguen PENDING.