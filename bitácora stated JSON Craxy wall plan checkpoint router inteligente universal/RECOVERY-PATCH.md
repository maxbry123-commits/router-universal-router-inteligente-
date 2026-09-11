# RECOVERY PATCH — ROUTER INTELIGENTE UNIVERSAL

Contrato: `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP` · FAST-CLOSE.

## Estado válido RIU-0051
- P01 ACTIVE en 99%; P02/P03 pendientes.
- HF-M01/M02/M03 preservados; auth/provider/RW externos siguen FLAGS/GAP.
- HF-M04 `FLAG-HF-M04-COMPUTE-001`; no otra ventana larga.
- HF-M05 integración PASS; HF-M06/M07/M10/M11/M12 batch PASS.
- M08/M13/M14/M15/M16/M19: FLAGS exactos contra `a10g-small`/formato observado o provider no autorizado; no equivalen a imposibilidad global.
- M17/M18: initial `6aa3a1875527934177ec4e06` exit127; probe confirmó `/app/llama-cli`; retry `6aa3a24f5527934177ec4e3c` lanzado.
- M09/M20: candidatos locales pendientes de runtime vLLM corregido; smoke `6aa3a15c5527934177ec4e04` falló por executable path y probe `6aa3a2cb5527934177ec4e50` fue lanzado.

## Boot
1. Releer fuentes de verdad.
2. Inspeccionar M17/M18 retry y persistir resultado individual.
3. Resolver runtime M09/M20 y ejecutar con timeout corto; FLAG exacto si el runtime autorizado no cierra.
4. Tras cerrar P01 ejecutable, entrar P02 sólo GAPs bloqueantes y luego P03 API Key Manager+E2E.

Cierre global: 100% PASS de lo ejecutable + FLAGS externos explícitos; no bloquear core por proveedor externo probado.