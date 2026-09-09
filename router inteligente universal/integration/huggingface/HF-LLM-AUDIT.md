# HF LLM AUDIT — ROUTER INTELIGENTE UNIVERSAL

Contrato: `tel.workflow/v3` · nodo: `P01_COMPONENTS_AND_HF_LLM_AUDIT` · modo: `FAIL_CLOSED_LOOP`.

## Evidencia confirmada
- Cuenta Hugging Face autenticada en la ejecución: `COMAND-CENTER-1`.
- Scope observado: lectura de repos + Jobs; no se infieren modelos privados no enumerados.
- La operación directa `model_search(author=COMAND-CENTER-1)` sigue fallando con `Tool model_search not found`.
- StrategyDelta ejecutado mediante Hugging Face Jobs + `huggingface_hub.HfApi.list_models(author='COMAND-CENTER-1', full=True)`.
- Job de lectura pública: `https://huggingface.co/jobs/COMAND-CENTER-1/6aa0f30c32d5d0c22c5af586` → `COUNT 0`.
- Job de control de credenciales del contenedor: `https://huggingface.co/jobs/COMAND-CENTER-1/6aa0f328900620b5c77e5534` → `HF_TOKEN=False`, `HUGGING_FACE_HUB_TOKEN=False`, `HUGGINGFACE_TOKEN=False`.
- Conclusión limitada por evidencia: **0 modelos públicos propiedad de `COMAND-CENTER-1` son enumerables desde el Hub público en esta pasada**. Esto NO demuestra ausencia de modelos privados ni de endpoints remotos consumibles por el Router.
- No se inventa ningún `model_id`; adapters por modelo permanecen bloqueados hasta confirmar IDs reales consumibles.

## Reuse local confirmado
- `huggueface/manifest.yml` declara `HF-ROUTER-BRIDGE-V1`, modo `REMOTE_ONLY`, FastAPI/OpenAI-compatible, secretos por entorno y failover `HF1->HF2->HF3->WAITING`.
- `huggueface/bridge/router_hf_bridge.py` ya contiene puente remoto para proveedores OpenAI-compatible (`groq`, `cerebras`, `nvidia`, `openrouter`) con `provider_models()` y `chat()`; por regla `REUSE > PATCH > ADAPT > GENERATE` debe evaluarse antes de crear otro gateway.
- El manifiesto reserva Hugging Face mediante `HF_INFERENCE_ENDPOINT` + `HF_TOKEN`; no se hardcodean endpoints ni tokens.

## Contrato de adapter FastAPI por modelo
Solo se materializa cuando el modelo sea confirmado por evidencia remota:
`model_id -> specialty -> provider/endpoint_ref -> adapter -> health -> FastAPI route -> tests`.

Un modelo confirmado deberá registrar como mínimo:
- `model_id` exacto;
- `revision/commit` si está disponible;
- `task/capability`;
- `endpoint_ref`, nunca token;
- `specialty` autorizada;
- límites/timeout;
- health/sondeo;
- ruta FastAPI común o alias por modelo;
- evidencia de request real antes de `VERIFIED_CLOSED`.

## GAP / StrategyDelta
`GAP-HF-CATALOG-001`: refinado. La ruta alternativa autorizada sí permitió verificar el inventario **público del owner** y devolvió 0; falta verificar modelos privados/endpoints configurados realmente disponibles al Router.

No bloquea tareas independientes, pero bloquea declarar completada la auditoría LLM o generar adapters por modelos supuestos.

StrategyDelta siguiente: cruzar `HF_INFERENCE_ENDPOINT`/referencias persistidas del repo y cualquier registry de endpoints con evidencia accesible; confirmar `model_id/revision/task` por Hub o endpoint real. Solo entonces crear registry/adapters FastAPI.

## Refutaciones
1. `HF autenticado` NO implica `modelos enumerados`.
2. `COUNT 0 público` NO implica `0 modelos privados/endpoints`.
3. `bridge FastAPI presente` NO implica `LLM integrado`.

Estado: `ACTIVE_LOOP / PUBLIC_OWNER_ENUMERATION_VERIFIED / PRIVATE_ENDPOINT_ENUMERATION_PENDING`.
