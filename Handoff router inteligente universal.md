# Handoff Router Inteligente Universal

## Estado ejecutivo
`tel.workflow/v3` / `FAIL_CLOSED_LOOP` / `ACTIVE_LOOP`.

## Arquitectura
Entrada -> DAG fija -> Enchufe Gate -> RedUniversal -> adapter/conector -> verifier.

## RIU-0040
- HF-M01 compute real: PASS.
- HF-M01 Enchufe/RedUniversal hot-path determinista: Job `6aa297195527934177ec0aed` COMPLETED, `2 passed`.
- Dataset/storage RO: `HuggingFaceH4/ultrachat_200k` montado en Job `6aa2983921047bf1b03725eb`; `HF_M01_DATASET_STORAGE_BINDING_OK True`; manifest SHA256 `241f6f1a9ac692d9bb2c1556e2be369c15d6a53401256749d34f3e1a6fc0b640`.
- Provider auth: Job `6aa2985921047bf1b03725ed` ERROR 403, permiso Inference Providers insuficiente; secreto redactado.
- Auditoría RIU-0040: commit `dbcd504acc500e31d36abcddaf103434d87866e9`.

## GAP/FLAG
`FLAG-HF-PROVIDER-AUTH-001` abierto. HF-M01 NO READY. No declarar bucket RW persistente sin evidencia.

## Plan único
1. P01 ACTIVE — resolver provider auth HF-M01; después HF-M02..20 1×1.
2. P02 PENDING — C01-C23.
3. P03 PENDING — API Key Manager + E2E.

Exigir ruta+SHA/read-back+test/log+URL.