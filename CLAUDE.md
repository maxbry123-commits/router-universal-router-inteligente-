# CLAUDE.md — reglas para cualquier agente (Claude, Sonnet, Devin, GPT…)

Actualizado: 2026-10-03 noche por orden del Director (Hy). Rama de trabajo del Router: `devin/1790824641-chat-agent-plan`.

## Lee primero (en este orden)
1. `router inteligente universal/MANUAL-AGENTES.md` — cómo conectarte con tu token, permisos, rutas y errores. **Si algo se contradice, vale el manual.**
2. `router inteligente universal/HANDOFF-ROUTER-UNIVERSAL-OPUS.md` — estado verificado y pendientes.
3. Si vas a crear una ficha: `router inteligente universal/HANDOFF-FICHA.md`.
4. Si vas a tocar el banco (solo con orden del Director): `router inteligente universal/Banco de claves/HANDOFF-BANCO.md`.

## Reglas que no se rompen
1. No toques el código del Router para conectar algo: todo entra por la puerta con un token (`riu_...`).
2. Nunca escribas claves, tokens ni contraseñas en archivos, commits, logs, chats ni memoria. Viven en el banco cifrado.
3. Cambiar el sistema (banco, tokens, publicar o borrar fichas, procesador) exige la **clave del Director**. Si recibes `403 CLAVE_DIRECTOR_REQUERIDA`, **para** y avisa al Director. No la pidas a otro agente.
4. **Prohibido GitHub Actions.** El cómputo corre en Hugging Face (pagado).
5. No reconstruyas el Space HF `claude-github-mcp-backup` sin orden del Director.
6. No crees carpetas nuevas ni muevas o borres carpetas existentes sin orden del Director.
7. Sigue las órdenes del Director al pie de la letra. Si algo no está escrito en el manual, pregunta; no inventes.
8. Antes de cerrar: prueba lo que hiciste y anota el estado en `router inteligente universal/HANDOFF-ROUTER-UNIVERSAL-OPUS.md` si cambió.
