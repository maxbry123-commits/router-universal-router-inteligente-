# Handoff — LLM system HF (`llm system HF/`)

Actualizado: 2026-11-08. Rama de trabajo: `ccr-f01c3de9-bmry0s`.

## 0. Registro de actividad (más reciente primero)

- 2026-11-08 — README del Space añadido con arquitectura, variables y limitaciones.
- 2026-11-08 — Handoff actualizado. Sin cambios de código en este Space en esta fecha.

## 0.1 Arquitectura resumida

`entrypoint.sh` clona el repo en la rama `GITHUB_BRANCH` y arranca `manager.py` (proxy en 7860). `manager.py` carga `llama-server` en 8081 bajo demanda y lo descarga tras `IDLE_UNLOAD_S`. `download_model.py` trae el GGUF desde Hugging Face al arrancar. Detalle en `llm system HF/README.md`.

## 1. Qué es
Space de Docker para servir **un** modelo GGUF local con `llama-server`, detrás de un proxy HTTP que exige `X-API-Key` y descarga el modelo desde Hugging Face al arrancar. Es el "Edificio 1" de modelos locales.

## 2. Archivos

| Archivo | Función |
|---|---|
| `Dockerfile` | Ubuntu 24.04. Instala `llama.cpp` b12000 (versión fija en `LLAMA_URL`), `huggingface_hub` y `hf_transfer`. Puerto 7860. |
| `entrypoint.sh` | Clona o actualiza el repo con `GITHUB_TOKEN`, rama `GITHUB_BRANCH` (por defecto `main`), descarga el modelo y arranca `manager.py`. |
| `download_model.py` | Descarga `MODEL_FILE` de `MODEL_ID` a `/data/models`. Si falla, el manager arranca en modo degradado. |
| `manager.py` | Proxy en 7860. Carga `llama-server` en 8081 la primera vez que llega una petición. Descarga por inactividad a los `IDLE_UNLOAD_S` segundos (900 por defecto). |
| `scaler_ram.py` | Vigila RAM y despierta un Space vecino. **No se ejecuta** en esta imagen. Ver §5. |

## 3. Variables de entorno

| Variable | Por defecto | Uso |
|---|---|---|
| `GITHUB_TOKEN` | — | Auto-pull del repo. Obligatoria para clonar. |
| `GITHUB_BRANCH` | `main` | **Poner `ccr-f01c3de9-bmry0s` en este Space.** Con el valor por defecto arranca código de `main`. |
| `ROUTER_API_KEY` | — | Obligatoria. `manager.py` no arranca sin ella. |
| `MODEL_ID` | `Qwen/Qwen2.5-Coder-0.5B-Instruct-GGUF` | Repo del modelo. |
| `MODEL_FILE` | `qwen2.5-coder-0.5b-instruct-q5_k_m.gguf` | Archivo GGUF dentro del repo. |
| `MODEL_PATH` | `/data/models/qwen2.5-coder-0.5b-instruct-q5_k_m.gguf` | Ruta que usa `llama-server`. Debe coincidir con `MODEL_FILE`. |
| `IDLE_UNLOAD_S` | `900` | Segundos sin llamadas antes de descargar el modelo de memoria. |

**Un Space = un modelo.** Para cada Space hay que fijar `MODEL_ID`, `MODEL_FILE` y `MODEL_PATH`. El código por defecto corresponde solo a `swe-code-s1`.

## 4. Estado y comportamiento

- **Sin saldo en Hugging Face:** según el reporte de la SALIDA 3, los Spaces están en PAUSED (error 402). No se ha verificado en esta sesión.
- **Sueño:** la regla de `sleep_time=900` es de la plataforma. `IDLE_UNLOAD_S` solo descarga el modelo de RAM; el Space puede seguir encendido.
- **Arranque:** cada reinicio vuelve a clonar o actualizar el repo y descarga el modelo si falta.

## 5. Riesgos abiertos

- **R1 — Encendido automático:** `scaler_ram.py` despierta el Space de `NEXT_SPACE_URL` cuando la RAM supera el 85 %. No está en el CMD de esta imagen, pero el archivo sigue en el repo. La instrucción previa era eliminar el encendido automático. No activar esta carpeta con `scaler_ram.py` sin revisar.
- **R2 — Sin streaming:** `manager.py` lee la respuesta completa de `llama-server` antes de devolverla. El parámetro `stream=true` no funciona.
- **R3 — Sin tiempo máximo:** la llamada interna a `llama-server` (`urlopen`) no tiene `timeout`. Una generación colgada bloquea el hilo.
- **R4 — Modo degradado silencioso:** si la descarga falla, el Space sigue arriba y responde con error al consumir el modelo. Vigilar `/health` y los logs.
- **R5 — Clonado con token en la URL:** `entrypoint.sh` incrusta `GITHUB_TOKEN` en la URL de clonado. Evitar imprimir logs de ese paso.
- **R6 — Rama divergida:** `main` y la rama de trabajo no se contienen mutuamente (ver `ROUTER_MVP_V1_HANDOFF.md` R3).

## 6. Cómo verificar

```bash
cd "llm system HF"
python3 -m py_compile manager.py download_model.py scaler_ram.py
curl -s https://<space>.hf.space/health          # debe responder {"status":"ok"}
curl -s -X POST https://<space>.hf.space/v1/chat/completions \
  -H "X-API-Key: $ROUTER_API_KEY" -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"ping"}]}'
```

El `curl` de chat carga el modelo y tarda; el primer intento puede pasar de 30 s.

## 7. Pendientes

1. Poner `GITHUB_BRANCH=ccr-f01c3de9-bmry0s` en cada Space que deba correr código de esta rama.
2. Fijar `MODEL_ID`, `MODEL_FILE` y `MODEL_PATH` por Space (s1, s2, s3).
3. Añadir `timeout` a la llamada a `llama-server` (R3).
4. Soportar `stream=true` o documentar que no está soportado (R2).
5. Confirmar que `lfm2.5-350m` y `qwen3-0.6b` existen con esos nombres de archivo en Hugging Face antes de configurarlos.
