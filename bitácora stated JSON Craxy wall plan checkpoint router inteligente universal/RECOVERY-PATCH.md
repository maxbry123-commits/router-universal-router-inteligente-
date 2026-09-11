# RECOVERY PATCH — ROUTER INTELIGENTE UNIVERSAL
Contrato: `tel.workflow/v3` · `FAIL_CLOSED_LOOP` · FAST-CLOSE.

## Estado RIU-0053
- P01 `CLOSED_EXECUTABLE_SET`; P02 ACTIVE; P03 PENDING.
- M20 PASS real; M09 compute real COMPLETED but response `content=null`/reasoning-only -> exact response-contract FLAG.
- M17/M18 GGUF retry `6aa3a24f5527934177ec4e3c` exceeded short timeout and was CANCELED; no further long window.
- M04/large-model/provider/RW-storage boundaries remain explicit FLAGS/GAP and do not block core close.

## Boot
1. Releer fuentes.
2. P02 inspect physical repo hot-path and patch only blocking C01-C23 with REUSE>PATCH>ADAPT>GENERATE.
3. Leave undefined nonblocking contracts documented.
4. Enter P03 API Key Manager + real E2E.
Cierre global requires P03 real E2E plus explicit external FLAGS.