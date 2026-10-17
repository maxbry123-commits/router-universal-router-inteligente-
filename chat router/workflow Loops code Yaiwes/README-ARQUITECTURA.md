# README arquitectura — workflow Loops code Yaiwes

Raíz única: https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/main/chat%20router/workflow%20Loops%20code%20Yaiwes

Regla del Director: INPUT literal → STATE/CHECKPOINT → delta 1×1 → verify/refute → persist → siguiente nodo. DSL-DAG P1–P8; el harness de DeepSeek es la base que conecta el wordflow; Hermes + OpenClaw son la base permanente del chat.

## Subraíces

- agentes/ — solo 3 subcarpetas: chat-router-05-AGENTES (asistentes, colmena, gobierno, AGENTES.yaml), plan-opus-agentes, handoffs-agentes: https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/main/chat%20router/workflow%20Loops%20code%20Yaiwes/agentes
- code/ — código del loop (wordflow_loop, runtime, memoria, backend, minimax_mcp, skills_schema, workspace, harness-plugins, plan-opus-runner): https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/main/chat%20router/workflow%20Loops%20code%20Yaiwes/code
- workflow/ — DSL-DAG, contrato, nodos, centro de control, bitácora/crazy wall, estado: https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/main/chat%20router/workflow%20Loops%20code%20Yaiwes/workflow
- skills/ — skills del loop (ECC): https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/main/chat%20router/workflow%20Loops%20code%20Yaiwes/skills
- HANDOFF único: https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/chat%20router/workflow%20Loops%20code%20Yaiwes/HANDOFF.md

## ⚠️ Archivos VIVOS (cableados): la copia aquí es de lectura; el ORIGINAL es el vivo

Los workflows no se editan, así que estos originales siguen en su sitio. Si cambias algo, cámbialo en el original.

- router inteligente universal/agents-yaiwes (SIN copia aquí desde t144u; se usa directo el original)
  - Vivo: https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/main/router%20inteligente%20universal/agents-yaiwes
  - Lo lee: riu-agents-run.yml y otros ~20 workflows
- router inteligente universal/agents (SIN copia aquí desde t144u; se usa directo el original)
  - Vivo: https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/main/router%20inteligente%20universal/agents
  - Lo lee: ORDERS.yaml (RUN-002) + run_agent.py
- agentes/chat-router-05-AGENTES = COPIA de chat router/05-AGENTES (asistentes, colmena, gobierno)
  - Vivo: https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/main/chat%20router/05-AGENTES
  - Lo lee: workflows del chat (3 refs)
- workflow/plan = COPIA de chat router/01-PLAN + archivos solo-rama Devin (DSL-DAG P1-P8, contrato, nodos); si un archivo chocaba, la versión de la rama está en workflow/version-rama-devin/
  - Vivo: https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/main/chat%20router/01-PLAN
  - Lo lee: workflows del chat
- workflow/estado = COPIA de chat router/03-ESTADO + 03-ESTADO de la rama Devin (HANDOFF.md, memoria.md, EQUIPOS)
  - Vivo: https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/main/chat%20router/03-ESTADO
  - Lo lee: workflows del chat
- workflow/estado-y-handoff-global = COPIA de Estado y handoff global (bitácora, ESTADO.json, CRAZY_WALL)
  - Vivo: https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/main/Estado%20y%20handoff%20global
  - Lo lee: Huggingface/coneccion huggueface Github/CHECKPOINT.json (ruta HF)
- agentes repo (Plan Opus) — vivo en el repo agentes, lo lee .github/workflows/plan-opus-loop.yml:
  - https://github.com/maxbry123-commits/agentes/blob/main/Claude%20notas/PLAN-OPUS → copia en workflow/plan-opus/ (CENTRO-DE-CONTROL, CRAZY-WALL-BITACORA, PROMPT-DSL-DAG, HANDOFF-PLAN-OPUS) y agentes/plan-opus-agentes/
  - https://github.com/maxbry123-commits/agentes/blob/main/Claude%20notas/PLAN-DSL-DAG-00-CONTRATO.yaml, -01-NODOS, -4-OBJETIVOS, PLAN-MAESTRO-4-OBJETIVOS.md, memoria.md, AGENTS.md → copia en workflow/plan-opus/
  - https://github.com/maxbry123-commits/agentes/blob/main/.github/workflows/plan-opus-loop.yml → copia de referencia en workflow/plan-opus/referencia-workflow/ (NO se ejecuta aquí)
  - runner https://github.com/maxbry123-commits/agentes/blob/main/Claude%20notas/PLAN-OPUS/runner → copia en code/plan-opus-runner/
- Wordflow de 154.810 archivos en agentes: https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes (no se copia por tamaño; se enlaza)
- Harness DeepSeek (base del chat, vivo): https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/main/chat%20router/deepseek-harness-chat
- Motores canónicos (vivos, no se copian): https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/main/Motores%20descarga%20extracci%C3%B3n%20b%C3%BAsquedas

## Hermes y OpenClaw (base permanente del chat; espejo por enlace)

Viven solo en sus repos propios (orden de Antonio, 17-oct-2026). Sin copia de código aquí: el espejo es este enlace fijado a commit.

- Hermes v0.22.2: https://github.com/maxbry123-commits/hermes-agent/tree/d923a5eb487a17c0a68801bba9ef0f56c81040a8
- OpenClaw v2026.10.4: https://github.com/maxbry123-commits/openclaw/tree/383c124cc32ffee3f8e56f549b88da94d269a4af
- Registro del loop: `code/wordflow_loop/wordflow_loop/agent_fleet/agent_fleet_registry.json` (`source_repo` + `source_commit`, `mirror: link`).

## skills/ (ECC)

- Qué es: ECC (affaan-m/ECC v2.2.3, MIT), 311 skills en formato `SKILL.md` (frontmatter `name` + `description`).
- Dónde: https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/main/chat%20router/workflow%20Loops%20code%20Yaiwes/skills/ECC
- Cómo lo llama el loop: `code/skills_schema/ecc.dag.yaml` (claim → execute → verify). El agente del nodo lee `skills/ECC/skills/<nombre>/SKILL.md`; sin runtime (`YAIWES_ECC_COMMAND`) falla cerrado (BLOCKED).

## Movido (no cableado; original borrado)

- Documentos del proyecto/➡️📂 Wordflow LOOP router inteligente universal → https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/main/chat%20router/workflow%20Loops%20code%20Yaiwes/workflow/wordflow-loop

## Origen rama Devin

Rama devin/1790824641-chat-agent-plan (PR #6, cerrada sin merge, cabeza afd424bc9, 2026-10-08): https://github.com/maxbry123-commits/router-universal-router-inteligente-/pull/6 . Se trajo a main solo lo que no existía en main (code/*, Crazy Wall Orquestador, PLAN-4-OBJETIVOS, docs, archivos solo-rama de 01-PLAN y 03-ESTADO). No se trajeron: harness plugins/deepseek-harness-chat (14.096, duplicado del harness vivo), _copias-anteriores (473, copias viejas), 11-EVIDENCIA (informes viejos), 📂 notas auditoría Claude, y las carpetas 00/02/05-13 de la rama porque main tiene versión más nueva.
