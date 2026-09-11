# Handoff Router Inteligente Universal

## Estado ejecutivo
`tel.workflow/v3` / `FAIL_CLOSED_LOOP` / `ACTIVE_LOOP` / FAST-CLOSE.

## Arquitectura
Entrada -> DAG fija -> Enchufe Gate -> RedUniversal -> adapter/conector -> verifier.

## RIU-0049
- HF-M01/M02/M03 conservan PASS internos ya certificados; auth/provider/RW storage externos quedan FLAGS/GAP, sin bloquear core.
- HF-M04 mantiene `FLAG-HF-M04-COMPUTE-001` tras dos timeout-state anomalies; no repetir otra ventana larga.
- HF-M05 `Qwen/Qwen2.5-7B-Instruct`: compute PASS + integración real PASS. Job `6aa3977e21047bf1b0374e94` COMPLETED; HTTP 200; dataset RO `/data` True/10 files; CUDA True; response `RIU_HF_M05_ROUTE_OK`; evidence SHA256 `d3352d066152f07379352c94eaae94dd415be1adcda68b43791f8736c9653e79`; read-back True; `FASTAPI_ENCHUFE_ROUTER_M05_OK=True`. Persistent RW storage remains external GAP.

## Plan único
1. P01 ACTIVE — lote compatible M06/M07/M10/M11/M12 en una corrida HF Job con persistencia individual; después M08/M09/M13-M20 por compatibilidad o FLAG exacto.
2. P02 PENDING — cerrar sólo GAPs C01-C23 que bloqueen hot-path real.
3. P03 PENDING — API Key Manager hasta 100 slots + E2E real.

Cierre global = 100% PASS de lo ejecutable + FLAGS externos explícitos; exigir ruta+SHA/read-back+test/log+URL.