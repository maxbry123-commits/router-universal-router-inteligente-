# RIU-0105 — Chat MVP sobre el Router + selector Kimi K3 / MiniMax / DeepSeek V4 + auth MAXBRY — 2026-09-19

Contrato: `tel.workflow/v3` · `FAIL_CLOSED_LOOP`. Alcance: solo este repo (P3). Número RIU-0105 usado en los commits sin coordinación previa: si otro chat lo usó, renumerar esta entrada, no los commits.

## Input del Director (resumen fiel)
Prioridad única, en bucle, sin escalar: (1) Chat MVP; (2) conectar las API al Router y selector del chat a Kimi K3, MiniMax, DeepSeek V4 Flash y Pro, con GitHub y Hugging Face; (3) auditar y habilitar los modelos con las API para el enjambre de más de 50 agentes.

## Qué se construyó (commits en `main`)
| Pieza | Archivo (bajo `router inteligente universal/`) | Commit |
|---|---|---|
| Catálogo del selector (sin inventar model_id; patrones DeepSeek V4/V4.x) | `integration/huggingface/chat_catalog.py` | `369642d4`, `9a322cf5` |
| Executor: ruta certificada intacta; intento en vivo solo con flag; timeout 60 s | `integration/huggingface/chat_executor.py` | `3dc72514`, `5a52e85a` |
| UI de chat (página única, selector, aviso "NO certificado") | `integration/huggingface/chat_ui.html` | `ad39aeb8`, `e51fffa7` |
| Gateway: `/chat`, `/chat/models`, validación del modelo en el borde HTTP (400) | `integration/huggingface/fastapi_gateway.py` | `b5641027`, `6c1ca19c` |
| Auth: keys del keystore MAXBRY-001..100 con 1 solo PBKDF2 por petición | `integration/huggingface/keystore_auth.py`, `api_key_auth.py` | `2501f83d`, `c5eaac6d` |
| Tests | `tests/test_chat_mvp.py`, `test_chat_catalog_patterns.py`, `test_chat_gateway.py`, `test_keystore_auth.py` | varios |
| Verificación en runner real | `.github/workflows/riu-chat-mvp-verify.yml` | `0b41dbf8` |

## Evidencia (runner real, annotations del check-run 105985371715, run 35476051245, HEAD `0b41dbf8`)
- Tests: **36 passed** (incluye `test_huggingface_openai_chat_registry.py` → cierra `GAP-TEST-EXECUTION-001`; `test_hf_scheduler`, `test_hf_router_hot_path`, `test_identity_pool`, y el keystore real: 100 ranuras activas, solo hashes, ids MAXBRY-001..100).
- E2E por el gateway (API key → Enchufe → RedUniversal → HF → respuesta), prompt "Reply with the single word OK", `HTTP 200 finish=stop`: `moonshotai/Kimi-K3`, `deepseek-ai/DeepSeek-V4-Flash`, `-V4-Flash-0731`, `-V4.1-Flash`, `-V4-Pro`, `-V4-Pro-0813`, `MiniMaxAI/MiniMax-M3`, `-M2.7`, `-M2.5`, `-M2.1`, `-M2`, `-M1-80k`. `Qwen/Qwen3-8B` 200 (certificado). `Qwen/Qwen3-0.6B` y `openai-community/gpt2`: 503 `todos_los_destinos_fallaron` (ningún proveedor los sirve; su "certificación" histórica fue solo en HF Jobs).
- Catálogo del router HF: 138 modelos; incluye MiniMax M1-80k…M3, DeepSeek V4-Flash/Flash-0731/Flash-Vision-Exp/V4-Pro/V4-Pro-0813/V4.1-Flash, Kimi K2.x/K3, GLM 4.x/5.x.
- `HF_TOKEN_1` (cuenta `COMAND-CENTER-1`, fine-grained: `discussion.write`, `post.write`, 1 scope adicional) SÍ hace inferencia vía el router → `GAP-EXTERNAL-CREDENTIAL-SCOPE-001` queda **desactualizado**: el 403 histórico era de la credencial anterior. NO tiene escritura global de repos: un workflow no puede crear el HF Space.
- Estado de certificación: los 12 modelos anteriores tienen `REMOTE_INFERENCE_SMOKE` PASS pero NO `FAILURE_FALLBACK_TEST` ni `EVIDENCE` en el registry → siguen `certified=false`. No se editó `model_registry.json`.

## Cómo correrlo (no desplegado en ningún host todavía)
```
cd "router inteligente universal"
pip install fastapi uvicorn pydantic huggingface_hub
HF_TOKEN=<token con Inference Providers> RIU_CHAT_ALLOW_PROVIDER_LIVE=1 \
  uvicorn integration.huggingface.fastapi_gateway:app --host 0.0.0.0 --port 7860
# abrir /chat ; pegar una key riu_MAXBRY-NNN_... (o definir RIU_AGENT_API_KEYS)
```
Las 100 keys en texto plano las tiene solo el Director (CSV entregado una vez por otro chat). Un agente del enjambre usa `Authorization: Bearer riu_MAXBRY-NNN_...` contra `POST /v1/chat/completions`.

## Duplicidad a resolver (otro chat)
Existe `gateway/hf_chat_mvp/app.py` (Gradio, llama a HF/Groq/NVIDIA/Cerebras directo, sin pasar por el Router). Este nodo es el chat que SÍ pasa por el Router. Propuesta: el Gradio llama a `/v1/chat/completions` del gateway con una key MAXBRY en vez de a los proveedores. Decisión del Director.

## GAPs
- `GAP-CHAT-DEPLOY-001`: sin host. Opciones: HF Space Docker (lo crea el Director; el token no puede), o VPS/Codespace.
- `GAP-MODEL-CERT-001`: registrar los 12 modelos con `FAILURE_FALLBACK_TEST` + evidencia para pasar a `certified`.
- `GAP-LOCAL-MODELS-001`: "modelos locales" no existe en el contrato (`REMOTE_INFERENCE_ONLY`, 0 pesos persistentes). Si el Director quiere inferencia local real (Ollama/llama.cpp/vLLM), es cambio de contrato.
- `GAP-SWARM-50-001`: falta prueba con concurrencia (≥50 agentes simultáneos), límites por key y cuota por proveedor (Kimi K3 lo sirven together/fireworks/featherless/baseten/deepinfra).
- `GAP-DOC-SYNC`: STATE/CHECKPOINT/PLAN/Handoff/bitácora sin este nodo.
- Clave rotación: las credenciales que el Director pegó en chat (según Handoff sección 14) siguen pendientes de rotar.

## Próximo delta seguro
1) Prueba de carga 50 agentes (workflow con 50 keys de prueba efímeras contra el gateway). 2) `FAILURE_FALLBACK_TEST` + registrar modelos. 3) Sync documental. 4) Desplegar cuando el Director cree el Space.
