# T-11 — PLANTILLA OPERATIVA PARA README ARQUITECTURA / X-RAY

## Regla maestra

**Solo documentar lo que existe y fue verificado.**

Si tiene 1 workflow, documentar 1.  
Si tiene 20, documentar 20.  
Si no usa subagentes: `SUBAGENTES: NO USA`.  
Si una conexión está declarada pero no probada: `CONFIGURED`, no `ACTIVE`.

## Dos documentos derivados obligatorios

### A. `ROUTER-FINGERPRINT.md`
Schema: `yaiwes.router-fingerprint/v1`

Debe contener A→R de la plantilla literal del Director guardada en `T-11-00-INPUT-BLOCK-VERBATIM.md`.

### B. `ARCHITECTURE-XRAY.md`

Bloques obligatorios:

1. OBJETIVO / CONTRATO
2. KERNEL / CORE
3. CÓMO DECIDE
4. FSM + MICRO LOOP
5. LOOP GENERAL
6. STRUCTURED ACTION
7. WORKFLOW
8. SUBAGENTES
9. MEMORIA
10. TOOLS
11. POOL
12. SCHEDULER
13. REGISTRY
14. ROUTER
15. STATE MANAGER
16. POLICY ENGINE / SHERIFF
17. SHERIFF CHAIN
18. DSL / DAG ENGINE
19. MISSION / GOAL LOCK
20. REASONING CAPSULE
21. ALGORITHM PORTFOLIO
22. SELECTOR / ROTADOR
23. DIRECTOR
24. IDEMPOTENCY / REPLAY
25. SAFE EDIT
26. EXECUTION / SANDBOX
27. OBSERVATION
28. GAP → FIX → RETEST
29. ORACLE DETERMINISTA
30. EVIDENCE / RECEIPT
31. LEDGER
32. RECOVERY / RESUME
33. VISUAL LOOP — OPCIONAL FRONTEND

## Gate del núcleo

```text
C01 EVENT LOOP
C02 SCHEDULER
C03 REGISTRY
C04 ROUTER
C05 STATE MANAGER
C06 POLICY ENGINE
C07 DSL / DAG ENGINE
C08 MISSION / GOAL LOCK
C09 REASONING CAPSULE
C10 ALGORITHM PORTFOLIO
C11 SELECTOR / ROTADOR
C12 DIRECTOR
C13 SHERIFF CHAIN
C14 LEDGER
E2E TRACE
READY / NOT_READY
```

Cada Cxx debe tener:

```yaml
id:
component:
real_path:
entrypoint:
expected_behavior:
test_command:
test_result:
evidence:
state: PASS|FAIL|PARTIAL|UNKNOWN
```

## Flujo global obligatorio

`OBJETIVO → KERNEL → DECIDIR → WORKFLOW REAL → RECURSOS REALES → EJECUTAR → OBSERVAR → VERIFICAR → EVIDENCIA → CERRAR`

## Huella verificable

Generar además `FINGERPRINT-MANIFEST.json`:

```json
{
  "schema": "yaiwes.router-fingerprint/v1",
  "repo": "",
  "branch": "",
  "commit_sha": "",
  "snapshot_at": "",
  "components": [],
  "connections": [],
  "tests": [],
  "active_resources": [],
  "offline_resources": [],
  "blocked": [],
  "changes_since_previous": [],
  "normalized_manifest_sha256": ""
}
```

`normalized_manifest_sha256` identifica el snapshot documental. **No prueba funcionamiento.**

## Uso por agentes

Rowboat / Ruflo / Hermes / OpenClaw deben poder:

1. leer fingerprint antes de una misión;
2. localizar owner/ruta/entrypoint;
3. contrastar fingerprint con código real si van a tocar esa zona;
4. actualizar solo las secciones afectadas;
5. adjuntar evidencia;
6. nunca cambiar `ACTIVE` por inferencia.

## Diagrama visual

Artify/Archify u otra skill visual:
- queda como dependencia externa pendiente de verificación;
- no inventar URL en SALIDA 1;
- cuando sea verificada, podrá renderizar el DAG/arquitectura desde `FINGERPRINT-MANIFEST.json`;
- el JSON/Markdown sigue siendo fuente de verdad; el diagrama es una proyección.
