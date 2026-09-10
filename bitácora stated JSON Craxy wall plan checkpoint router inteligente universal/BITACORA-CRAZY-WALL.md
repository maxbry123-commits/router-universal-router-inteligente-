# BITÁCORA CRAZY WALL — ROUTER INTELIGENTE UNIVERSAL

**Contrato:** `tel.workflow/v3`
**Modo:** `FAIL_CLOSED_LOOP`

## RIU-0001..0035 — TRAZABILIDAD PREVIA
Baseline, componentes, Handoff, plan 3 pasos, HF, Gate/conectores v6/registry/validator/schema/RedUniversal, auditorías, catálogo público 20 y reconciliación del registry quedan preservados por commits/STATE/CHECKPOINT previos.

## RIU-0036 — HF-M01 CONFIG/TOKENIZER/GENERATION EN CÓMPUTO REAL
INPUT literal: continuar P01 1×1 sin promover READY por metadata; HF Jobs como cómputo real.

HF Job `6aa26cc321047bf1b0371f28` (`cpu-upgrade`) → `COMPLETED`. URL https://huggingface.co/jobs/COMAND-CENTER-1/6aa26cc321047bf1b0371f28

Read-back real desde Hub dentro del Job:
- `model_id=Qwen/Qwen3-0.6B`
- `pipeline=text-generation`, `library=transformers`
- `Qwen3ForCausalLM`, `model_type=qwen3`, `torch_dtype=bfloat16`
- `max_position_embeddings=40960`
- safetensors `751632384` parámetros BF16
- `config.json`, `tokenizer_config.json`, `generation_config.json` descargados y leídos
- provider observado: `featherless-ai`, status `live`, task `conversational`

Decision: HF-M01 avanza a `CONFIG_TOKENIZER_VALIDATED`, pero NO READY. Faltan serving compute/acelerador, dataset/storage, adapter, registro FastAPI y llamada real por Enchufe/Router.

3 refutaciones: config/tokenizer ≠ inferencia; provider live ≠ hot path Router; cpu-upgrade para auditoría ≠ acelerador final de serving. Council12 PASS; cross-check PASS; CODA `KEEP_HF_M01_NOT_READY_UNTIL_SERVING`; `verify_final=PASS_CONFIGURATION_ONLY_SERVING_PENDING`.

## NEXT
Cola 1×1: HF-M01 serving compute/acelerador → dataset/storage → adapter → FastAPI → llamada real/read-back. Solo entonces HF-M02.
