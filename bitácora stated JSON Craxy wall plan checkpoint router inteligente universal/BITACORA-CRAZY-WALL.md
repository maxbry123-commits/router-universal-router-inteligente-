# BITÁCORA CRAZY WALL — ROUTER INTELIGENTE UNIVERSAL

**Contrato:** `tel.workflow/v3`
**Modo:** `FAIL_CLOSED_LOOP`

## RIU-0001..0041
Trazabilidad previa preservada: catálogo 20, HF-M01 compute/hot-path/dataset RO, FLAG provider-auth 403, HF-M02 compute real.

## RIU-0042 — HF-M02 DATASET + FASTAPI + ENCHUFE + ROUTER
Fuentes de verdad releídas antes del delta. Investigación oficial HF confirmó Jobs como cómputo real, datasets/model repos montados RO y Storage Buckets RW persistentes.
HF Job `6aa2cf4f21047bf1b0372e67`, `cpu-upgrade`, terminó `COMPLETED` el 2026-09-10T15:49:19Z.
Read-back logs: `REPO_ZIP_SHA256 033a19f379e56f3a23bcad488af9089bc6f9a2e1fae25df6dd17a06bee8412df`; `DATASET_MOUNT True FILES 16`; `HTTP_STATUS 200`; `FASTAPI_ENCHUFE_ROUTER_M02_OK True`; `MODEL_CLASS GPT2LMHeadModel`; `PARAMS 124439808`.
Decisión: dataset mount + gateway FastAPI + Enchufe + Router + adapter para HF-M02 PASS. Persistencia RW/output bucket todavía NO PASS, por lo que HF-M02 permanece NO READY.
GAP nuevo: `GAP-HF-M02-RW-STORAGE-001=PERSISTENT_RW_STORAGE_NOT_YET_CERTIFIED`.
3 refutaciones: HTTP 200 != storage RW persistente; dataset mount != output bucket; progreso HF-M02 no resuelve provider-auth HF-M01.
Council12 PASS; cross-check PASS; CODA `PERSIST_HF_M02_INTEGRATION_KEEP_NO_READY_UNTIL_RW_STORAGE`; verify_final=`PASS_HF_M02_INTEGRATED_HOT_PATH_STORAGE_RW_PENDING`.

## NEXT
Cola 1×1: certificar Storage Bucket/output RW persistente HF-M02. Si boundary externo impide hacerlo, registrar FLAG/GAP y continuar sólo trabajo P01 independiente seguro.