# RECOVERY PATCH — ROUTER INTELIGENTE UNIVERSAL
Contrato: `tel.workflow/v3` · `FAIL_CLOSED_LOOP` · FAST-CLOSE.

## Estado RIU-0052
- P01 ACTIVE 99%; P02/P03 pendientes.
- M20 real inference PASS: Job `6aa3a3cd5527934177ec4e7e` COMPLETED, exact model_id, response `OK`, vLLM fingerprint, SHA `5c45711905d5c34282a4711527ced24ede31e3390bf318285a01e8d78acf5302`, `HF_M20_OK=True`.
- M09 Job `6aa3a3dd5527934177ec4e80` y M17/M18 Job `6aa3a24f5527934177ec4e3c` siguen pendientes de estado terminal.
- M08/M13/M14/M15/M16/M19 conservan FLAGS exactos para flavor/formato/provider actual; M04 conserva FLAG.

## Boot
1. Releer fuentes.
2. Resolver estado terminal M09/M17/M18 y persistir individualmente.
3. Cerrar P01 ejecutable; entrar P02 sólo bloqueantes y luego P03 API Key Manager+E2E.
Cierre global = 100% PASS ejecutable + FLAGS externos explícitos.