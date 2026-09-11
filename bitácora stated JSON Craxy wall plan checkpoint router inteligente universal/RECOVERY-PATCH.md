# RECOVERY PATCH — ROUTER INTELIGENTE UNIVERSAL

Contrato: `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP` · FAST-CLOSE.

## Estado válido RIU-0049
- P01 ACTIVE; P02/P03 PENDING.
- HF-M01/M02/M03 mantienen PASS internos ya certificados y boundaries externos auth/storage documentados.
- HF-M04 mantiene `FLAG-HF-M04-COMPUTE-001` tras dos anomalías timeout-state; no consumir otra ventana larga sin StrategyDelta corto/materialmente distinto.
- HF-M05 `Qwen/Qwen2.5-7B-Instruct`: compute PASS previo + integración real PASS en Job `6aa3977e21047bf1b0374e94`; HTTP 200; dataset `/data` mount True/10 files; CUDA True; route verified; respuesta `RIU_HF_M05_ROUTE_OK`; evidence `/tmp/riu_hf_m05_integration_evidence.json`; SHA256 `d3352d066152f07379352c94eaae94dd415be1adcda68b43791f8736c9653e79`; read-back True; `FASTAPI_ENCHUFE_ROUTER_M05_OK=True`.
- Persistencia RW HF-M05 no certificada por falta de ruta/bucket autorizado; queda GAP externo y no invalida el hot-path.

## Boot
1. Releer fuentes de verdad.
2. Ejecutar lote compatible M06/M07/M10/M11/M12 en un HF Job; persistir resultado individual.
3. Para M08/M09/M13-M20: ejecutar sólo flavor/tamaño compatible; si no, registrar FLAG exacto y continuar.
4. Después cerrar únicamente C01-C23 bloqueantes del hot-path y P03 API Key Manager+E2E.

Cierre global: PASS de lo ejecutable + lista explícita de FLAGS externos; no bloquear core por proveedor externo probado.