# BITÁCORA CRAZY WALL — ROUTER INTELIGENTE UNIVERSAL

**Contrato:** `tel.workflow/v3`
**Modo:** `FAIL_CLOSED_LOOP`

## RIU-0001..0046
Trazabilidad previa preservada: catálogo 20; HF-M01 compute/hot-path/dataset RO + FLAG provider-auth 403; HF-M02 compute/integración + FLAG storage RW 403; HF-M03 compute GPU + integración FastAPI→Enchufe→Router→adapter + dataset RO PASS; storage RW PENDING; HF-M04 primer timeout-state registrado y retry lanzado.

## RIU-0047 — HF-M04 FLAG + HF-M05 SAFE ADVANCE
Fuentes de verdad releídas antes del delta. La documentación oficial Hugging Face indica que un Job debe detenerse cuando supera su timeout configurado. Retry HF-M04 `6aa34d825527934177ec3d2c` fue inspeccionado aún `RUNNING` después de superar `timeout_seconds=7200`, con logs no finales/blank; se canceló sin PASS. Se eleva `FLAG-HF-M04-COMPUTE-001` y permanece `GAP-HF-M04-TIMEOUT-001`.
Regla FLAG aplicada: continuar sólo tarea P01 independiente segura. HF-M05 model_id observado y validado: `Qwen/Qwen2.5-7B-Instruct`; Hub metadata: text-generation, `AutoModelForCausalLM`, ~7615.6M parámetros. Comunidad técnica Qwen confirma uso por Transformers con `AutoModelForCausalLM`/`AutoTokenizer`.
Job real HF-M05 `6aa3781121047bf1b0374a5c` lanzado en `a10g-small`, imagen PyTorch CUDA, Transformers, timeout 30m; estado inicial `SCHEDULING`; no existe inferencia final todavía.
3 refutaciones: RUNNING fuera de timeout no equivale output; cancelar HF-M04 no lo cierra como PASS; SCHEDULING HF-M05 no demuestra compute PASS.
Council12 PASS; cross-check PASS; CODA `FLAG_HF_M04_CONTINUE_ONLY_INDEPENDENT_SAFE_HF_M05`; verify_final=`HF_M05_JOB_SCHEDULING_NO_PASS_YET`.

## NEXT
Cola 1×1: inspeccionar `6aa3781121047bf1b0374a5c`; exigir `COMPLETED` + `RIU_HF_M05_OK=True` + clase/parámetros/CUDA/log/URL antes de promover HF-M05 compute. P02/P03 siguen PENDING.