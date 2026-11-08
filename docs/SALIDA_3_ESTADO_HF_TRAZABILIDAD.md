# SALIDA 3: ESTADO DE HUGGING FACE Y TRAZABILIDAD

Mapa de infraestructura: qué hay en la nube, dónde están los archivos y cómo auditarlos.

---

## 1. Estado del Repositorio en GitHub

- **Repositorio:** maxbry123-commits/router-universal-router-inteligente-
- **Rama de trabajo:** `ccr-f01c3de9-bmry0s` (contiene los Lotes 1 al 35).
- **Rama `main`:** no contiene la rama de trabajo. Ver sección 7 (verificación).
- **URL de trazabilidad (historial de commits):**
  https://github.com/maxbry123-commits/router-universal-router-inteligente-/commits/ccr-f01c3de9-bmry0s
- **Código clave (dónde buscar):**
  - `ROUTER MVP v1/system_prompt_py/` — router central, orquestador, cliente MCP.
  - `llm system HF/` — manager de modelos locales, `entrypoint.sh`.

---

## 2. Estado de los Spaces en Hugging Face

Los Spaces están divididos en 2 edificios. Actualmente están en estado **PAUSED** porque la cuenta no tiene créditos prepago (error 402), pero el código está listo para arrancar en cuanto haya saldo.

**Edificio 1 — Modelos locales (CPU Upgrade 32 GB):**

- `swe-code-s1`: configurado con `qwen2.5-coder-0.5b`.
- `swe-code-s2`: configurado con `lfm2.5-350m`.
- `swe-code-s3`: configurado con `qwen3-0.6b`.
- Regla: se apagan solos a los 15 minutos (`sleep_time=900`) si no reciben llamadas.

**Edificio 2 — Cómputo / Router / Agentes (CPU Upgrade 32 GB):**

- `riu-router`: router central. Tiene `app.py`, `control_api.py` y `MCPMemoryClient.py`.
- `swe-code-web`: space del puente web con OpenClaw. Intacto, no se borró.
- `claude-github-mcp-backup`: space de respaldo.

---

## 3. Estado del Almacenamiento (Buckets y Datasets)

- **Buckets (43.2 GB usados):** se limpió la basura de auditorías y logs viejos.
- **Datasets (18 GB usados):**
  - `swe-code-hf-gguf` (9.14 GB): protegido. Son los pesos de los modelos.
  - `swe-code-loras` (2.82 GB): protegido. Son los adaptadores por modo.
  - `router-universal...auditoria`: se limpió el exceso de basura.

---

## 4. Variables de entorno (Secrets) requeridas

Para que los Spaces arranquen, deben estar configurados estos Secrets en Hugging Face:

1. `ROUTER_API_KEY`: clave maestra para que el chat se conecte al router.
2. `GITHUB_TOKEN`: para que `entrypoint.sh` haga el auto-pull del código.
3. `AGENT_HARNESS_URL`: URL HTTP del harness de DeepSeek para ejecutar herramientas.
4. `MCP_MEMORY_URL`: URL HTTP del servidor de memoria del harness (`checkpoint_put`, `handoff_pack`).
5. `GROQ_KEYS` y `NVIDIA_KEYS`: llaves de API separadas por comas.

Los valores no se guardan en este documento.

---

## 5. URLs visibles del proyecto (handoff)

- Repositorio (código): https://github.com/maxbry123-commits/router-universal-router-inteligente-
- Router en vivo (cuando tenga saldo): https://comand-center-1-riu-router.hf.space
- Endpoint de OpenAI (para el chat): https://comand-center-1-riu-router.hf.space/v1/chat/completions
- Endpoint de control (ON/OFF): https://comand-center-1-riu-router.hf.space/control/{space_id}/pause
- MCP de memoria (harness): `http://[TU_IP_DEL_HARNESS]:8791/mcp`

---

## 6. Último lote de código

- Commit `c38821dd87` — Lote 35: ventana de proveedor (114 s), sin fallback en 429, aviso de saldo (`no_balance`), división a ≤200 LOC y parcial persistente.
- Ubicación: `ROUTER MVP v1/system_prompt_py/` (`provider_window.py`, `fallback_middleware.py`, `generic_model_adapter.py`, `openai_compatible_proxy.py`, `code_splitter.py`, `semantic_checkpoint.py`, `chat_b_implementer.py`, `chat_ab_orchestrator.py`).

---

## 7. Verificación realizada al guardar este documento

Comprobado en el repositorio:

- La rama `ccr-f01c3de9-bmry0s` está en `c38821dd87`, por encima de `31fc302f8a` (Lote 34). Sí contiene el Lote 35, no solo 1–34.
- Las carpetas `llm system HF/` y `ROUTER MVP v1/system_prompt_py/` existen.

**No comprobado en este paso:**

- Estado PAUSED de los Spaces, error 402, tamaños de buckets y datasets, y existencia de los Secrets. Son datos reportados, no verificados contra Hugging Face.

**Discrepancia que conviene revisar:**

- La afirmación "rama `main` intacta y protegida" no coincide con el repositorio. `origin/main` está en `7ff5e111ba` y tiene commits que no están en la rama de trabajo, entre ellos `hf-emergency-cleanup` (eliminación de `keep_alive`) y commits "Auto-commit … Auditado por Sheriff". La rama de trabajo tampoco está contenida en `main`. Ambas historias han divergido. Antes de cualquier PR hay que decidir cómo integrarlas.
