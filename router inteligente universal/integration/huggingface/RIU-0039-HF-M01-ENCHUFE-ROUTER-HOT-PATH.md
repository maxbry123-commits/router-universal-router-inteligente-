# RIU-0039 — HF-M01 Enchufe/Router deterministic hot-path

Contrato: `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP`.

## INPUT / prioridad
Continuar exclusivamente P01. Cola 1×1: HF-M01 `Qwen/Qwen3-0.6B`. Objetivo de este delta: eliminar el bypass FastAPI→adapter y demostrar que el código persistido atraviesa Enchufe Gate + RedUniversal antes del adapter HF.

## Investigación previa
- Hugging Face documenta `InferenceClient.chat_completion` y `client.chat.completions.create` como interfaces equivalentes/OpenAI-compatible.
- Hugging Face Jobs dispone de almacenamiento efímero por flavor; datasets y buckets pueden leerse/montarse y los Storage Buckets persisten resultados entre Jobs.
- Fuentes: https://huggingface.co/docs/huggingface_hub/guides/inference y https://huggingface.co/docs/hub/jobs-large-datasets

## Delta ADAPT
1. Creado `integration/huggingface/router_hot_path.py` reutilizando `red/enchufe_gate.py` + `red/red_universal.py`; no se creó segundo router.
2. `fastapi_gateway.py` v0.2 delega a `route_chat_completion()`.
3. Creado `tests/test_hf_router_hot_path.py`; executor sustituible solo para prueba determinista de frontera/ruteo.

Commits:
- hot path: `86f5f545f070dc3180652e73265f6fc77ba1e514`
- gateway: `6da8ecd573986bc4e77a2c749e37d9f34955bd57`
- test: `8509fa25793fec73a1e9ce023787713df5ed4225`

## Verificación material en HF Jobs
Primer intento `6aa2970221047bf1b0372550`: fallo pre-test por payload base64 inválido. StrategyDelta: eliminar base64 y ejecutar bootstrap Python como argv.

Segundo Job: `6aa297195527934177ec0aed` · flavor `cpu-upgrade` · `COMPLETED`.
URL: https://huggingface.co/jobs/COMAND-CENTER-1/6aa297195527934177ec0aed

Read-back desde `main` dentro del Job: `enchufe_gate.py`, `red_universal.py`, `conectores.py`, `huggingface_openai_chat.py`, `router_hot_path.py`, `model_registry.json`, `test_hf_router_hot_path.py`.
Resultado: `2 passed in 1.25s`; `RIU_HOT_PATH_TEST_RC 0`.

## Qué queda probado
- contrato HF aceptado por Enchufe Gate;
- nodo `ai.hf.chat` conectado a RedUniversal;
- ruta declarativa `api.fastapi.hf --[chat.completion]--> ai.hf.chat`;
- payload atraviesa RedUniversal y llega al adapter boundary;
- gateway persistido ya no llama directamente al adapter.

## Lo que NO queda probado
1. Executor fake del test no demuestra provider hosted autenticado.
2. Hot-path determinista no demuestra dataset/storage binding.
3. HF-M01 local inference previa + este test no equivalen todavía a E2E FastAPI→provider real con API key de agente.

Council12: PASS. Cross-check: PASS. CODA: `CLOSE_ROUTER_ENCHUFE_CODE_GAP_KEEP_DATASET_AUTH_PENDING`.
verify_final: `PASS_DETERMINISTIC_ROUTER_ENCHUFE_HOT_PATH_DATASET_AUTH_PENDING`.

HF-M01 continúa NO READY hasta cerrar dataset/storage y la ejecución provider/hot-path real requerida por el plan.