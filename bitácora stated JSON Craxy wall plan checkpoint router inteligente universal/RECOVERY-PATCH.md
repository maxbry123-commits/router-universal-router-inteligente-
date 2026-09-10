# RECOVERY PATCH — ROUTER INTELIGENTE UNIVERSAL

Contrato: `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP`.

## Estado válido RIU-0045
- P01 ACTIVE; P02/P03 PENDING.
- HF-M01 compute/hot-path/dataset RO PASS; provider auth 403 sigue `FLAG-HF-PROVIDER-AUTH-001`; NO READY.
- HF-M02 compute + integración real PASS; storage RW bloqueado por `FLAG-HF-M02-RW-STORAGE-AUTH-001`; NO READY.
- HF-M03 `Qwen/Qwen3-8B` compute + integración FastAPI→Enchufe→Router→adapter + dataset RO PASS en Job `6aa2f8e921047bf1b03732b7`: HTTP 200, `RIU_HF_M03_ROUTE_OK`, `Qwen3ForCausalLM`, 8190735360 params, CUDA True; NO READY porque storage RW persistente sigue sin certificarse.

## Boot
1. Releer fuentes de verdad.
2. Cola 1×1: validar HF-M04 compute real; mantener FLAGs HF-M01/HF-M02 y GAP storage HF-M03.
3. Continuar sólo P01 independiente seguro mientras boundaries externos permanezcan abiertos.
4. Tras P01, P02 y luego P03; no agregar fases.

Cierre solo con ruta+SHA/diff+read-back+test/log+URL. Estado `ACTIVE_LOOP`.