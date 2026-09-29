# EVIDENCIA 2026-09-29 (03:30–03:45 Bogotá)
Solo hechos leídos o probados. Lo demás dice SIN VERIFICAR.

## 1. Modelos de NVIDIA probados en vivo (run 36543892304, 4 claves presentes)
El catálogo de NVIDIA devolvió 81 modelos. Candidatos de las familias pedidas y prueba con 8 tokens:
| Modelo (id exacto) | Resultado |
|---|---|
| `moonshotai/kimi-k3` | 200 en 0,8 s (responde) |
| `z-ai/glm-5.3` | 200 en 1,3 s (responde). No existe "glm-5" a secas: la versión que hay es 5.3 |
| `z-ai/glm-5.3-flash` | sin respuesta en 25 s |
| `deepseek-ai/deepseek-v4.1-flash` | sin respuesta en 25 s con las 4 claves (puede ser arranque en frío; SIN CONFIRMAR) |
| `moonshotai/kimi-k2.6` | existe en el catálogo (no se probó) |
Groq: `qwen/qwen3.8-27b` responde (probado antes, y en el Router vivo grupo g2).
Nota: una primera corrida (36542967275) se cancelo a mano porque su paso de auto-borrado se atascó; no dejó cambios. La sonda ya fue borrada.

## 2. Archivos que el Director subió antes y lo que son (leídos hoy)
| Archivo subido | Qué es | ¿Está en el repo? |
|---|---|---|
| `enchufe_universal_parte_1 … universal_plugin_bus_v2_integrated.py` (30 KB) | "Universal Plugin Bus v2": registro de plugins, cambio en caliente, gobernador de coste, salud, failover, contrato de fichas | NO (solo llegó como adjunto) |
| `enchufe_universal_parte_2 … ficha_contract_v2.py` (17 KB) | Contrato de fichas v2.0: esquema, validador de 36 invariantes | NO como tal (el repo tiene `enchufe/validator_v2.py` y `domain/schemas/enchufe_v2.py`, más chicos) |
| `JSON para IA DSL MAXBRY YAIWES NCT … enchufe de todas las fichas` | Contrato universal de módulos v1.5 (JSON) | Parcial (documento del enchufe v2 de Fables en `Documentos del proyecto`) |
| `MAX-SYSTEM-100X-FINAL-1.md`, `MAVIS-PARALLEL-100X.md` | Guías de paralelismo (de otro agente, "Mavis") | NO (solo adjuntos) |
| `arquitectura chat agentes … NO TOCAR.md` | Arquitectura del chat | SÍ (`chat router/00-INSTRUCCIONES/`) |
| Adjunto 7746ab7d | Informe de otra IA sobre OmniRoute (falla de memoria/lockfile) | NO. Ya no aplica: OmniRoute fue eliminado |
Conclusión: el bus de plugins de Fables (partes 1 y 2) es el candidato natural para el "plugin abierto"; hoy solo existe como adjunto. Falta decidir subirlo al repo.

## 3. Componentes que ya existen en el repo para el Router (inventario por conteo de archivos)
`router inteligente universal/Componentes del Router/`: `hermes-agent` (13 030), `router inteligente software` (2 408, con "componentes descargados", "router core" y "router core version alternativa"), `dataset Yaiwes` (58), `Yaiwes Cognitive Control Plane` (11).
`router inteligente universal/Componente open soure router inteligente universal/` (más de 388 000 archivos): entre otros LiteLLM, llama.cpp, vllm, SGLang, ollama, vLLM-Semantic-Router, vLLM-Router, RouterArena, open-webui, ruflo (con el plugin `ruflo-deepseek-harness`), crewAI, n8n, langgraph, qdrant, chroma, redis, postgres, huggingface_hub, MCP-Python-SDK.
Y en la raíz del Router: `openclaw` (44 964), `rowboat` (1 499), `agents-yaiwes` (852).

### dataset Yaiwes (el dataset del repo para razonamiento)
`Componentes del Router/dataset Yaiwes/`: 107 métodos de razonamiento, 1 139 registros en niveles A/B/C (segmentos JSONL con índice; el Router usa registro + índice y recupera solo lo necesario, nunca inyecta el JSONL entero al modelo). Trae un plugin propio (`plugin/yaiwes_dataset_plugin.py`, id `yaiwes.dataset.router` 3.0.0) y su ficha. Su README dice que el cableado del plugin universal está reservado para el ÚLTIMO nodo `PLUGIN-999`.
`Componentes del Router/Yaiwes Cognitive Control Plane/`: 5 módulos deterministas (fuente de verdad, compositor de contexto, consistencia, `router.py` de selección de rutas, guardia de política). Es el mecanismo del selector; no es un segundo Router de modelos.
Estado de integración con el Router en marcha: NO conectado (SIN VERIFICAR por prueba; no hay ninguna ruta suya en `app.py`).

## 4. Proveedor local (lo que existe hoy)
- Código: `integration/chat_mvp/providers.py` entrada `local` (API compatible OpenAI: llama.cpp / Ollama / vLLM). Dirección por la variable `RIU_LOCAL_BASE_URL`, clave `RIU_LOCAL_API_KEY`. Sin la variable, el proveedor queda "no configurado".
- Cadena g2: entrada `local` con modelo por la variable `RIU_G2_LOCAL_MODEL` (vacía hoy → se salta: `local:NO_MODEL_CONFIGURED`).
- Servidor local vivo: NINGUNO. No hay máquina de 32 GB corriendo un modelo.
- Piezas para construirlo, ya descargadas en el repo (sin instalar): llama.cpp, vllm, SGLang y ollama en `Componente open soure…`.
