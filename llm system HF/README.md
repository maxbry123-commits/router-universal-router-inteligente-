---
title: LLM system HF
emoji: 🧠
colorFrom: gray
colorTo: blue
sdk: docker
app_port: 7860
pinned: false
---
# LLM system HF

Space de Docker que sirve un modelo GGUF local con `llama-server` detrás de un proxy HTTP con `X-API-Key`. Un Space = un modelo.

Actualizado: 2026-11-08 · rama de trabajo `ccr-f01c3de9-bmry0s`.

## Arquitectura

```
Cliente (router) ──X-API-Key──► manager.py (7860)
                                  │  carga bajo demanda
                                  ▼
                           llama-server (8081, GGUF)
                                  ▲
download_model.py ── Hugging Face ┘  (al arrancar)
entrypoint.sh ─────► clona el repo (GITHUB_BRANCH) y arranca manager.py
```

- `manager.py` descarga el modelo de RAM tras `IDLE_UNLOAD_S` segundos sin llamadas (900 por defecto).
- Si la descarga falla, el Space arranca en modo degradado.
- `scaler_ram.py` está en el repo pero no se ejecuta en esta imagen.

## Variables de entorno

| Variable | Por defecto | Uso |
|---|---|---|
| `GITHUB_TOKEN` | — | Clonado del repo. |
| `GITHUB_BRANCH` | `main` | Poner `ccr-f01c3de9-bmry0s` en este Space. |
| `ROUTER_API_KEY` | — | Obligatoria. |
| `MODEL_ID` | `Qwen/Qwen2.5-Coder-0.5B-Instruct-GGUF` | Repo del modelo. |
| `MODEL_FILE` | `qwen2.5-coder-0.5b-instruct-q5_k_m.gguf` | Archivo GGUF. |
| `MODEL_PATH` | `/data/models/qwen2.5-coder-0.5b-instruct-q5_k_m.gguf` | Ruta para `llama-server`. Debe coincidir con `MODEL_FILE`. |
| `IDLE_UNLOAD_S` | `900` | Segundos de inactividad antes de descargar el modelo de RAM. |
| `LLAMA_TIMEOUT_S` | `300` | Tiempo máximo de espera a `llama-server` por petición. |

## Limitaciones conocidas

- Sin `stream=true`: la respuesta se lee completa.
- La llamada interna a `llama-server` tiene `timeout` configurable con `LLAMA_TIMEOUT_S` (300 s por defecto).

## Verificar

```bash
python3 -m py_compile manager.py download_model.py scaler_ram.py
curl -s https://<space>.hf.space/health
```

## Documentación relacionada

- `docs/handoff/LLM_SYSTEM_HF_HANDOFF.md` — estado, riesgos y pendientes.
