# RECOVERY PATCH — ROUTER INTELIGENTE UNIVERSAL

Contrato: `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP`.

## Estado válido RIU-0047
- P01 ACTIVE; P02/P03 PENDING.
- HF-M01 compute/hot-path/dataset RO PASS; provider auth 403 sigue FLAG; NO READY.
- HF-M02 compute + integración real PASS; storage RW 403 sigue FLAG; NO READY.
- HF-M03 compute + integración FastAPI→Enchufe→Router→adapter + dataset RO PASS; storage RW persistente sigue sin certificarse; NO READY.
- HF-M04: dos Jobs cancelados tras anomalía timeout-state repetida sin salida final (`6aa316585527934177ec29ee`, `6aa34d825527934177ec3d2c`); `FLAG-HF-M04-COMPUTE-001`; NO PASS.
- HF-M05 `Qwen/Qwen2.5-7B-Instruct`: Hub metadata verificada; Job real `6aa3781121047bf1b0374a5c` lanzado a10g-small/Transformers, timeout 30m; estado inicial SCHEDULING; NO PASS.

## Boot
1. Releer fuentes de verdad.
2. Cola 1×1: inspeccionar HF-M05 y exigir `COMPLETED` + `RIU_HF_M05_OK=True` + clase/parámetros/CUDA/log/URL.
3. Si PASS, integrar adapter + dataset/storage + FastAPI/Enchufe; si GAP, registrar y aplicar StrategyDelta distinto.
4. HF-M04 queda FLAG y sólo se continúa trabajo P01 independiente seguro; después P02 y P03, sin fases nuevas.

Cierre solo con ruta+SHA/diff+read-back+test/log+URL. Estado `ACTIVE_LOOP`.