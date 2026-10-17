# T-11 — HANDOFF / TESTS / PASS-FAIL

## Estado de entrada

- Baseline: T-01…T-10.
- T-11 se añade después de T-10.
- Vercel: OFF.
- Investigación web: fuera de alcance de SALIDA 1.
- SALIDA 2: comunidades/webs.
- SALIDA 3: skills concretos → schema/runtime.

## Orden de trabajo

```text
T11-A INVENTARIO
→ T11-B EVIDENCE ENGINE
→ T11-C STATE/RECOVERY
→ T11-D WORKER/SAFETY
→ T11-E BROWSER/FINALIZE
→ T11-F MIRROR FACTORY
→ T11-G 10 ROOTS
→ T11-H NATIVE TOOLS
→ T11-I SKILL RUNTIME CONTRACT
→ T11-J FINGERPRINT/XRAY
→ T11-K CIERRE
```

## Pruebas mínimas obligatorias

1. Parser determinista: known inputs → schema correcto.
2. Query compiler: template estable y deduplicado.
3. Fanout: un adaptador falla, otros sobreviven.
4. Ranker: resultados deterministas con fixture fija.
5. EvidencePacket: hash estable/cambio detectable.
6. Claims verifier: claim falso no pasa.
7. Event replay: reconstruye STATE.
8. Claim/lease: doble writer bloqueado.
9. Stuck: repetición sin evidencia → STUCK.
10. Failure policy: cada clase produce transición correcta.
11. Crash/resume: sin duplicar side effect.
12. WorkerBootstrap: contract inválido bloquea.
13. Worktree: dos workers aislados.
14. Browser gate: console error impide PASS.
15. Installer rollback: fallo no contamina destino.
16. LLM schema: salida libre inválida bloquea side effect.
17. NO_NEW_EVIDENCE: no incrementa progreso.
18. Task persistence: reopen/resume desde archivos.
19. Finalize: sin evidence → fail closed.
20. Mirror: hijos no salen de scopes.
21. Authority: hijo no puede sustituir Sheriff/Judge.
22. Root migration: imports/tests siguen pasando.
23. Native tools: entrypoint real + receipt.
24. Skill runtime: DOCUMENTATION_ONLY no se ejecuta.
25. Fingerprint: ningún ACTIVE sin evidencia.
26. E2E completo.
27. E2E mirror.

## 3 simulaciones

### SIM-01 — Backend
`INPUT → PARSER → CONTRACT → WORKER → TEST → CLAIMS → VERIFY → FINALIZE`

### SIM-02 — Frontend
`INPUT → WORKER → EDIT → BUILD → BROWSER → INTERACT → SCREENSHOT → VERIFY → FINALIZE`

### SIM-03 — Mirror
`NEW TASK → MIRROR → HERMES CHILD + OPENCLAW CHILD → EXECUTION → CENTRAL SHERIFF/JUDGE`

## 3 refutaciones

### REF-01
Intentar segundo writer sobre el mismo scope.  
Esperado: `REJECTED`.

### REF-02
Intentar finalizar con claim sin evidence.  
Esperado: `NEED_EVIDENCE` o `FAIL_CLOSED`.

### REF-03
Corromper/eliminar snapshot STATE y hacer replay.  
Esperado: reconstrucción determinista desde events.

## Criterios PASS T-11

```text
19/19 FEATURES IMPLEMENTED_OR_EXPLICIT_GAP
+
MIRROR FACTORY VERIFIED
+
10 ROOT MAP VERIFIED
+
NATIVE TOOL ADAPTERS VERIFIED
+
FINGERPRINT/XRAY GENERATED
+
3 SIMULATIONS PASS
+
3 REFUTATIONS PASS
+
TESTED_SHA == PUBLISHED_SHA
=
T-11 VERIFIED_CLOSED
```

## Criterios FAIL

- ruta inventada;
- componente marcado ACTIVE sin prueba;
- worker fuera de scope;
- PASS declarado por el mismo agente sin Judge/evidence;
- bitácora reescrita en vez de append-only;
- output LLM libre disparando side effect;
- move/refactor que rompa imports/tests;
- secret real en repo/evidence;
- Vercel desplegado sin autorización.

## Handoff obligatorio por subnodo

```yaml
node_id:
status:
base_sha:
tested_sha:
files_touched:
schemas_added:
tests_run:
evidence:
gaps:
next_node:
recovery:
```

Actualizar:
- BITACORA.jsonl
- STATE.json
- CRAZY_WALL.json
- HANDOFF.md
- Devin notas
- Claude notas

## Siguiente después de T-11

No ejecutar automáticamente desde este paquete:
- SALIDA 2 — 20 webs/comunidades + nuevo DAG.
- SALIDA 3 — ECC, Agent Skills, Task Observer, Local Ultra Review, UltraReview, Claude-Mem, GSD, Superpowers, Find Skills convertidos a schema/runtime.
