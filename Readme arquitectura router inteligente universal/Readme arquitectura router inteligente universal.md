# Router Inteligente Universal — Arquitectura y estado de integración
Contrato: `tel.workflow/v3` · `FAIL_CLOSED_LOOP` · FAST-CLOSE.

## Plan autorizado — sólo 3 pasos
1. Hugging Face — `CLOSED_EXECUTABLE_SET`.
2. GitHub/C01-C23 — ACTIVE, sólo bloqueantes del hot-path/E2E.
3. API Key Manager + E2E — PENDING.

## P01 RIU-0053
M05, M06/M07/M10/M11/M12 y M20 tienen PASS verificables. M09 ejecutó realmente (`6aa3a3dd5527934177ec4e80`, SHA `43a490a128c6a64b845cd2397a881c2e85969d7a15db669a47f0b230f4bb4e68`) pero devolvió `content=null` con reasoning-only, por lo que queda FLAG de contrato. M17/M18 job `6aa3a24f5527934177ec4e3c` fue CANCELED tras superar ventana corta; no PASS. M04/large/provider/RW boundaries continúan FLAGS exactos.

## P02 regla
`REUSE > PATCH > ADAPT > GENERATE`; no reauditar donors cerrados, no materializar contratos no bloqueantes, no monolito. Hot-path objetivo: `FastAPI -> Auth/APIKeyGuard -> Enchufe Gate -> RedUniversal -> adapter -> destination -> verifier`.

## Cierre
`VERIFIED_CLOSED` exige P03 E2E real; FLAGS externos demostrados no retienen artificialmente el core.