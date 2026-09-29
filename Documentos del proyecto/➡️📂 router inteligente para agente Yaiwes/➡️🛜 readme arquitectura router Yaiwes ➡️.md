# ➡️🛜 README ARQUITECTURA — ROUTER YAIWES (pronóstico + búsqueda) — pendiente de instalar

Fecha: 2026-09-22. Router INDEPENDIENTE del Router Inteligente Universal principal, para el "agente Yaiwes" del proyecto. Estado: **NADA instalado
todavía** — esto es el plan, anotado antes de ejecutar, por orden del Director (`Claude notas/INPUT-VERBATIM-2026-09-22-dd-…md`).

## Para qué es
El "input shark" del agente Yaiwes necesita 3 capacidades que el Router principal no tiene: pronosticar series de tiempo (ventas, tráfico,
demanda), razonamiento jerárquico (HRM) y búsqueda web abierta sin pagar por una API de búsqueda comercial.

## Piezas (verificadas que existen; ninguna instalada aún)
### Pronóstico — TimesFM (Google)
| Pieza | Para qué | Estado |
|---|---|---|
| `google-research/timesfm` (repo) | código para cargar el modelo y correr inferencia | oficial, existe |
| paquete `timesfm` (PyPI, 2.0.2) | forma de llamarlo desde Python | oficial, existe |
| `timesfm-forecasting/SKILL.md` | instrucciones para que un agente sepa cuándo y cómo usarlo | oficial, existe |
| `timesfm-forecasting/scripts/check_system.py` | revisa RAM/GPU antes de cargar el modelo | oficial, existe |
| `timesfm-forecasting/scripts/forecast_csv.py` | recibe un CSV, devuelve el pronóstico, sin escribir el pipeline a mano | oficial, existe |
| Colección de Hugging Face `google/timesfm-release` | pesos hasta la versión 2.5 | oficial, existe |
| TimesFM 3.0 (`google/timesfm-3.0-pytorch`) | multivariable, con covariables | licencia NO comercial/NO producción — ojo con esto |
| BigQuery `AI.FORECAST`, Vertex Model Garden, Google Sheets | formas de usarlo sin instalar nada local | de pago / requieren cuenta de Google Cloud |

### Razonamiento — HRM
`sapientinc/HRM-Text-1B` (1B, generación de texto) — existe en Hugging Face. Sin verificar todavía su papel exacto dentro de Yaiwes.

### Búsqueda — Qwen3-0.6B Search Agent + Search-R1 + SearXNG + Crawl4AI
| Pieza | Para qué |
|---|---|
| `pantomiman/Qwen3-0.6B-v0.1` | modelo chico entrenado para decidir cuándo buscar y leer evidencia |
| `PeterGriffinJin/Search-R1` | marco: razonar → buscar → leer → buscar de nuevo |
| `searxng/searxng` | motor de búsqueda propio, sin pagar por API de búsqueda |
| `unclecode/crawl4ai` | abre las URLs encontradas y saca el texto limpio |
| `luxiaolei/searxng-crawl4ai-mcp` o `TadMSTR/searxng-mcp` | une búsqueda + lectura detrás de un servidor MCP |

## Cadena propuesta (sin construir todavía)
```
Petición del agente Yaiwes
  → Qwen3-0.6B decide si hace falta buscar
  → SearXNG (buscador propio) → Crawl4AI (lee las páginas) → reranker
  → paquete de evidencia ya filtrado
  → TimesFM (si la tarea es un pronóstico) o HRM (si es razonamiento) o DeepSeek (si es complejo)
  → resultado
```

## Pendiente (todo)
1. Descargar README + código fuente de cada pieza (delegado al agente 12, ver `agents-yaiwes/agent-12-yaiwes-router/`).
2. Decidir con qué modelo de pronóstico se prueba primero (2.5, con licencia comercial; NO 3.0 todavía, por su licencia).
3. Confirmar con el Director para qué caso de uso concreto se necesita el pronóstico (sigue sin decir qué va a pronosticar).
4. Armar el Router de Yaiwes en su propio código, separado del Router principal, una vez estén las piezas.
