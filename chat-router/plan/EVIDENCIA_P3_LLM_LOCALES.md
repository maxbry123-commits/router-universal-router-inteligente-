# Evidencia P3 — LLM locales conectadas a SWE CODE

Rama: `ccr-f01c3de9-bmry0s` · Sub-agente A-4 (llm-locales) · Plan: `chat-router/plan/PLAN_PASOS_1_A_5.md`
Fecha: 2026-11-09

## 1. Localizacion (tarea 1)

| Eslabon | Ubicacion | Evidencia |
|---|---|---|
| LLM locales (Space HF, llama-server + proxy X-API-Key) | `llm system HF/` | https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/90d569b8e7b93058649bf3f681ddb261ed9e31ce/llm%20system%20HF |
| Proxy local `/v1/chat/completions` con `X-API-Key` | `llm system HF/manager.py` | https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/90d569b8e7b93058649bf3f681ddb261ed9e31ce/llm%20system%20HF/manager.py |
| Harness DeepSeek (metodo de referencia: URL por env, POST, degraded si falta) | `plugins/deepseek_harness/plugin.py` | https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/90d569b8e7b93058649bf3f681ddb261ed9e31ce/plugins/deepseek_harness/plugin.py |
| Puerta LLM del harness (`action=llm` -> `puente_chat.llm_call`) | `plugins/deepseek_harness/plugin.py` | misma URL que arriba |
| Ficha 4 / gateway de modelos | `fichas/fichas_qwen/` | https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/90d569b8e7b93058649bf3f681ddb261ed9e31ce/fichas/fichas_qwen |
| Modelos SWE CODE (swe-code-s1/s2/s3) | `docs/handoff/LLM_SYSTEM_HF_HANDOFF.md` §7 | https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/2de7e38f9385af7eeb97df7a2157f0cc2ce1c262/docs/handoff/LLM_SYSTEM_HF_HANDOFF.md |

Nota: la busqueda de codigo de GitHub devolvio `incomplete_results` para los terminos `SWE CODE`, `deepseek` y `deepseek_harness`; no se usa como prueba.

El proxy `llm_router/openai_compatible_proxy.py` solo enruta Groq y NVIDIA. `llm_router/agentes.py` solo enruta hermes y openclaw. Ninguno referencia el Space local.

## 2. Cableado (tarea 2)

Se anade el plugin `llm_local_swe_code` con el mismo patron que `deepseek_harness` (una carpeta por plugin con `ficha.json`, acciones `status` e `invoke`, degraded sin URL, sin secretos en codigo):

- `plugins/llm_local_swe_code/plugin.py`: POST a `{RIU_LLM_LOCAL_SWE_URL}/v1/chat/completions`, cabecera `X-API-Key` desde `RIU_LLM_LOCAL_SWE_API_KEY`, timeout `RIU_LLM_LOCAL_SWE_TIMEOUT` (def 120 s).
- `plugins/llm_local_swe_code/ficha.json`: contrato `plugin_host/v1`, `allowed_actions` = status, invoke.
- `plugins/llm_local_swe_code/__init__.py`: vacio, igual que deepseek_harness.

Commit: https://github.com/maxbry123-commits/router-universal-router-inteligente-/commit/386edf9e6cd4b262c42ef44497421348a6c93199

Diferencia con el harness DeepSeek: el Space exige `X-API-Key` y no `Authorization: Bearer`, por eso el plugin usa la cabecera `X-API-Key`.

## 3. Criterio por eslabon

| Eslabon | Estado | Evidencia / motivo |
|---|---|---|
| E1 Modelos locales localizados | PASS | Seccion 1 |
| E2 Metodo de conexion identificado (harness DeepSeek) | PASS | `plugins/deepseek_harness/plugin.py` |
| E3 Plugin de conexion LLM local -> SWE CODE escrito con el mismo metodo | PASS | commit 386edf9e6cd4b262c42ef44497421348a6c93199 |
| E4 Plugin registrado en el host y expuesto al router | 🚩 | No verificado: el host de plugins no se leyo (`integration/plugin_host`, `plugins/README-ROJO.md`). |
| E5 Harness DeepSeek -> `puente_chat.llm_call` enruta al Space local | 🚩 | No verificado: `plugins/puente_chat/plugin.py` ocupa 199 KB y no se inspecciono. No se cambio `puente_chat`. |
| E6 Prueba en vivo contra el Space (`/health`, `/v1/chat/completions`) | 🚩 | Sin acceso de red ni llaves en esta sesion. Los Spaces estan PAUSED segun `LLM_SYSTEM_HF_HANDOFF.md` §4 (error 402, no verificado). |
| E7 Variables de entorno en el entorno de ejecucion (`RIU_LLM_LOCAL_SWE_URL`, `RIU_LLM_LOCAL_SWE_API_KEY`) | 🚩 | Pendiente del owner. No se guardaron valores en el repo. |

## 4. Riesgos heredados (no tocados en este lote)

- R1 `scaler_ram.py` (encendido automatico), ver `LLM_SYSTEM_HF_HANDOFF.md` §5.
- R2 sin streaming (`stream=true` no funciona en el Space).
- R4 `GITHUB_BRANCH` por defecto `main`; hay que poner `ccr-f01c3de9-bmry0s` en cada Space.

## 5. Veredicto

P3 queda PARCIAL: el eslabon de conexion del plugin esta cableado en codigo (E3 PASS). La integracion con el harness y la prueba en vivo quedan como 🚩 con motivo explicito (E4 a E7).
