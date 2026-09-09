# HF LLM AUDIT — ROUTER INTELIGENTE UNIVERSAL

Contrato: `tel.workflow/v3` · nodo: `P01_COMPONENTS_AND_HF_LLM_AUDIT` · modo: `FAIL_CLOSED_LOOP`.

## Evidencia confirmada
- Cuenta Hugging Face autenticada en la ejecución: `COMAND-CENTER-1`.
- Scope observado: lectura de repos + Jobs; no se infieren modelos privados no enumerados.
- El inventario remoto de modelos NO quedó enumerado: la operación de catálogo `model_search(author=COMAND-CENTER-1)` devolvió `Tool model_search not found`.
- No se inventa ningún `model_id`; el catálogo queda `AUDIT_PENDING_REMOTE_ENUMERATION` hasta una lectura real.

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
`GAP-HF-CATALOG-001`: catálogo remoto no enumerable por el conector actual.

No bloquea tareas independientes, pero bloquea declarar completada la auditoría LLM o generar adapters por modelos supuestos.

StrategyDelta siguiente: usar una ruta alternativa autorizada de lectura del Hub (API/repos del usuario o evidencia persistida en HF/GitHub) y reconciliarla con este archivo. Si se confirma una lista, crear el registry y adapters únicamente para esos IDs.

## Refutaciones
1. `HF autenticado` NO implica `modelos enumerados`.
2. `bridge FastAPI presente` NO implica `LLM integrado`.
3. `model_id sugerido` sin evidencia remota NO cuenta como disponible.

Estado: `ACTIVE_LOOP / AUDIT_PENDING_REMOTE_ENUMERATION`.
