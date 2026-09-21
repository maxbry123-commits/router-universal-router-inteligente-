# RIU-0118 — Resultado de la instrucción (i): motor de búsqueda, modelos en Hugging Face, kit del otro equipo — 2026-09-21

Instrucción textual: `INPUT-VERBATIM-2026-09-21-i-busqueda-modelos-hf-kit.md`.

## I2. Motor de búsqueda de internet
- Existe y funciona (lo construyó otro chat): `websearch_engine.py` en la carpeta `➡️📂motores de descarga extracción copiado movimiento archivos router-universal-router-inteligente-/➡️📂 motor de búsqueda/`. Workflow: `RIU Websearch Run` (`riu-websearch-run.yml`, dispatch con `query` y `providers`) y `riu-websearch.yml` (solo anotaciones).
- Prueba de hoy (run `ws-35551065373`, consulta "Nanbeige4.2-3B GGUF Q4_K_M llama.cpp"): 8 resultados, sin LLM y sin clave (proveedor `ddgs`, estado PASS). Publica `router inteligente universal/websearch-results/<run>/summary.md`. Hay 10 corridas guardadas (9 de otro chat).
- Límites: corre en GitHub Actions (quien lo use necesita un token con permiso de Actions en este repo); NO es un endpoint del Router ni está conectado al chat; Brave/Tavily/Serper/Firecrawl solo funcionan si existen sus claves (no hay). Uso autónomo (sin GitHub) sin probar.

## I3. Modelos en Hugging Face (comprobado con las herramientas del Hub, 2026-09-21)
| Modelo | En el Hub | Servido por API (Inference Providers) | Q4 |
|---|---|---|---|
| Decider-2B (`Mapika/decider-2b`) | Sí, 1.9B, apache-2.0, 20K descargas, actualizado 2026-09-20 | No | No aplica (modelo de decisión, no chat); hay Space de demo |
| Qwen3-0.6B (`Qwen/Qwen3-0.6B`, original) | Sí | Sí, `featherless-ai` (live); OJO: nuestra prueba del 2026-09-20 dio 503 | El GGUF oficial solo trae Q8_0 (639 MB) |
| Nanbeige4.2-3B (`Nanbeige/Nanbeige4.2-3B`) | Sí, 4.2B parámetros reales, código propio (`custom_code`), 100K descargas | No | GGUF Q4_K_M de la comunidad: `bartowski/Nanbeige_Nanbeige4.2-3B-GGUF`, `Abiray/Nanbeige4.2-3B-GGUF`, `owao/...`; exige el fork de llama.cpp rama `nanbeige42` (o Ollama `nanbeige/nanbeige4.2:3b-Q4_K_M`). El Director oficial ofrece GPTQ-Int8 y FP8 |
| Qwen3.5-9B Q4 | Sí | El original `Qwen/Qwen3.5-9B` lo sirven 4 proveedores (together, featherless-ai, ovhcloud, deepinfra) | `unsloth/Qwen3.5-9B-GGUF`: `Qwen3.5-9B-Q4_K_M.gguf` 5.7 GB (también `bartowski/Qwen_Qwen3.5-9B-GGUF`) |
Corrección de Claude: antes dije que los Jobs de HF no pueden servir un endpoint. Es falso: `hf jobs run --expose <puerto>` publica `https://<job>--<puerto>.hf.jobs` (lo usa `riu-hf-job-serving-smoke.yml` de otro chat, resultado sin leer). Los modelos locales sí pueden servirse desde un Job (cpu-upgrade 32 GB alcanza para Q4 de 9B).

## I4. ¿El kit del otro equipo se conecta con nuestro Router?
NO. `KIT-EQUIPO-NVIDIA/nvidia_team_client.py` llama directo a NVIDIA con su propio respaldo simple entre 4 claves: no pasa por el Enchufe Gate, ni por el hot-path, ni por la caché, el cortacircuitos, la política de grupos ni el DAG. Solo son las APIs. Para pasar por el Router: correr `uvicorn integration.chat_mvp.app:app`, importar el banco del equipo (`POST /vault/import`), abrirlo (`/vault/unlock`) y llamar a `/chat/route` o `/chat/send` con una API key MAXBRY. Eso funciona en local; el Router aún no tiene URL pública.
