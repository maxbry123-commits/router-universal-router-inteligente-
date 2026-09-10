# RECOVERY PATCH — ROUTER INTELIGENTE UNIVERSAL

Contrato: `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP`.

## Estado válido
- Plan limitado a 3 pasos.
- Paso 1 ACTIVE: HF Jobs compute real operativo.
- Inventario público 20: Job `6aa2513d5527934177ebfaad` → COUNT=20.
- HF-M01 `Qwen/Qwen3-0.6B`: Job `6aa26cc321047bf1b0371f28` → COMPLETED; validó `Qwen3ForCausalLM`, `qwen3`, BF16, `751632384` parámetros y read-back de config/tokenizer/generation; provider observado `featherless-ai` live conversational.
- HF-M01 sigue NO READY: faltan serving compute/acelerador, dataset/storage, adapter, registro FastAPI y llamada real del Router.
- GAP-HF-CATALOG-001 queda reducido al catálogo privado por boundary de `HF_TOKEN`.
- Paso 2 PENDING tras P01. Paso 3 PENDING.

## Boot de recuperación
1. Leer STATE/CHECKPOINT/PLAN/BITACORA/README arquitectura/Handoff/PARCHE.
2. Continuar `P01_HF_M01_SERVING_VALIDATION`.
3. Cerrar HF-M01: serving compute/acelerador → dataset/storage → adapter → FastAPI → llamada real/read-back.
4. Repetir 1×1 HF-M02..HF-M20.
5. Si aparece GAP, investigar y aplicar StrategyDelta materialmente distinto; no promover READY por presencia.
6. Tras cerrar 20, ejecutar P02 C01-C23 con `REUSE > PATCH > ADAPT > GENERATE` y Enchufe Universal.
7. Solo después ejecutar P03 API Key Manager + E2E real.

## Cierre
Exigir `ruta + diff/SHA + read-back + test/log + URL`. Estado `ACTIVE_LOOP`.
