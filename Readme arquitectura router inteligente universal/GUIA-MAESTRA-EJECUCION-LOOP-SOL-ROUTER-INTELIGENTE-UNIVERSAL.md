# GUIA MAESTRA DE EJECUCION LOOP — ROUTER INTELIGENTE UNIVERSAL

> Contrato operativo: `tel.workflow/v4`
> Modo: `FAIL_CLOSED_EXECUTION_LOOP`
> Propósito: recuperar el proyecto desde evidencia real, ejecutar deltas pequeños, verificar, persistir y continuar sin rehacer trabajo cerrado.

## 0. LEY PRINCIPAL

`ENTENDER LO MÍNIMO NECESARIO → EJECUTAR UN DELTA REAL → VERIFICAR → PERSISTIR → SIGUIENTE NODO`

Prohibiciones:
- análisis repetitivo sin delta;
- PASS por presencia de archivos;
- mock tratado como ejecución real;
- `force` sobre `main`;
- monolitos;
- duplicar código reusable;
- cerrar GAP/FLAG sin evidencia nueva.

## 1. CONTRACT_BLOCK

```yaml
contract: tel.workflow/v4
mode: FAIL_CLOSED_EXECUTION_LOOP
project: router inteligente universal
repo: maxbry123-commits/router-universal-router-inteligente-
root: /
input_policy: READ_LITERAL
node_policy: ONE_USER_INSTRUCTION_ONE_LITERAL_NODE
execution_policy: EXECUTE_SMALLEST_SAFE_DELTA
closure_policy: EVIDENCE_REQUIRED
architecture_policy: NON_MONOLITHIC_PLUGIN_ADAPTER
vendor_policy: CODE_ONLY_REUSE_FIRST
state_policy: PERSIST_AFTER_EACH_RELEVANT_DELTA
```

## 2. ESTADOS

`PENDING | ACTIVE | VERIFYING | GAP | BLOCKED | CLOSED_UNVERIFIED | VERIFIED_CLOSED`

## 3. BOOT OBLIGATORIO

1. Leer `STATE.json`.
2. Leer `CHECKPOINT.json`.
3. Leer `PLAN-TAREAS.md`.
4. Leer `RECOVERY-PATCH.md`.
5. Leer `BITACORA-CRAZY-WALL.md`.
6. Leer esta guía.
7. Consultar HEAD real.
8. Identificar último `VERIFIED_CLOSED`.
9. Identificar nodo actual.
10. Recuperar solo evidencia necesaria.
11. Elegir delta seguro.
12. Ejecutar.

## 4. SHERIFF

Antes de modificar:
- nodo literal;
- destino exacto;
- evidencia actual;
- qué está cerrado;
- qué falta;
- riesgo de concurrencia;
- reusable existente;
- dependencia externa.

Destino ambiguo → `FAIL_CLOSED`.

## 5. RESEARCH / REUSE

Orden:
1. `Componente open soure router inteligente universal/`;
2. todo este repo;
3. `frontend`;
4. `agentes`;
5. `osquestador-auditor`;
6. fuente oficial GitHub cuando haga falta.

Registrar URL + SHA + licencia + destino cuando corresponda.

Resultado: `REUSE_FOUND` o `NO_REUSE_FOUND`.

## 6. ANTI-STALL

Después de 1–3 lecturas útiles debe existir delta físico o `BLOCKED` sustentado.
Cinco lecturas seguidas sin cambio → `STALL_DETECTED` → ejecutar el delta seguro mínimo.

## 7. PLAN 1×1

```yaml
CURRENT:
  node: PXX
  task: una sola tarea
DELTA:
  path: ruta exacta
  action: cambio exacto
EXPECTED_EVIDENCE:
  - ruta
  - SHA
  - read-back
  - test/log
NEXT_IF_PASS: siguiente nodo
NEXT_IF_FAIL: StrategyDelta distinto
```

## 8. ARQUITECTURA DE CÓDIGO

```text
component source
→ contracts
→ adapter
→ plugin/factory
→ registry
→ loader/guard
→ test
→ evidence
```

No modificar vendor salvo necesidad demostrada.

## 9. VALIDATOR

Comprobar:
- schema;
- imports;
- destino;
- provenance;
- no monolito;
- no owner duplicado;
- activation fail-closed;
- tests;
- concurrencia segura.

Fallo → `GAP`.

## 10. VERIFIER

Jerarquía:
1. ruta;
2. SHA;
3. read-back;
4. test determinista;
5. integración real;
6. logs/runtime;
7. repetición cuando sea flaky.

## 11. GAP + STRATEGY DELTA

Registrar estrategia fallida, evidencia, causa y nueva estrategia materialmente distinta.
Investigar hasta 20 alternativas solo cuando haga falta; ejecutar la mejor y detener búsqueda al resolver.

## 12. BLOCK / FLAG

Registrar evidencia + recovery. Si existe tarea independiente segura, continuar. No paralizar todo el proyecto por una rama bloqueada.

## 13. WATCHDOG

`READ STATE → CHECKPOINT → PLAN → RECOVERY → HEAD → CURRENT NODE → EXECUTE ONE SAFE DELTA → VERIFY → PERSIST → REPORT`

## 14. SUPERVISOR

Detectar:
`STALL_ANALYSIS`, `REPEATED_RESEARCH`, `DUPLICATE_IMPLEMENTATION`, `FAKE_PASS`, `STALE_STATE`, `CONCURRENT_WRITE`, `MONOLITH_DRIFT`, `UNVERIFIED_CLOSURE`.

## 15. 3 REFUTACIONES

1. ¿Se siguió literalmente el INPUT?
2. ¿Existe evidencia real de cada claim?
3. ¿Se respetó arquitectura/LOOP sin rehacer trabajo verificado?

Cualquier NO → repetir LOOP.

## 16. COUNCIL 12

Revisar 12 gates: objetivo, INPUT, destino, estado, evidencia, reusable, arquitectura, concurrencia, dependencia, test, rollback, cierre.

## 17. PERSISTENCIA

Después de cada delta relevante actualizar:
- `BITACORA-CRAZY-WALL.md`
- `STATE.json`
- `CHECKPOINT.json`
- `PLAN-TAREAS.md`
- `RECOVERY-PATCH.md`
- README arquitectura cuando cambie arquitectura.

## 18. CIERRE

`archivo presente ≠ integrado`
`código escrito ≠ ejecutado`
`test mock ≠ test real`

Solo `VERIFIED_CLOSED` cuando todos los gates exigidos tengan evidencia real.
