# RECOVERY PATCH — ROUTER INTELIGENTE UNIVERSAL

Contrato: `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP`.

## Estado válido RIU-0044
- P01 ACTIVE; P02/P03 PENDING.
- HF-M01 compute/hot-path/dataset RO PASS; provider auth 403 sigue `FLAG-HF-PROVIDER-AUTH-001`; NO READY.
- HF-M02 compute + integración real PASS; storage RW bloqueado por `FLAG-HF-M02-RW-STORAGE-AUTH-001`; NO READY.
- HF-M03 `Qwen/Qwen3-8B` compute real PASS en Job `6aa2ecbb21047bf1b037318e`: `Qwen3ForCausalLM`, 8190735360 parámetros, respuesta `RIU_HF_M03_OK`, `MAX_MEMORY_ALLOCATED=16396255232`; NO READY porque adapter/dataset/storage/FastAPI siguen PENDING.

## Boot
1. Releer fuentes de verdad.
2. Cola 1×1: validar HF-M03 adapter + dataset/storage + FastAPI/Enchufe con Job real; mantener FLAGs HF-M01/HF-M02.
3. Continuar sólo P01 independiente seguro mientras boundaries externos permanezcan abiertos.
4. Tras P01, P02 y luego P03; no agregar fases.

Cierre solo con ruta+SHA/diff+read-back+test/log+URL. Estado `ACTIVE_LOOP`.