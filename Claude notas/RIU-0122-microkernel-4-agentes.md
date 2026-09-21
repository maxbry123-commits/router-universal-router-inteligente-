# RIU-0122 — Prioridad única: 4 microagentes (Claude orquesta, ellos ejecutan) — 2026-09-21

Instrucción textual: `INPUT-VERBATIM-2026-09-21-n-prioridad-4-microagentes.md`. Todo lo demás quedó pendiente (regla del Director).

## Qué se construyó (`router inteligente universal/agent-microkernel/`)
- `workflow.dag.yaml` (esquema `yaiwes.micro-agent/v1`, modo `fail_closed`): 4 agentes. `code-agent` (escribe `template_engine.py`), `recurring-agent` (arma la lista de tareas pendientes desde los GAPs del handoff), `docs-agent` (escribe el contrato `README_AGENTE.md`), `audit-agent` (depende de los tres; resume lo que produjeron con sus sha256). Los tres primeros corren en paralelo; el auditor después.
- `TRIGGER.json`: la orden literal del Director. Claude lo edita y despacha `RIU Microkernel Run` para activar la siguiente ronda.
- `kernel/`: `dag_loader.py` (valida el DAG, niveles en paralelo), `dispatcher.py`, `sheriff.py` (Pydantic; comprobaciones deterministas: AST, ejecución con `exit=0`, esquema de tareas, encabezados, sha256, detector de claves), `state_store.py` (Crazy Wall `yaiwes.crazy-wall/v1`: un archivo por agente + `crazy_wall.state.json`), `runner.py` (reintento máx. 2 con las comprobaciones fallidas; HANDOFF.md determinista).
- Ruta de modelos (orden del Director): NVIDIA / Groq / Cerebras primero; si toda la ruta falla, DeepSeek V4 Flash (recurrentes) o MiniMax M3 (código) por el router de Hugging Face. Cada llamada pasa por el núcleo del Router (Enchufe Gate → RedUniversal, concurrencia adaptativa, cortacircuitos y pool de claves).
- Claves: solo en `runtime-bank.db.gz.b64` (banco cifrado, 18 claves: 5 NVIDIA, 5 Cerebras, 7 Groq, 1 Hugging Face; la 6.ª de Cerebras era idéntica a la 3.ª). El repo es público: sin la contraseña no se abre. La contraseña (24 caracteres aleatorios) está guardada solo como el secreto `RIU_RUNTIME_BANK_PASSPHRASE` del workflow y en el chat del Director.
- Workflow: `.github/workflows/riu-microkernel-run.yml`.

## Desviaciones del diseño pegado por el Director (a su veto)
PocketFlow no se usó (el runner propio son ~60 líneas y ya está probado el resto del Router); LiteLLM no se usó (el Router propio ya da reintentos, respaldo y pool de claves). Falta `sheriff.schema.json` y la carpeta `schemas/`; el disparo por la API de Jobs de HF (sin GitHub Actions) sigue pendiente.

## Pendiente anotado (no se toca hasta cerrar esto)
Banco maestro sin las claves nuevas · chat en Vercel/HF · agentes buscador/escritor web/descargas · SmolAgents · Verdict-151M · clave Jev · modelos locales · benchmark Nanbeige.
