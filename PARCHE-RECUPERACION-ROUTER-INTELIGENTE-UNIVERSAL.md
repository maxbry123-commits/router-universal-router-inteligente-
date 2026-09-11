# PARCHE DE RECUPERACIÓN — ROUTER INTELIGENTE UNIVERSAL

Estado actual: `ACTIVE_LOOP` · contrato `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP` · FAST-CLOSE · 99%.

## Hecho y verificado
- HF Jobs como cómputo real; catálogo público 20 certificado.
- HF-M01/M02/M03 conservan PASS internos; auth/provider/RW-storage externos quedan FLAGS/GAP explícitos.
- HF-M04 mantiene `FLAG-HF-M04-COMPUTE-001`; no otra ventana larga.
- HF-M05 integración real PASS; HF-M06/M07/M10/M11/M12 batch integrado PASS.
- M08/M13/M14/M15/M16/M19: FLAGS exactos contra `a10g-small` y formato observado/provider autorizado; no equivalen a imposibilidad global.
- M17/M18: StrategyDelta aplicado tras exit127; `/app/llama-cli` confirmado y Job `6aa3a24f5527934177ec4e3c` lanzado.
- M09/M20: candidatos locales; vLLM runtime probe `6aa3a2cb5527934177ec4e50` lanzado tras fallo de path del smoke inicial.

## GAP/FLAG
- `GAP-HF-CATALOG-001`: catálogo privado.
- `FLAG-HF-PROVIDER-AUTH-001`: permiso Inference Providers insuficiente.
- storage RW HF-M02/HF-M03/HF-M05: boundary externo no certificado.
- `GAP-HF-M04-TIMEOUT-001` + `FLAG-HF-M04-COMPUTE-001`.
- `GAP-HF-M17-M18-RUNTIME-001`: path binario inicial corregido mediante StrategyDelta.
- `GAP-HF-VLLM-IMAGE-PATH-001`: imagen vLLM requiere entrypoint/path real antes de M09/M20.
- GAP P02 contractuales sólo bloquean si afectan E2E real.

## Lista única
- [x] HF-M05 integración real.
- [x] HF-M06/M07/M10/M11/M12 batch compatible.
- [x] M08/M13/M14/M15/M16/M19 clasificados y FLAG exacto local/external.
- [ ] M17/M18 retry real.
- [ ] M09/M20 runtime compatible.
- [ ] P02 sólo GAPs C01-C23 bloqueantes del hot-path.
- [ ] P03 API Key Manager hasta 100 slots + E2E real.

Cierre: 100% PASS de lo ejecutable + lista explícita de FLAGS externos; no quedarse en 98% por proveedor externo probado.