# 📂 pruebas Nvidia groq

## Prueba 01 — Groq por MCP (sin otro puente)

- Rama: `main`
- Herramienta: conector MCP existente `chat` → `resultado`
- Sesión: `pruebas-nvidia-groq-20261103`
- Proceso: `p-prueba-mcp-groq-20261103-1`
- Modelo: `groq/qwen/qwen3.8-27b`
- Petición: respuesta exacta `GROQ_MCP_PRUEBA_1_OK`, sin herramientas.
- Respuesta: `GROQ_MCP_PRUEBA_1_OK`
- Estado: **PASS** (`completado`, `finish_reason=stop`, `via=harness`).
- Streaming: **sí**, TTFT: 0,6761 s; duración: 0,6971 s; tokens reportados: 77.
- Herramientas utilizadas: 0.
- Evidencia: resultado real devuelto por el MCP del chat; no se ejecutó un bridge alternativo.

## Pendientes

1. Pruebas de generación de 500 líneas de código por Groq y tres modelos NVIDIA.
2. Revisión de los commits creados en las pruebas y validación de los archivos publicados.
3. No inferir que 500 líneas funcionan a partir de la prueba corta.
