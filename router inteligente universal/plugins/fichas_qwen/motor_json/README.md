# Adaptación del patrón Ricardo Bertran → YAIWES

Este paquete **no es una copia del código de Ricardo**: contiene un motor original de referencia para demostrar cómo adaptar el contrato `meta` + `ops` de su puente JSON/Python a un DAG permitido, con siete pruebas unitarias offline. La integración con las fichas y el Router real no se ha probado y **no debe aplicarse sin inspección de los componentes existentes**.

## Fuentes específicas de Ricardo Bertran

- `RicardoBertran/blender-json-scene-pipeline`: `tools/blender_tool/blender_cli.py`, `scenes/ai_scene.json`, `scenes/smoke_test.json`, `docs/scene-format.md`, `docs/architecture.md`.
- `RicardoBertran/qwen38-autonomous-fasth3`: `PROMPT_INSTALACION.md`, `README.md`.
- `RicardoBertran/llamacpp-agente-windows`: `README.md`.
- `RicardoBertran/qwen36-q4-mtp-cline`: `prompts/cline-gpu-pulse.md`, `configs/qwen36-35b-q4-mtp-256k.ini`.
- `RicardoBertran/VScode-Cline`: `prompts/prompt-maestro.md` (reconstruido, según repo).
- `RicardoBertran/qwen-nemotron-benchmark`: `prompts/agentic.txt`, `configs/sampling/qwen-agentic.json`, `results/validation/`.
- `RicardoBertran/comparativa-lfm25-qwen36`: `pruebas/02-inventario/prompt.txt`, `pruebas/03-organizacion/prompt.txt`, `docs/trazabilidad.md`.
- `RicardoBertran/ollama-nimble-decision-layer`: `docs/integration.md`, `examples/request.json`, `examples/response.json`.
- `RicardoBertran/mimo-vs-qwen-local-comparison`: `prompts/03-context-strict-json.md`.
- `RicardoBertran/qwen35-9b-vs-moe`: `prompts/02-planificacion.txt`, `prompts/03-programacion.txt`, `pruebas/verificar_codigo.py`.
- `RicardoBertran/modelos-ia-local`: `README.md`, `examples/continue.yaml` (incluye DeepSeek-R1 Distill Qwen 14B como modelo probado para razonamiento, no como agente autónomo).

No se identificó un repositorio del autor con un sistema publicado de programación autónoma usando **GLM-5** ni un framework **Claude Code** propio. Una publicación de comparación local/nube menciona Claude Sonnet, pero no constituye código reutilizable de Claude.

## Ejecución local del ejemplo

```bash
python motor_cli.py examples/smoke_test.json --policy allowed_ops.json --root ./workspace_demo
python motor_cli.py examples/plan_objetivo.json --policy allowed_ops.json --root ./workspace_demo
python pruebas_motor.py
```

`YAIWES_OP_REPORT` informa estado y recibos, pero `finish` cierra únicamente el lote: **no certifica el objetivo global**. La salida de la API del modelo debe validarse y nunca debe permitir nuevos nombres de operaciones por sí misma. No están incorporadas ejecuciones de shell, navegador, escrituras de repositorios ni modificaciones remotas.
