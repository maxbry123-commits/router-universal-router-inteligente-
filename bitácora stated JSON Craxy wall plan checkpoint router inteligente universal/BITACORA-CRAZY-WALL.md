# BITÁCORA CRAZY WALL — ROUTER INTELIGENTE UNIVERSAL

**Contrato:** `tel.workflow/v3`
**Modo:** `FAIL_CLOSED_LOOP`

## RIU-0001..0047
Trazabilidad previa preservada: catálogo 20; HF-M01 compute/hot-path/dataset RO + FLAG provider-auth 403; HF-M02 compute/integración + FLAG storage RW 403; HF-M03 compute GPU + integración FastAPI→Enchufe→Router→adapter + dataset RO PASS; storage RW PENDING; HF-M04 FLAG por anomalía timeout-state; HF-M05 Job real lanzado.

## RIU-0048 — HF-M05 REAL COMPUTE PASS
Fuentes de verdad releídas antes del delta. Investigación oficial Hugging Face/Qwen confirmó `Qwen/Qwen2.5-7B-Instruct` como causal LM de ~7.61B parámetros y uso con `AutoModelForCausalLM`/`AutoTokenizer`/chat template.
Job real HF-M05 `6aa3781121047bf1b0374a5c` inspeccionado `COMPLETED` en `a10g-small`. Logs: `Qwen2ForCausalLM`, `7615616512` parámetros, `CUDA=True`, salida `RIU_HF_M05_OK`, `RIU_HF_M05_OK=True`, `RIU_HF_M05_SECONDS=126.386`.
Decisión fail-closed: certificar únicamente compute real HF-M05. No READY por compute; adapter/dataset/storage/FastAPI→Enchufe→Router siguen pendientes.
3 refutaciones: COMPLETED sin output no bastaría; presencia del modelo no prueba inferencia; compute PASS no prueba integración/READY.
Council12 PASS; cross-check PASS; CODA `ADVANCE_HF_M05_INTEGRATION_NO_READY_UNTIL_HOT_PATH_AND_STORAGE_EVIDENCE`; verify_final=`PASS_HF_M05_REAL_COMPUTE_ONLY`.

## NEXT
Cola 1×1: validar HF-M05 adapter + dataset/storage + FastAPI→Enchufe→Router con Job real y exigir HTTP/log/ruta+SHA/read-back antes de persistir integración. P02/P03 siguen PENDING.