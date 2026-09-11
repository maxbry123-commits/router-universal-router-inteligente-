# PARCHE DE RECUPERACIÓN — ROUTER INTELIGENTE UNIVERSAL

Estado: `ACTIVE_LOOP` · contrato `tel.workflow/v3` · `FAIL_CLOSED_LOOP` · FAST-CLOSE · 99%.

## RIU-0052
- M01-M03 PASS internos preservados; auth/provider/RW externos siguen FLAGS/GAP.
- M04 FLAG sin otra ventana larga; M05 integración PASS; M06/M07/M10/M11/M12 batch PASS.
- M08/M13/M14/M15/M16/M19: FLAGS exactos para `a10g-small`/formato/provider actual.
- M20 `Qwen/Qwen2.5-7B-Instruct-AWQ`: Job `6aa3a3cd5527934177ec4e7e` COMPLETED; exact model; response `OK`; vLLM fingerprint; SHA256 `5c45711905d5c34282a4711527ced24ede31e3390bf318285a01e8d78acf5302`; `HF_M20_OK=True`.
- M09 Job `6aa3a3dd5527934177ec4e80`; M17/M18 Job `6aa3a24f5527934177ec4e3c` siguen en curso.

## Lista única
- [x] M20 real inference.
- [ ] Resolver estado terminal M09/M17/M18, PASS individual o FLAG exacto.
- [ ] P02 únicamente bloqueantes C01-C23.
- [ ] P03 API Key Manager + E2E.

Cierre = 100% PASS de lo ejecutable + FLAGS externos explícitos.