# Handoff — LLM system HF (Plano HF)

Actualizado: 2026-11-11 · Rama: ccr-f01c3de9-bmry0s · Salida 1/3 HF CERRADA.

## Estado
Space Docker que sirve un modelo GGUF local con llama-server, detras de proxy
con X-API-Key. Auto-pull de GitHub via entrypoint.sh. Verificacion SHA-256
contra registry.json al cargar modelo. Stream SSE opcional.

## Componentes
| Archivo | Funcion |
|---|---|
| Dockerfile | Ubuntu 24.04, llama.cpp b12000, puerto 7860 |
| entrypoint.sh | git clone/pull + download_model + exec manager.py |
| download_model.py | Descarga GGUF desde HF a /data/models |
| manager.py | Proxy 7860, carga llama-server 8081 bajo demanda, idle unload, stream SSE, sha256 |
| registry.json | Manifest s1/s2/s3 con sha256 (fill-on-first-run) |

## Variables de entorno
GITHUB_TOKEN (obligatoria) · GITHUB_BRANCH (poner ccr-f01c3de9-bmry0s)
ROUTER_API_KEY (obligatoria, falla cerrado) · MODEL_ID · MODEL_FILE · MODEL_PATH
IDLE_UNLOAD_S (900) · LLAMA_TIMEOUT_S (300) · SPACE_ID (s1/s2/s3)

## Cerrado en Salida 1/3 HF
- Stream SSE (R2 resuelto: stream=true funciona via _sse_proxy)
- Verificacion SHA-256 al cargar (Objetivo 3.6)
- registry.json por Space (Objetivo 3.8)
- entrypoint auto-pull resiliente

## Cerrado previamente
- R3 timeout llama-server 300s (commit 60e27dd03d)
- R1 scaler_ram retirado del CMD

## Pendiente operacional (owner)
- Fijar GITHUB_BRANCH=ccr-f01c3de9-bmry0s en cada Space
- Fijar MODEL_ID/MODEL_FILE/MODEL_PATH en s1/s2/s3
- Prueba en vivo /health y chat
- Calcular sha256 real de GGUF (runtime fill-on-first-run)

## Riesgos abiertos
- R4 modo degradado silencioso si descarga falla (vigilar /health)
- R5 clonado con token en URL (evitar imprimir logs)
- R6 rama divergida main vs trabajo
