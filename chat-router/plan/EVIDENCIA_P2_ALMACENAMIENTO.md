# EVIDENCIA P2 — Almacenamiento y memoria (A-3)

Rama: `ccr-f01c3de9-bmry0s` · Plan: `chat-router/plan/PLAN_PASOS_1_A_5.md` · Cadena: harness DeepSeek MCP > Router MVP v1 MCP > almacenamiento Hugging Face

| Eslabón | Estado | Evidencia |
|---|---|---|
| Harness DeepSeek (MCP) | 🚩 Parcial | Existe como plugin HTTP: https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/ccr-f01c3de9-bmry0s/plugins/deepseek_harness/plugin.py (acciones status, invoke, llm). No hay servidor MCP en el repo. Requiere `RIU_DEEPSEEK_HARNESS_URL`. |
| Router MVP v1 (MCP) | 🚩 Parcial | Existe `ROUTER MVP v1/system_prompt_py/tool_executor.py`: https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/ccr-f01c3de9-bmry0s/ROUTER%20MVP%20v1/system_prompt_py/tool_executor.py. No hay MCP; delega a `AGENT_HARNESS_URL`. |
| Almacenamiento Hugging Face | PASS (mapeo) | Plugin `hf_storage` (list/read/write/backup_sqlite) sobre bucket `COMAND-CENTER-1/yaiwes-memoria-storage`: https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/ccr-f01c3de9-bmry0s/plugins/hf_storage/plugin.py |
| Cableado Router MVP v1 → plugins | PASS (código) | Commit `eaafa6343a1a6063a24ce66dda49d029b90a26bc`: https://github.com/maxbry123-commits/router-universal-router-inteligente-/commit/eaafa6343a1a6063a24ce66dda49d029b90a26bc . Tools `deepseek_harness.<accion>` y `hf_storage.<accion>` se despachan a `plugin.handle`. Sin import válido devuelve `degraded`. |

## Pendientes 🚩
1. **MCP inexistente:** ningún archivo del repo implementa un servidor MCP para el harness ni para el Router MVP v1. Se cableó por plugin (HTTP/import), no por MCP.
2. **Sin prueba en runtime:** no se ejecutó nada (sandbox fuera de A-3). `plugins.*` requiere que la raíz del repo esté en `sys.path`; no verificado.
3. **Variables de entorno:** `RIU_DEEPSEEK_HARNESS_URL`, `HF_TOKEN` (solo nombre de variable, sin valores), `AGENT_HARNESS_URL`. Confirmar que existen en el despliegue.
4. **Búsqueda de código incompleta:** `search_code` de GitHub devolvió índice incompleto; el mapeo se hizo recorriendo directorios.
