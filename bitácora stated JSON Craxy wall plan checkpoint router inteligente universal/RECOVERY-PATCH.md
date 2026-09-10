# RECOVERY PATCH — ROUTER INTELIGENTE UNIVERSAL

Contrato: `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP`.

## Estado válido RIU-0041
- P01 ACTIVE; P02/P03 PENDING.
- HF-M01 compute real y hot-path Enchufe/RedUniversal determinista verificados.
- Dataset/storage RO binding HF-M01 verificado en HF Job `6aa2983921047bf1b03725eb` con `HuggingFaceH4/ultrachat_200k`; manifest SHA256 `241f6f1a9ac692d9bb2c1556e2be369c15d6a53401256749d34f3e1a6fc0b640`.
- Provider auth HF-M01 Job `6aa2985921047bf1b03725ed` alcanzó `router.huggingface.co/v1/chat/completions` y falló 403 por permisos insuficientes; secreto redactado; `FLAG-HF-PROVIDER-AUTH-001` abierto; HF-M01 NO READY.
- HF-M02 `openai-community/gpt2` compute local real verificado en Job `6aa2a4f25527934177ec0e01`: COMPLETED, GPT2LMHeadModel, cpu, 124439808 parámetros runtime, generación real; HF-M02 NO READY porque adapter/dataset/FastAPI siguen pendientes.

## Boot
1. Releer fuentes de verdad.
2. Continuar P01 independiente seguro con HF-M02 dataset/storage + adapter/FastAPI; mantener HF-M01 provider-auth FLAG sin falsificar PASS.
3. Ante GAP registrar evidencia y aplicar StrategyDelta materialmente distinto; no promover modelo incompleto.
4. Tras completar P01, continuar P02 y luego P03; no agregar fases.

Cierre solo con ruta+SHA/diff+read-back+test/log+URL. Estado `ACTIVE_LOOP`.