# RIU-0040 — HF-M01 dataset/storage + provider auth boundary

Contrato: `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP`.

## INPUT / cola 1×1
Continuar P01 sobre HF-M01 `Qwen/Qwen3-0.6B`. Prioridades: (1) cerrar dataset/storage binding en HF Jobs; (2) probar provider hosted autenticado usando secreto autorizado sin exponerlo.

## Investigación previa
- Dataset real verificado: `HuggingFaceH4/ultrachat_200k`, licencia MIT, task `text-generation`, formato parquet, 100K<n<1M.
- HF Jobs documenta mounts `hf://datasets/...:/mount:ro` y almacenamiento efímero por flavor; Storage Buckets son la vía persistente para outputs.
- HF `InferenceClient.chat_completion` usa token runtime para Inference Providers.

## Ejecución dataset/storage
HF Job `6aa2983921047bf1b03725eb`, flavor `cpu-upgrade`, `COMPLETED`.
Volume: `hf://datasets/HuggingFaceH4/ultrachat_200k:/data:ro`.
URL: https://huggingface.co/jobs/COMAND-CENTER-1/6aa2983921047bf1b03725eb
Read-back:
- `DATASET_MOUNT_EXISTS True`
- `DATASET_FILE_COUNT 10`
- parquet train/test gen+sft observados
- `DATASET_MANIFEST_SHA256 241f6f1a9ac692d9bb2c1556e2be369c15d6a53401256749d34f3e1a6fc0b640`
- `HF_M01_DATASET_STORAGE_BINDING_OK True`

Resultado: dataset remoto/storage read-only binding VERIFIED. Persistencia de outputs a Storage Bucket NO se declara porque no se creó/montó bucket RW en este delta.

## Ejecución provider autenticado
Se usó `secrets={HF_TOKEN:$HF_TOKEN}` del runtime de HF Jobs; el secreto quedó redactado en inspección/logs.
HF Job `6aa2985921047bf1b03725ed`, flavor `cpu-upgrade`, terminó `ERROR`.
URL: https://huggingface.co/jobs/COMAND-CENTER-1/6aa2985921047bf1b03725ed
Respuesta real: HTTP `403 Forbidden` desde `https://router.huggingface.co/v1/chat/completions` con mensaje de que el método de autenticación no tiene permisos suficientes para Inference Providers en nombre de `COMAND-CENTER-1`.

## FLAG
`FLAG-HF-PROVIDER-AUTH-001 = TOKEN_SCOPE_INSUFFICIENT_FOR_INFERENCE_PROVIDERS`.
No se expuso token. No se reintenta con credenciales inventadas ni se crea secreto nuevo.

## 3 refutaciones
1. Mount read-only de dataset no equivale a bucket persistente RW para outputs.
2. Token presente en Job no equivale a permiso de Inference Providers; 403 lo refuta materialmente.
3. Compute local + hot-path determinista + dataset binding no equivalen a HF-M01 READY mientras provider hosted autenticado siga fallando.

Council12: PASS. Cross-check: PASS. CODA: `CLOSE_DATASET_BINDING_REGISTER_PROVIDER_AUTH_FLAG_KEEP_HF_M01_NO_READY`.
verify_final: `PASS_DATASET_BINDING_PROVIDER_AUTH_FLAGGED`.
