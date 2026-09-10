# RECOVERY PATCH — ROUTER INTELIGENTE UNIVERSAL

Contrato: `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP`.

## Estado válido RIU-0040
- P01 ACTIVE; P02/P03 PENDING.
- HF-M01 compute real y hot-path Enchufe/RedUniversal determinista verificados.
- Dataset/storage RO binding verificado en HF Job `6aa2983921047bf1b03725eb` con `HuggingFaceH4/ultrachat_200k`; manifest SHA256 `241f6f1a9ac692d9bb2c1556e2be369c15d6a53401256749d34f3e1a6fc0b640`.
- Provider auth Job `6aa2985921047bf1b03725ed` alcanzó `router.huggingface.co/v1/chat/completions` y falló 403 por permisos insuficientes; secreto redactado.
- `FLAG-HF-PROVIDER-AUTH-001` abierto. HF-M01 NO READY.
- Auditoría RIU-0040: commit `dbcd504acc500e31d36abcddaf103434d87866e9`.

## Boot
1. Releer fuentes de verdad.
2. Resolver permiso autorizado de Inference Providers sin exponer credencial.
3. Si continúa FLAG, ejecutar solo validación P01 independiente segura; no promover HF-M01.
4. Tras HF-M01 READY continuar HF-M02..20, luego P02, luego P03.

Cierre solo con ruta+SHA/read-back+test/log+URL. Estado `ACTIVE_LOOP`.