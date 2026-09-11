# Handoff Router Inteligente Universal

## Estado ejecutivo
`tel.workflow/v3` / `FAIL_CLOSED_LOOP` / `ACTIVE_LOOP` / FAST-CLOSE / 99%.

## Arquitectura
Entrada -> DAG fija -> Enchufe Gate -> RedUniversal -> adapter/conector -> verifier.

## RIU-0051
- HF-M01/M02/M03 conservan PASS internos; auth/provider/RW storage externos permanecen FLAGS/GAP.
- HF-M04 mantiene `FLAG-HF-M04-COMPUTE-001`; no otra ventana larga.
- HF-M05 integrado PASS; HF-M06/M07/M10/M11/M12 batch integrado PASS.
- M08/M13/M14/M15/M16/M19: FLAG exacto contra `a10g-small` + formato observado/provider autorizado; no es imposibilidad global.
- M17/M18 GGUF: initial `6aa3a1875527934177ec4e06` exit127; `/app/llama-cli` confirmado; retry `6aa3a24f5527934177ec4e3c` en ejecución.
- M09 MXFP4 y M20 AWQ 4-bit siguen candidatos locales; vLLM path probe `6aa3a2cb5527934177ec4e50` en curso.

## Plan único
1. P01 ACTIVE — cerrar M17/M18 y luego M09/M20; FLAGS externos ya explicitados.
2. P02 PENDING — cerrar únicamente GAPs C01-C23 que bloqueen el hot-path real.
3. P03 PENDING — API Key Manager hasta 100 slots + E2E real.

Cierre global = 100% PASS de lo ejecutable + FLAGS externos explícitos; exigir ruta+SHA/read-back+test/log+URL.