# HANDOFF COMPLETO — 2026-09-22 11:41 UTC (Paso 1: actualización de contexto)

Estado real de TODO lo que está en curso. Fuente de verdad: este archivo + `agents-yaiwes/*/crazy_wall.state.json` de cada agente.

## Enjambre de agentes (13, cada uno con su chain.yaml)
| # | Nombre | Marco | Tarea | Estado a esta hora |
|---|---|---|---|---|
| 1 | chat-hf | PocketFlow | paneles del chat (banco, Router, cableado) | CERRADO 3/3 |
| 2 | chat-hf-smol | SmolAgents | panel de trabajos, plantilla fija, Crazy Wall | CERRADO 3/3 |
| 3 | router (HF sin PRO) | PocketFlow | Static Space (README, index.html, script) | CERRADO 3/3, sin publicar |
| 4 | router-smol | SmolAgents | catálogo de modelos, Job spec, monitor de nodos | CERRADO 3/3 |
| 5 | auditor | SmolAgents (copia) | auditoría forense 1a1 contra el input verbatim | PARCIAL — lens_chat y lens_storage cerrados; lens_models se agotó por tiempo; lens_cross sin correr |
| 6 | hf-nodes | PocketFlow | plan de RAM, 10 nodos, salto de nodo | CERRADO 2/2 |
| 7 | llama-hf | SmolAgents | comando de llama.cpp con aceleradores, Job spec, reporte de benchmark | CERRADO 3/3 |
| 8 | router-local | PocketFlow | pool de nodos locales + ruta espejo (para que los agentes no se paren) | CERRADO 2/2 |
| 9 | models-catalog | SmolAgents | catálogo completo de modelos + plan de instalación en 10 nodos | CERRADO 2/2 |
| 10 | model-install | PocketFlow | órdenes de instalación validadas (GPU prohibida) | CERRADO 2/2 |
| 11 | download-extraction | SmolAgents | descarga solo de componentes (6 donantes + 15 de Jev, en curso) | CERRADO 1/1 (lista); descargas reales pendientes de confirmar |
| 12 | yaiwes-router | SmolAgents | descarga de piezas del router Yaiwes (TimesFM, HRM, búsqueda) | CERRADO 1/1 (lista) |
| 13 | repo-inventory | PocketFlow | inventario determinista del repo (carpeta de componentes vendidos) | recién creado, en su primera ronda |

## Router: piezas reales construidas (código validado por el Sheriff, estado de cada una)
- **Resiliencia y banco de claves:** hecho, 39-49 pruebas pasan (`test_nvidia_pool.py`, `test_resilience.py`, `test_jev.py`, etc.).
- **`chain.py` (ejecutor de los agentes):** DSL DAG con Sheriff, presupuesto de 12 min por paso y 75 s por llamada; `ROUTE.json` con `route_by_group` (chat → DeepSeek V4 Flash primero; todo lo demás → NVIDIA primero).
- **`jev.py` + `/chat/jev`:** capa Choice/Score/Noul propia, ya probada (mockeada) y funcionando por el camino resiliente del Router.
- **Modelos locales en HF:** NINGUNO corriendo todavía en un servidor real. Solo código (`llama_cmd.py`, `hf_job.py`, `local_pool.py`, `mirror_route.py`) validado por pruebas, sin desplegar.
- **Router de HF en un Job real:** SÍ se probó una vez y respondió `/health` desde fuera (prueba puntual, ya terminado ese Job).

## Modelos "estilo Jev" — resultado real de las pruebas (24 casos, corregido)
Jev oficial (TypeSafe) confirmado CERRADO/de pago, no se instaló. Alternativas abiertas probadas en CPU: Qwen3-0.6B-RLCD-Decision (el mejor hasta ahora), Laya (base y typed-decisions), Decider-0.8B/2B (necesitan GPU para funcionar del todo, cargan pero fallan al calcular en CPU). Pendiente: comparación con HRM-Text-1B, LFM2.5-1.2B, Qwen3-0.6B plano (recién lanzada, sin resultado leído todavía).

## Pendiente para los 2 orquestadores nuevos (Microsoft Agent Framework + Grok) — NADA instalado
- **Microsoft Agent Framework** (`microsoft/agent-framework`, MIT, confirmado real): pedido como orquestador CENTRAL del Router completo. Falta: descargarlo, que "aprenda" el Router (auditoría + mapa mental), y su README (`➡️📂 readme osquestador router inteligente.md`, ver ese archivo con la plantilla del Director).
- **Grok:** el Director lo pidió como orquestador de los agentes del chat. CORRECCIÓN IMPORTANTE: Grok es un modelo cerrado de xAI, con API de pago — no se puede "descargar" como los modelos abiertos. Falta decidir cómo se conecta (clave de API) antes de avanzar.
- **Ventana selector** (marcar 1 o varios agentes, darles su system prompt, ejecutar): no construida.
- **Centinela (sheriff/guardián/juez) con Qwen 0.6B + Liquid 1B, vigilando antes que el watchdog de Claude:** no construido.

## Puente con el equipo de Opus
3 rutas (pensar / arquitectura y reparación / código) — decidido usar UN solo Router con prefijo `route_opus_*`, sin construir todavía. El documento para que se conecten sigue pendiente.

## Otros GAP abiertos, sin resolver
- Publicar el chat en algún lado real (Static Space listo, sin publicar).
- Vercel: solo lectura, puente con Jev bloqueado.
- El "ficha" del Router (cada ficha = un router con capas adaptativas) — EXPLÍCITAMENTE aplazado por el propio Director.
- La carpeta "Componente open soure router inteligente universal/" (Chart.js, LiteLLM, Prefect, etc., miles de archivos ajenos) — el agente 13 la está inventariando ahora.
- Límite de gasto en HF: recomendado, sin confirmar si el Director ya lo puso.

## Sobre "limpieza de memoria y del chat, autorización para borrar"
NO borré el historial de `Claude notas/INPUT-VERBATIM-*.md`: es el registro 1 a 1 que el propio Director exigió desde el principio ("anotar cada instrucción textual antes de ejecutar"); borrarlo contradice esa regla suya. Lo que sí hice: este archivo consolida el estado actual en un solo lugar, para no tener que leer 30 archivos sueltos. Si de verdad quieres borrar el historial verbatim, dilo explícitamente y en qué archivos, y lo hago — pero por ahora lo dejo intacto.
