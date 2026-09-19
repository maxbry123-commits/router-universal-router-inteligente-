# RIU-0101 — Registro: recuperación de contexto (cuenta 2) + consejos de continuidad — 2026-09-18

Contrato: `tel.workflow/v3` · `FAIL_CLOSED_LOOP`. Autorización vigente: P1-P4 de RIU-0098. Este Claude escribe SOLO en este repo.
Este registro vive en `Claude notas/` como archivo pequeño (la API de GitHub no permite append; reescribir `BITACORA-CRAZY-WALL.md` de 33 KB o `memoria.md` de 45 KB arriesga corromper historial). Cuando se autorice, su contenido se copia como entrada RIU-0101 al final de la bitácora.

## Input del Director (resumen fiel)
1. Este Claude es parte de un equipo de cuentas; al acabarse el plan se cambia de cuenta y quien retoma usa `Claude notas/` + Crazy Wall/bitácora/STATE/Handoff. Único repo de trabajo: este. Seguir instrucciones 1 a 1 y anotar cada avance.
2. Revisar este repo, `agentes/Claude notas/` y la bitácora/STATE/Handoff.
3. Anotar en `Claude notas/` consejos y estrategias de contexto, recuperación y continuidad.
4. Leer los archivos del proyecto y recuperar contexto.
5. Última instrucción: una sola vista rápida y una escritura en `Claude notas/` de `main` (este archivo).

## Evidencia (read-back sobre `main`, listado de `Claude notas/`)
| Archivo | Blob SHA | Bytes | Commit |
|---|---|---|---|
| `00-LEEME-PRIMERO.md` | `bae4440ad25999a62c553388ea824be549474840` | 11118 | `f36d3e81b26e92ff7fce235cd073c16502cb02e8` |
| `CONSEJOS-CONTINUIDAD-Y-RECUPERACION.md` | `7d45faab01ba699606689a449d8ae5eae4bb231d` | 14981 | `da26fb4388893459be0e7126ba82fd6b5ad85149` |
| `memoria.md` (SIN modificar) | `2b30b3cb972561ff1e1e2f2fd8618152988e000a` | 45685 | — |
Padre de los commits: `3e6fc2258c52dd23343bd5cf91dedead021d5504` (RIU-0100); nadie más había escrito entre medias. El read-back confirma ruta, SHA y tamaño; no se releyó el contenido byte a byte.

## Hallazgos clave (detalle en `00-LEEME-PRIMERO.md`)
- `hf_scheduler.py` existe y está probado (RIU-0074); `memoria.md` §8.2/§10.5 lo daba por pendiente. Corregido en la adenda.
- `red/identity_pool.py` existe (RIU-0079, 64 identidades); `memoria.md` no lo citaba.
- `GAP_ADAPTER_REGISTRY_SCHEMA`: código ya reparado (`CODE_FIXED_TEST_WRITTEN_EXECUTION_PENDING`); Handoff y CHECKPOINT lo siguen mostrando abierto.
- Desfase documental: bitácora RIU-0100, CHECKPOINT RIU-0097, Handoff RIU-0093, PLAN RIU-0089, STATE RIU-0086.
- `tel.workflow/v3` (CLAUDE.md, bitácora) vs `v4` (GUIA-MAESTRA): `GAP-CONTRACT-VERSION-V3-V4-001`, requiere decisión del Director.
- "VERIFIED_CLOSED 100 %" es solo el alcance histórico P01-P03 (hot-path GitHub público); `global_closed=false`.

## Estado del nodo
`CONTEXTO_RECUPERADO + CONSEJOS_CONTINUIDAD_DOCUMENTADOS`. Sin cambios de código ni de estado técnico; ningún PASS nuevo. NO se tocaron STATE.json, CHECKPOINT.json, PLAN-TAREAS.md, Handoff ni BITACORA-CRAZY-WALL.md (siguen desfasados; GAP `DOC_STATE_PLAN_CHECKPOINT_HANDOFF_SYNC` abierto).
Lectura pendiente (pasadas forenses 3 y 4): `Documentos proyectos.../`, `dataset Yaiwes/`, `Yaiwes Cognitive Control Plane/`, `conectividad.../`, `coneccion huggueface Github/`, `router inteligente software/`, código de `red/`, `security/`, `verifier/`, `gateway/`, `engine/`, y los informes de `forensics/` archivo por archivo.

## Próximo delta seguro
`STATE_RECONCILIATION → CRAZY_WALL_SYNC (copiar este RIU-0101 a la bitácora) → PLAN_SYNC → CHECKPOINT_SYNC → HANDOFF_SYNC → GAP-TEST-EXECUTION-001 → ...`. `HF_SCHEDULER_IMPLEMENTATION` ya no va en la lista.

## Preguntas abiertas para el Director
1. ¿Contrato oficial `tel.workflow/v3` o `v4`?
2. ¿Autorizas reconciliar STATE/CHECKPOINT/PLAN/Handoff/bitácora en bloque como próximo nodo?
3. ¿Autorizas partir la bitácora en tramos + un índice de nodos para poder añadir entradas sin reescribir 33 KB?
4. Credencial HF con scope de Inference Providers (`GAP-EXTERNAL-CREDENTIAL-SCOPE-001`): solo puede darla el Director.
