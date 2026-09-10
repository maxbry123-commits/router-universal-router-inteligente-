# Handoff Router Inteligente Universal

## Estado ejecutivo
`tel.workflow/v3` / `FAIL_CLOSED_LOOP` / `ACTIVE_LOOP`.

## Arquitectura
Entrada -> DAG fija -> Enchufe Gate -> RedUniversal -> adapter/conector -> verifier.

## RIU-0041
- HF-M01 compute real: PASS.
- HF-M01 Enchufe/RedUniversal hot-path determinista: Job `6aa297195527934177ec0aed` COMPLETED, `2 passed`.
- Dataset/storage RO HF-M01: `HuggingFaceH4/ultrachat_200k` montado en Job `6aa2983921047bf1b03725eb`; binding OK; manifest SHA256 `241f6f1a9ac692d9bb2c1556e2be369c15d6a53401256749d34f3e1a6fc0b640`.
- Provider auth HF-M01: Job `6aa2985921047bf1b03725ed` ERROR 403, permiso Inference Providers insuficiente; secreto redactado; HF-M01 NO READY.
- HF-M02 `openai-community/gpt2`: Job `6aa2a4f25527934177ec0e01` COMPLETED en `cpu-upgrade`; GPT2LMHeadModel, CPU, 124439808 parámetros runtime, generación real; compute PASS únicamente; HF-M02 NO READY.

## GAP/FLAG
`FLAG-HF-PROVIDER-AUTH-001` abierto. Adapter/dataset-storage/FastAPI de HF-M02 pendientes. No declarar bucket RW persistente sin evidencia.

## Plan único
1. P01 ACTIVE — cola 1×1 HF-M02 dataset/storage + adapter/FastAPI como trabajo independiente seguro; mantener FLAG HF-M01; después HF-M03..20.
2. P02 PENDING — C01-C23.
3. P03 PENDING — API Key Manager + E2E.

Exigir ruta+SHA/read-back+test/log+URL.