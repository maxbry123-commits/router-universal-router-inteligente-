# BITÁCORA CRAZY WALL — ROUTER INTELIGENTE UNIVERSAL

**Contrato:** `tel.workflow/v3`
**Modo:** `FAIL_CLOSED_LOOP`

## RIU-0001..0033 — TRAZABILIDAD PREVIA
Baseline, componentes, Handoff, plan 3 pasos, HF, Gate/conectores v6/registry/validator/schema/RedUniversal, auditorías y HF Jobs compute real preservados por commits/STATE/CHECKPOINT previos.

## RIU-0034 — CATÁLOGO PÚBLICO 20 MODELOS HF
INPUT: cerrar primero Hugging Face con 20 modelos reales, sin inventar IDs; Jobs como cómputo real; cola 1×1.

Attempt A: Job `6aa251005527934177ebfaa6` falló por dependencia ausente (`ModuleNotFoundError: huggingface_hub`). No PASS.
StrategyDelta B: usar metadata PEP 723 dentro del script UV. Job `6aa2510f21047bf1b0371aec` enumeró 20 modelos text-generation reales.
StrategyDelta C: filtrar `private=False`, `gated=False`, `library=transformers` y excluir repos de testing. Job `6aa2512c21047bf1b0371af0` → `COUNT 20`.
Read-back final: Job `6aa2513d5527934177ebfaad` → `FIRST=Qwen/Qwen3-0.6B`, `ALL=` 20 IDs completos, `COUNT=20`. URL https://huggingface.co/jobs/COMAND-CENTER-1/6aa2513d5527934177ebfaad

Decisión: inventario público de 20 modelos queda `CATALOG_OBSERVED`; no `READY`. `GAP-HF-CATALOG-001` se reduce exclusivamente al catálogo privado del owner, ya que Jobs no recibe `HF_TOKEN` implícito.

Persistencia: índice modelos commit `49962acfc50aa9b84e88410693a66d3858ea110c`; STATE/CHECKPOINT/PLAN/RECOVERY/README arquitectura sincronizados en este delta.

Refutaciones: 20 IDs ≠ 20 adapters; modelo público ≠ runtime servido; catálogo ≠ FastAPI hot path. Council12 PASS; cross-check PASS; CODA `REGISTER_OBSERVED_ONLY_THEN_VALIDATE_1X1`; `verify_final=PASS_CATALOG_ONLY_ADAPTERS_PENDING`.

## NEXT
P01 continúa `HF-M01 Qwen/Qwen3-0.6B`: metadata/processor → compute/acelerador → dataset/storage → adapter → FastAPI → llamada real/read-back. Después repetir 1×1 hasta HF-M20; luego P02 y P03.
