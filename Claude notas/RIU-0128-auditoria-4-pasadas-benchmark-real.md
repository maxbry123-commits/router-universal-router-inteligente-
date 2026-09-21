# RIU-0128 — Instrucción (u): solo chat y modelos locales; auditoría en 4 pasadas — 2026-09-21 15:20 UTC

Instrucción textual: `INPUT-VERBATIM-2026-09-21-u-auditar-4-pasadas-chat-modelos.md`. Prioridad ÚNICA: el chat y los modelos de IA locales (Jev, Muse Glimmer y agentes de Meta quedan pendientes). "para si" = GAP (no se entiende).

## Estado del enjambre tras la ronda de las 14:54 (15 min; evidencia: run `35615257838`)
CERRADOS: agente 1 (paneles), 2 (trabajos, plantilla fija, Crazy Wall), 3 (Static Space), 4 (registro, Job, monitor), 6 (RAM/nodos), 8 (pool local + ruta espejo), 9 (catálogo + plan de 10 nodos).
PARCIAL: agente 7 (llama_cmd y hf_job cerrados; `bench_report` agotó el tiempo). BLOQUEADO: agente 5 auditor (agotó el tiempo en su primera pasada: ahora responde desde el contexto, 6 pasos máx.).

## Benchmark real de llama.cpp (runner de 4 vCPU; run `35614491628`; 1 copia de pesos, 4 ranuras, atención flash, KV q8_0, `--cache-ram 512`)
| modelo | pp256 | tg128 | 1 sesión | 4 sesiones (total / cada una) | 8 sesiones (total / cada una) |
|---|---|---|---|---|---|
| Qwen3.5-0.8B Q4_0 (563 MB) | 136.2 | 44.2 | 39.5 t/s | 57.6 / 14.4 | 60.3 / 7.5 |
| LFM2.5-1.2B Instruct Q4_K_M (731 MB) | 88.6 | 44.5 | 39.4 t/s | 48.2 / 12.0 | 49.4 / 6.2 |
| Qwen3-0.6B Q8_0 (639 MB) | 149.5 | 50.3 | – | – | – |
| Gemma 4 E2B QAT Q4_0 (3.3 GB) | 42.7 | 18.0 | – | – | – |
Lectura: el límite es la CPU (con 4 vCPU, 4 sesiones dan ~1.5× el total de 1 sesión); más sesiones simultáneas solo reparten lo mismo. El escalado real es por NÚMERO DE NODOS (10 nodos de 8 vCPU).

## Auditoría de 4 pasadas (agente 5; run en curso)
Pasada 1 chat · 2 almacenamiento y cableado de agentes con chat y documentos · 3 modelos locales y aceleradores · 4 verificación cruzada. Cada pasada = todas las notas del Director filtradas por tema (`agent-5-auditor/packs/lens-*.md`, texto literal). Salidas deterministas: `agent-5-auditor/AUDIT-CHECKLIST.md` y `agent-5-auditor/DELEGACION.md` (lo que se manda hacer, por área).

## Sin agente asignado todavía (lo verá la pasada 2)
Almacenamiento para agentes en HF (SQL, grafo, caché, documentos) y cableado de los agentes con el chat y con los documentos.
