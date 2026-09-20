# RIU-0108 — VALIDACIÓN DE INPUT BLOCKS + PLAN MAESTRO CHAT MVP + CORRECCIONES — 2026-09-20

Contrato: `tel.workflow/v3` · `FAIL_CLOSED_LOOP`. Escritura solo en este repo (P3). Entrada en archivo propio (sin reescribir `BITACORA-CRAZY-WALL.md`). Numeración: RIU-0105 (chat), 0106 (otro chat), 0107 (input 05), este es 0108.

## Input (INPUT BLOCK 06)
Verbatim, con los tokens pegados REDACTADOS (repo público): `Claude notas/INPUT-BLOCK-06-secret-bank-stack-plan-VERBATIM.md` (commit `38e1ee3c`). Aquí y en la adenda de `Readme arquitectura…` quedan las decisiones estructuradas y el enlace al textual, no una tercera copia del texto.

## Validación pedida: "todas mis instrucciones anotadas 1 a 1 verbatim"
| Bloque | Estado antes | Estado ahora |
|---|---|---|
| 01 conectar y recuperar contexto | solo resumen | textual en `INPUT-BLOCKS-01-04-VERBATIM.md` |
| 02 pasos 1-4 | resumen (RIU-0101) | textual |
| 03 vista rápida + escritura | resumen | textual |
| 04a / 04b objetivo chat + modo loop | resumen (RIU-0105) | textual |
| 05 chat + almacenamiento + grupos | textual en 3 sitios | sin cambios (+ fe de erratas de los adjuntos) |
| 06 banco de claves + stack + plan | — | textual en Claude notas (redactado); estructurado aquí y en README arquitectura |
Resultado: los bloques 01-04 NO estaban textuales; ya lo están. Los bloques 05 y 06 están completos con las salvedades indicadas.

## Hechos verificados hoy (runner real)
- `HF_TOKEN_1` (cuenta `COMAND-CENTER-1`): fine-grained; scope de usuario con `repo.content.read`, `repo.access.read`, `repo.write`, `inference.serverless.write`, `inference.endpoints.infer.write`, `inference.endpoints.write`, `collection.write`, `discussion.write`, `job.write`, webhooks y notificaciones. Run `35493036087`. CORRIGE `RIU-0105`/`RIU-0107`: el token SÍ puede escribir repos/Spaces y lanzar Jobs; no hace falta el token pegado.
- Motor de búsqueda del Router ejecutado en runner: ddgs 8/8 resultados por consulta, sin LLM. Run `35493077904`. Workflow reutilizable `.github/workflows/riu-websearch.yml`.
- Metadatos: Open WebUI 152,590★ (licencia propia), LibreChat 44,424★ MIT, Graphiti 31,021★ Apache-2.0, FalkorDB 6,190★ (NOASSERTION), AgentDB 89★ (push 2026-07-30), SQLCipher 7,280★ BSD-3. Check-run `106030864774`.
- Hub: Decider-2B-Vision (Apache-2.0, base Qwen3.5-2B-Base, 105 descargas), NanoJev (base Qwen3-0.6B, 277 descargas), LFM2-2.6B vs LFM2.5-2.6B (ambos existen). Run `35493036087`.

## Instrucciones aplicadas
- "Elimina MiroThinker-8B y yasserrmd/Neuro-Orchestrator-8B": quitados de la lista de modelos del plan (Grupo 0 queda con LFM2.5-8B-A1B y OpenThinker3-7B + Command Center; pendiente confirmar D4).
- Stack de datos fijado: PostgreSQL + Redis + AgentDB + Graphiti sobre FalkorDB; sin Kuzu; sin Graphty.
- Raíz nueva `Chat Mvp/` en `main` (aún no creada; F1).
- "Añade al sistema jev": `SISTEMA-JEV-COMPONENTES.md`.
- Plan replicando el método de `agentes`: `PLAN-MAESTRO-CHAT-MVP.md` + Anexos A y B.

## Seguridad
Tokens pegados en el chat (1 Hugging Face, 3 GitHub: cuentas Maxbry 123, abc123, planeta 123): NO usados, NO guardados, redactados en los registros. Deben rotarse. Repo público: ningún secreto ni vault entra al repo.

## Erratas de este nodo
- `PLAN-ANEXO-B-STORAGE-Y-CHAT-OPEN-SOURCE.md`, línea "Fuentes": la evidencia de los metadatos de GitHub es el check-run `106030864774` (run `35492935732`); el texto "run `35493036087`? no:" es un descuido de redacción.
- Dos de tres ejecuciones de `riu-research-plan-inputs.yml` fallaron por un `endswith("websearch_engine.py")` que cogía `test_websearch_engine.py`; corregido en `riu-websearch.yml` con nombre exacto.

## GAPs
`GAP-CHAT-DEPLOY-001` (ahora desbloqueable: el token puede crear el Space), `GAP-SECRET-BANK-001` (F3), `GAP-STORAGE-MVP-001` (F4, decisión D1), `GAP-GH-MULTIACCOUNT-001` (F5, D5), `GAP-SECRETS-MISSING-001` (NVIDIA ×4, DeepSeek directa, 3 tokens GitHub, rotación), `GAP-MODELS-NO-PROVIDER-001`, `GAP-DOC-SYNC` (STATE/CHECKPOINT/PLAN/Handoff sin RIU-0105..0108).

## Estado del nodo
`INPUTS_VALIDADOS + PLAN_v1_ESCRITO + DECISIONES_ABIERTAS(D1-D6)`. Sin cambios de runtime. F1 no iniciada a la espera del Director.

## Próximo delta seguro
Con D1-D6 (o "defaults"): F1 — workflow que crea el Space Docker privado en `COMAND-CENTER-1` con `HF_TOKEN_1` y sirve el gateway + `/chat`; raíz `Chat Mvp/`.
