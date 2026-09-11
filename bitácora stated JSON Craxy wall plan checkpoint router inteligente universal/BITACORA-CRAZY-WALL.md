# BITÁCORA CRAZY WALL — ROUTER INTELIGENTE UNIVERSAL

**Contrato:** `tel.workflow/v3`
**Modo:** `FAIL_CLOSED_LOOP`

## RIU-0001..0048
Trazabilidad previa preservada: catálogo 20; HF-M01 compute/hot-path/dataset RO + FLAG provider-auth 403; HF-M02 compute/integración + FLAG storage RW 403; HF-M03 compute GPU + integración FastAPI→Enchufe→Router→adapter + dataset RO PASS; storage RW PENDING; HF-M04 FLAG por anomalía timeout-state; HF-M05 compute GPU PASS.

## RIU-0049 — HF-M05 INTEGRATION PASS
Fuentes de verdad releídas antes del delta. Investigación oficial Hugging Face confirmó Jobs/UV, PEP-723, mounts de datasets RO y buckets RW.
Primer intento `6aa3975221047bf1b0374e84` ERROR por dependencia externa no instalada (`ModuleNotFoundError: fastapi`); no se promovió.
StrategyDelta materialmente distinto: dependencias PEP-723 embebidas. Job `6aa3977e21047bf1b0374e94` COMPLETED en `a10g-small`.
Evidencia: `Qwen/Qwen2.5-7B-Instruct`; `RIU_HF_M05_HTTP_STATUS=200`; dataset `/data` mount=True con 10 archivos; CUDA=True; `RIU_HF_M05_ROUTE_VERIFIED=True`; respuesta exacta `RIU_HF_M05_ROUTE_OK`; evidence path `/tmp/riu_hf_m05_integration_evidence.json`; SHA256 `d3352d066152f07379352c94eaae94dd415be1adcda68b43791f8736c9653e79`; read-back=True; `FASTAPI_ENCHUFE_ROUTER_M05_OK=True`.
Decisión fail-closed: certificar M05 adapter+dataset RO+FastAPI→Enchufe→Router hot-path. Persistencia RW permanece boundary externo no bloqueante del core y se registra como GAP, sin inventar bucket/credencial.
3 refutaciones PASS: ERROR inicial no prueba integración; HTTP 200 sin route/model/dataset/SHA no bastaría; storage efímero/read-back no equivale bucket RW persistente.
Council12 PASS; cross-check PASS; CODA `ADVANCE_COMPATIBLE_BATCH_M06_M12_WITH_EXTERNAL_STORAGE_BOUNDARY`; verify_final=`PASS_HF_M05_INTEGRATED_HOT_PATH`.

## NEXT
Lote compatible P01: M06/M07/M10/M11/M12 en una corrida HF Job, persistiendo resultado individual; grandes/gated se FLAG y continúan. P02/P03 permanecen PENDING.