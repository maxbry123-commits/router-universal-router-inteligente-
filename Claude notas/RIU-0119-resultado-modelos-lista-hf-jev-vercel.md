# RIU-0119 — Resultado de la instrucción (k): modelos de la lista en Hugging Face y Jev en Vercel — 2026-09-21

Instrucción textual: `INPUT-VERBATIM-2026-09-21-k-pesos-remotos-nanbeige-microkernels.md` (K1, K2, K4, K5, K6). Comprobado con las herramientas del Hub y una búsqueda web el mismo día.

## Modelos de la lista (¿existen sus pesos en Hugging Face? ¿con qué se sirven en un Job?)
| Modelo | Pesos en HF | Cómo se serviría por `hf://…:/model:ro` |
|---|---|---|
| LFM2.5-1.2B-Thinking | SÍ oficial: `LiquidAI/LFM2.5-1.2B-Thinking-GGUF` con `Q4_K_M` (730.9 MB), Q5, Q6, Q8, BF16 | llama.cpp estándar (imagen `ghcr.io/ggml-org/llama.cpp:server`) |
| Qwen3-0.6B | SÍ: `Qwen/Qwen3-0.6B` y GGUF oficial `Qwen/Qwen3-0.6B-GGUF` (solo Q8_0, 639 MB) | llama.cpp estándar |
| K2-Horizon-0.9B | SÍ oficial: `IFM/K2-Horizon-0.9B` y `IFM/K2-Horizon-0.9B-GGUF` (cuantizaciones sin listar aún) | llama.cpp si el GGUF está soportado (sin probar) |
| Nanbeige4.2-3B | SÍ: `Nanbeige/Nanbeige4.2-3B` (código propio). Q4_K_M solo de la comunidad (`bartowski/Nanbeige_Nanbeige4.2-3B-GGUF`, `Abiray/…`) | Exige el llama.cpp con la rama `nanbeige42` del fork de Nanbeige: hace falta una imagen propia; la estándar puede no cargarlo (sin probar) |
| NanoJev | SÍ: `C-Tianyu/NanoJev` (`best.safetensors` 2.4 GB + código en `source/` + manifiestos SHA256) y conversiones de terceros | NO llama.cpp: runtime Python con su código (transformers/PyTorch) |
| Decider-0.8B | SÍ: `Mapika/decider-0.8b` (+ GGUF de comunidad `mradermacher/decider-0.8b-GGUF`) | Runtime Python (modelo de decisión); GGUF de comunidad sin probar |
| Decider-2B | SÍ: `Mapika/decider-2b` | Runtime Python |
| Laya-421M | PARCIAL: existe la familia `convaiinnovations/laya`, `laya-multilingual`, `laya-typed-decisions` (clasificación de texto); NO confirmado que alguna sea "421M" | Runtime Python (sin verificar) |
| Verdict-151M | NO ENCONTRADO en Hugging Face (solo modelos ajenos de nombre parecido) | GAP: falta el nombre/URL exacto |
Qwen 9B queda fuera del flujo de código por decisión del Director (K6).

## ¿Sabe Claude llamar al modelo por un Job de HF con pesos remotos? (K2)
SÍ, el patrón es `hf jobs run --flavor cpu-upgrade --expose <puerto> -v hf://models/ORG/MODELO:/model:ro <imagen llama.cpp> -- … --model /model/<archivo>.gguf` y se llama a `https://<job>--<puerto>.hf.jobs/v1/chat/completions` con el token. Ya está escrito por otro chat en `riu-hf-job-serving-smoke.yml` (con LFM2.5-8B-A1B; su resultado NO se ha leído). Lo que FALTA: correr esa prueba con los modelos de esta lista, la imagen para Nanbeige, el runtime Python para NanoJev/Decider y el monitor de RAM/CPU por nodo (verde/amarillo/drenaje/cerrado) del punto K6.

## Jev en Vercel AI Gateway (K4/J4)
Confirmado hoy: existe `typesafe-ai/jev` (lanzado el 2026-09-15; precio publicado 0.042 USD por millón de tokens de entrada, salida gratis; devuelve decisiones tipadas con probabilidades, NO texto). Se llama SOLO con el AI SDK 7 (`experimental_evaluate`); no funciona por los endpoints compatibles con OpenAI. Requiere una cuenta de Vercel y una clave de AI Gateway (`AI_GATEWAY_API_KEY`), que Claude no tiene. El conector de Vercel del Director está `connect_incomplete` y solo lee. GAP: sin esa clave no se puede probar Jev.

## ¿Chat provisional en Vercel o en Hugging Face? (K3) — recomendación de Claude
Vercel para la cara del chat y su API (gratis, ya se usará para Jev y para el puente de webhooks); Hugging Face Jobs para el cómputo y los modelos locales. Motivo: los Spaces Docker de HF exigen PRO (402); Vercel no guarda archivos entre peticiones (el almacenamiento debe ir fuera) y tiene límite de tiempo por petición (a verificar). El Director decide.
