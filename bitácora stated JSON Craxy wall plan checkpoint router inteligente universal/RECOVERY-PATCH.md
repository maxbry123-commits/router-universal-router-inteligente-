# RECOVERY PATCH — ROUTER INTELIGENTE UNIVERSAL

Contrato: `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP`.

## Estado válido RIU-0046
- P01 ACTIVE; P02/P03 PENDING.
- HF-M01 compute/hot-path/dataset RO PASS; provider auth 403 sigue FLAG; NO READY.
- HF-M02 compute + integración real PASS; storage RW 403 sigue FLAG; NO READY.
- HF-M03 compute + integración FastAPI→Enchufe→Router→adapter + dataset RO PASS; storage RW persistente sigue sin certificarse; NO READY.
- HF-M04 `unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF`: Job `6aa316585527934177ec29ee` cancelado tras anomalía `RUNNING` más allá de `timeout_seconds=1800`, sin salida final. Retry `6aa34d825527934177ec3d2c` lanzado con timeout explícito 2h/7200s; estado inicial SCHEDULING; NO PASS.

## Boot
1. Releer fuentes de verdad.
2. Cola 1×1: inspeccionar retry HF-M04 y exigir `COMPLETED` + inferencia final verificable.
3. Si PASS, integrar adapter + dataset/storage + FastAPI/Enchufe; si GAP, registrar y aplicar StrategyDelta distinto.
4. Tras P01, P02 y luego P03; no agregar fases.

Cierre solo con ruta+SHA/diff+read-back+test/log+URL. Estado `ACTIVE_LOOP`.