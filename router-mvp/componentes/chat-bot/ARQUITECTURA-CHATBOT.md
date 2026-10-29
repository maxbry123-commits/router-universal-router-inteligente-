# Arquitectura del chatbot (tipo GrokBot) — PENDIENTE DE ANÁLISIS

Estado: esqueleto. El análisis completo es la «Salida 2»; hasta entonces no se cablea nada.

## Objetivo
Una UI web y local, con modelos pequeños embebidos y almacenamiento local, que funcione como GrokBot.

## Componentes descargados con el motor de descarga y extracción (motor 2)
Cada uno quedó con `DOWNLOAD_EXTRACT_MANIFEST.json` (hashes), `_archives/` (partes ≤12 MiB) y `code/` (árbol extraído). Índice: `README-INDICE-COMPONENTES.md`.

| Capa | Componente | Para qué sirve | Licencia / aviso |
|---|---|---|---|
| Referencia GrokBot | `OpenBot-ashhart` | Réplica de GrokBot: app de escritorio local que maneja varios agentes en una conversación | revisar LICENSE |
| Referencia GrokBot | `OpenBot-nightly-labs` | Espacio de trabajo local con agentes persistentes, colas, navegador embebido | **PolyForm Noncommercial: solo uso no comercial** |
| Modelos embebidos (navegador) | `web-llm` | Ejecuta LLM pequeños en el navegador con WebGPU | revisar LICENSE |
| Modelos embebidos (navegador) | `transformers.js` | Modelos de Hugging Face en el navegador (ONNX/WASM) | revisar LICENSE |
| Modelos embebidos (navegador) | `wllama` | llama.cpp en WebAssembly (GGUF en el navegador) | revisar LICENSE |
| Almacenamiento local | `pglite` | Postgres embebido en el navegador | revisar LICENSE |
| Almacenamiento local | `sqlite-wasm` | SQLite en el navegador | revisar LICENSE |
| Ya existente | `open-webui` | Interfaz de chat abierta (referencia de UI) | revisar LICENSE |

## No descargado
- `docs.x.ai/grok-bot/overview` y `openbot.run`: el entorno de ejecución no tiene acceso a esos dominios. `openbot.run` es el sitio de otro proyecto (robot con teléfono), no del chatbot.

## Preguntas abiertas del análisis
1. ¿La UI local corre sola en el navegador (web-llm / wllama) o habla con el Router?
2. ¿Qué modelo pequeño se embebe y de dónde se descarga?
3. ¿Dónde se guarda el historial local (pglite o sqlite-wasm) y cómo se sincroniza con el almacenamiento de HF?
4. Licencia: lo que se copie de `OpenBot-nightly-labs` queda limitado a uso no comercial.
