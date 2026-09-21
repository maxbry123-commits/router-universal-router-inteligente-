# RIU-0127 — Instrucción (t): espejo, 10 procesadores, MVP DeepSeek/MiniMax, agentes descargados y enjambre — 2026-09-21 14:55 UTC

Instrucción textual: `INPUT-VERBATIM-2026-09-21-t-espejo-10-procesadores-mvp-delegar.md`. Regla del Director: Claude NO hace las tareas; solo prepara el Router MVP y los agentes y delega.

## Verificado hoy (evidencia)
- El Router corre dentro de un Job de Hugging Face y responde `/health` 200 desde fuera (Job `6ab13e9752d0dbd7f1d79aff`, puerto 8000, 10 min de prueba). Forma correcta: `run_job(..., expose=[8000])` (lista de puertos). El endpoint es `https://<job_id>--8000.hf.jobs` y EXIGE un token de HF con lectura en el espacio del Job: un chat estático necesita OAuth (GAP por validar).
- Tokens por segundo reales (runner de 4 vCPU, llama.cpp b11071, flash attention): Qwen3.5-0.8B Q4_0 pp256 154.7 / tg128 28.2 t/s; LFM2.5-1.2B Instruct Q4_K_M pp256 103.3 / tg128 30.4; LFM2.5-1.2B Thinking igual. Gemma 4 E2B (3.3 GB), Qwen3-0.6B y las ranuras 1/4/8 en paralelo: benchmark relanzado (1 copia de pesos, 4 ranuras, KV q8_0, `--cache-ram 512`).
- Un Job de HF cpu-basic y cpu-upgrade completan (el ERROR de antes era del script).
- La ronda de 5 agentes anterior se colgó una hora por falta de límites de tiempo (corregido: 12 min por paso, 75 s por llamada, 30 min por agente).

## Router MVP para los agentes (orden del Director)
`agents-yaiwes/ROUTE.json`: pasos de CÓDIGO → MiniMax M3 primero (`route_code`); TRABAJOS → DeepSeek V4 Flash primero (`route_jobs`); después Groq, NVIDIA, Cerebras. Ambos por el router de HF (se cobran a la cuenta de HF). Cuando el chat esté 100 % operativo y los modelos locales instalados, se CIERRA su acceso quitando esas entradas.

## Definiciones aclaradas por el Director
- ESPEJO = usar el MISMO peso del modelo en varias sesiones a la vez sin copiar el modelo (una copia cargada por servidor, varias ranuras).
- Reducir la caché SOLO para modelos locales: caché KV `q8_0`, contexto por ranura acotado, `--cache-ram` limitado, sin `--mlock`; si un nodo no aguanta, se salta al siguiente; escala a 10 nodos HF de 32 GB.

## Paso 2 (crear y descargar los agentes)
Workflow `RIU Download Agents`: clona en pequeño los agentes que el Director dio (Muse Code SDK, Muse Glimmer / agent loop, MetaCua, CUA + MCP, SmolAgents, PocketFlow) a `agents-yaiwes/donors/` con `MANIFEST.json` (commit, archivos, estado). Interpretación de Claude de "los agentes que te di"; si era otra lista, es un GAP.

## Paso 3 (enjambre activado con las tareas del plan): agentes 1 a 9 (cada carpeta `agents-yaiwes/agent-*/chain.yaml`)
1 chat (paneles) · 2 chat (trabajos, plantilla fija, Crazy Wall) · 3 HF (chat sin PRO: Static Space) · 4 HF (registro de modelos, Job, monitor) · 5 AUDITOR · 6 HF nodos (RAM, caché reducida, 10 procesadores, salto de nodo) · 7 HF llama-server (aceleradores, Job, benchmark) · 8 Router (pool de nodos locales + ruta espejo para que los agentes no se paren) · 9 modelos (catálogo de TODOS los modelos dados + plan de instalación en 10 nodos). El workflow `RIU Agents Run` ejecuta toda carpeta `agent-*` con `chain.yaml` en paralelo.

## Pendiente anotado (no se toca hasta cerrar esto)
Publicar el Static Space y unirlo al Router del Job (OAuth) · integrar los entregables verificados en el Router (manifiesto de integración con pruebas) · lanzar los servidores de modelos en los 10 nodos y medir · Muse Glimmer + 4 agentes de Meta (el Director dirá qué harán) · puente con Jev (Vercel de solo lectura) · Groq clave 1 inválida.
