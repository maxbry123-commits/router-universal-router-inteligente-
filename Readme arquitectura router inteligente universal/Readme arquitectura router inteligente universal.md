# Router Inteligente Universal — Arquitectura y estado de integración

Contrato operativo: `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP`.

## 1. Objetivo
Backend Python 95% determinista / 5% LLM. Flujo: `INPUT -> classifier -> DAG fija -> validator/Enchufe Gate -> Router/RedUniversal -> conector -> destino -> verify/state`.

## 2. Plan autorizado — solo 3 pasos
1. Hugging Face + modelos + FastAPI — ACTIVE.
2. Integración GitHub/C01-C23 — PENDING tras P01.
3. API keys agentes + E2E — PENDING.

## 3. Estado P01 — RIU-0041
- Catálogo público 20 certificado.
- HF-M01 config/tokenizer/generation + inferencia local real verificados.
- FastAPI delega a `router_hot_path.py`, que reutiliza Enchufe Gate + RedUniversal; Job `6aa297195527934177ec0aed` ejecutó `2 passed`.
- Dataset/storage RO binding HF-M01 verificado con `HuggingFaceH4/ultrachat_200k` en Job `6aa2983921047bf1b03725eb`; 10 archivos montados y manifest SHA256 `241f6f1a9ac692d9bb2c1556e2be369c15d6a53401256749d34f3e1a6fc0b640`.
- Provider hosted autenticado HF-M01 todavía NO PASS: Job `6aa2985921047bf1b03725ed` alcanzó el endpoint HF y recibió 403 por permisos insuficientes; secreto permaneció redactado.
- HF-M02 `openai-community/gpt2` compute local real verificado por HF Job `6aa2a4f25527934177ec0e01`: COMPLETED, `GPT2LMHeadModel`, CPU, 124439808 parámetros runtime y generación real. HF-M02 sigue NO READY: adapter/dataset-storage/FastAPI pendientes.

HF-M01 sigue NO READY por `FLAG-HF-PROVIDER-AUTH-001`. HF-M02 sigue NO READY por integración incompleta. La cola P01 puede continuar trabajo independiente seguro sin falsificar provider auth.

## 4. Reglas
No 20 servidores FastAPI; gateway único y adapters separados. No monolito. P02 `REUSE > PATCH > ADAPT > GENERATE`. Descarga/copia/movimiento solo motores canónicos autorizados.

## 5. Cierre
`compute != READY`; `dataset mount != output bucket`; `token presente != permiso inference`; `hot-path determinista != provider autenticado`; solo `VERIFIED_CLOSED` tras P03 E2E real.