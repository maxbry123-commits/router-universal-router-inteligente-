# PLAN DE TAREAS — ROUTER INTELIGENTE UNIVERSAL
Contrato: `tel.workflow/v3` · `FAIL_CLOSED_LOOP` · FAST-CLOSE.
1. **Paso 1 — Hugging Face** — CLOSED_EXECUTABLE_SET.
   - ✅ M05, M06/M07/M10/M11/M12, M20 verified.
   - ⚑ M09 compute real verified but `content=null`/reasoning-only response contract flagged; M17 timeout; M18 not reached in sequential GGUF job; M04 and large/provider/storage external flags preserved.
2. **Paso 2 — C01-C23** — ACTIVE: inspect and close only blockers of real hot-path/E2E; undefined nonblockers remain documented GAP.
3. **Paso 3 — API Key Manager + E2E** — PENDING: up to 100 slots, hash-only, revoke/rotate, real agent→key→FastAPI→Enchufe→Router→adapter→destination→verifier.
Cierre global = PASS ejecutable + explicit external FLAGS + final P03 E2E.