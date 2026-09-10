# RECOVERY PATCH — ROUTER INTELIGENTE UNIVERSAL

Contrato: `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP`.

## Estado válido
- Plan limitado a 3 pasos.
- Paso 1 ACTIVE: HF Jobs compute real operativo.
- RIU-0034: Job `6aa2513d5527934177ebfaad` devolvió `COUNT=20` de modelos públicos, no gated, `transformers`, `text-generation`; índice persistido en commit `49962acfc50aa9b84e88410693a66d3858ea110c`.
- Los 20 están solo `CATALOG_OBSERVED`; ningún modelo se considera READY sin adapter/compute/dataset/FastAPI/llamada real.
- GAP-HF-CATALOG-001 queda reducido al catálogo privado de `COMAND-CENTER-1` por boundary de `HF_TOKEN`.
- Paso 2 PENDING tras P01. Paso 3 PENDING.

## Boot de recuperación
1. Leer STATE/CHECKPOINT/PLAN/BITACORA/README arquitectura/Handoff.
2. Continuar `P01_HF_VALIDATE_20` desde `HF-M01 Qwen/Qwen3-0.6B`.
3. Validar 1×1: metadata/processor → compute/acelerador → dataset/storage → adapter → FastAPI → llamada real/read-back.
4. Si aparece GAP, investigar y aplicar StrategyDelta materialmente distinto; no promover READY por presencia.
5. Tras cerrar 20, ejecutar P02 C01-C23 con `REUSE > PATCH > ADAPT > GENERATE` y Enchufe Universal.
6. Solo después ejecutar P03 API Key Manager + E2E real.

## Cierre
Exigir `ruta + diff/SHA + read-back + test/log + URL`. Estado `ACTIVE_LOOP`.
