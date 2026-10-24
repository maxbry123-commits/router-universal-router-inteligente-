# Fichas y prompt — arquitectura

- **Ficha única** del chat: Qwen Token Plan (`mvp/modelos.json`). Las fichas heredadas `nv-*`, `hf-*`, `ask-consil*` usan el modelo por defecto.
- **Capas del system prompt** (de fuera a dentro): formato de salida (siempre) ➡️ system prompt completo (`mvp/system-prompt/`, solo con el botón ON) ➡️ bloque de modo (`mode_router`, no en el modo por defecto para no apagar herramientas) ➡️ mensaje propio con constitución, yaiwes.md, sandbox y pendientes ➡️ anclados del usuario.
- **Regla:** el system prompt no se edita ni se recorta; las capas se añaden por fuera.
- `fichas/system-prompt` y `mvp/system-prompt` son la misma copia (mismo SHA de árbol).
