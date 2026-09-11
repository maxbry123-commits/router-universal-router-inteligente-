# Handoff Router Inteligente Universal

## Estado ejecutivo
`tel.workflow/v3` / `FAIL_CLOSED_LOOP` / `ACTIVE_LOOP` / FAST-CLOSE / 99%.

## Arquitectura
Entrada -> DAG fija -> Enchufe Gate -> RedUniversal -> adapter/conector -> verifier.

## RIU-0052
- M01-M03 preservados; M04 FLAG; M05 y batch M06/M07/M10/M11/M12 PASS.
- M08/M13/M14/M15/M16/M19 FLAGS exactos para flavor/formato/provider actual.
- M20 `Qwen/Qwen2.5-7B-Instruct-AWQ`: Job `6aa3a3cd5527934177ec4e7e` COMPLETED; vLLM; exact model; response `OK`; SHA `5c45711905d5c34282a4711527ced24ede31e3390bf318285a01e8d78acf5302`; PASS.
- M09 `6aa3a3dd5527934177ec4e80` y M17/M18 `6aa3a24f5527934177ec4e3c` en curso.

## Plan único
1. P01 ACTIVE — finalizar M09/M17/M18 y cerrar ejecutable set.
2. P02 PENDING — sólo C01-C23 bloqueantes del hot-path.
3. P03 PENDING — API Key Manager hasta 100 slots + E2E real.

Cierre global = 100% PASS ejecutable + FLAGS externos explícitos.