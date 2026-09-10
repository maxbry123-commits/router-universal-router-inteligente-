# BITÁCORA CRAZY WALL — ROUTER INTELIGENTE UNIVERSAL

**Contrato:** `tel.workflow/v3`
**Modo:** `FAIL_CLOSED_LOOP`

## RIU-0001..0042
Trazabilidad previa preservada: catálogo 20, HF-M01 compute/hot-path/dataset RO, FLAG provider-auth 403, HF-M02 compute real e integración FastAPI→Enchufe→Router→adapter con dataset RO.

## RIU-0043 — HF-M02 STORAGE RW AUTH BOUNDARY
Fuentes de verdad releídas antes del delta. Investigación oficial HF confirmó que Storage Buckets son RW por defecto en Jobs y que persistencia exige comprobar que el output realmente aterrizó después de terminar el Job.
StrategyDelta 1: intento de montar `COMAND-CENTER-1/jobs-artifacts` como bucket gestionado; API devolvió 404, por lo que no se declaró existencia ni PASS.
StrategyDelta 2: HF Job `6aa2ebc15527934177ec1eb6`, `cpu-basic`, secreto `HF_TOKEN` pasado por mecanismo protegido sin imprimirlo, intentó `create_bucket('riu-router-storage', private=True, exist_ok=True)`.
Resultado final: `ERROR`; HTTP 403 `read access but not required permissions`; bucket create/write no autorizado por la credencial disponible. No se expuso secreto.
Decisión: registrar `FLAG-HF-M02-RW-STORAGE-AUTH-001`; mantener `GAP-HF-M02-RW-STORAGE-001`; HF-M02 continúa NO READY. Boundary externo permite continuar sólo trabajo P01 independiente seguro.
3 refutaciones: Job ERROR != storage PASS; token disponible != permiso write; hot-path previo != persistencia RW.
Council12 PASS; cross-check PASS; CODA `PERSIST_STORAGE_AUTH_FLAG_CONTINUE_ONLY_SAFE_P01_HF_M03`; verify_final=`PASS_FLAGGED_EXTERNAL_BOUNDARY_NO_STORAGE_READY`.

## NEXT
Cola 1×1: HF-M03 `Qwen/Qwen3-8B` real compute en HF Jobs. Mantener FLAGs HF-M01/HF-M02 abiertos; no iniciar P02/P03.