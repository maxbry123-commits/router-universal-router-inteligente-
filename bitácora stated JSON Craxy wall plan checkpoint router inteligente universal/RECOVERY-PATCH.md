# RECOVERY PATCH — ROUTER INTELIGENTE UNIVERSAL

Contrato: `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP` · FAST-CLOSE.

## Estado válido RIU-0050
- P01 ACTIVE en 99%; P02/P03 pendientes.
- HF-M01/M02/M03: PASS internos preservados; auth/provider/RW externos siguen FLAGS/GAP explícitos.
- HF-M04 mantiene `FLAG-HF-M04-COMPUTE-001`; no consumir otra ventana larga.
- HF-M05 integración real PASS.
- HF-M06/M07/M10/M11/M12: Job `6aa398fe5527934177ec4cd0` COMPLETED; cada modelo pasó verifier individual detrás de FastAPI→Enchufe→Router→HFAdapter; dataset RO mount True/10 files; summary `/tmp/riu_hf_batch_m06_m12_summary.json`; SHA256 `c3b38014bdd5423cd85b42f14d54fc13c95247a0aa29e3729eb3ac84264dd6a5`; read-back True; `RIU_HF_BATCH_M06_M12_OK=True`.
- M06 SHA individual `e5820de1040e58a84591fd48a3f8a1fbf256090b03ba082a7f0f9e9b30a04d01`; M12 SHA individual `640448abf630b2c7df1e70fc8849d72dcb84096bf47d9c124dc746c51026b2ab`.

## Boot
1. Releer fuentes de verdad.
2. Clasificar M08/M09/M13-M20 por tamaño/flavor/scope.
3. Ejecutar compatibles; no ejecutables/gated/provider-only reciben FLAG exacto y se continúa.
4. Tras cerrar P01 ejecutable, entrar P02 sólo GAPs bloqueantes y luego P03 API Key Manager+E2E.

Cierre global: 100% PASS de lo ejecutable + FLAGS externos explícitos; no bloquear core por proveedor externo probado.