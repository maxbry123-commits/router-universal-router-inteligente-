# CHAT-B05.md — TASK-05: Core Services (Auth + Ledger + Monitoring)
ROLE: CHAT B — Desarrollador Backend. Sin autoridad de arquitectura. Ambigüedad no cubierta = BLOCKER.

## 1. CONTEXTO HEREDADO
Depende de **TASK-01 y TASK-02 COMPLETED**. DAG_NODES: N11, N12, N17.

## 2. OBJETIVO
R1 (Auth), R9 (Ledger hash-chain append-only), R10 (Monitoring tipo OTel) — los tres cierran gaps identificados en GAP_01_ROUTER.md.

## 3. ROOT_IDs

| ROOT_ID | Archivo | Acción | LOC est. |
|---|---|---|---|
| R-021 | `core/auth.py` | NEW | ~150 |
| R-022 | `core/ledger.py` | NEW | ~150 |
| R-034 | `core/monitoring.py` | NEW | ~180 |

## 4. CONTRATOS
- `auth.py`: emitir/validar sesiones internas del Router; delega cifrado de credenciales a `SecretVault` (R-012, TASK-02). Sesión inválida → 401 + evento en ledger.
- `ledger.py`: **append-only real** — sin método de update/delete expuesto públicamente. Cada entrada encadena `hash(entrada_anterior + entrada_actual)`. Debe soportar `registrar(evento: dict) -> str` (devuelve hash).
- `monitoring.py`: agrega spans por `trace_id`, cierra trace con latencia total; expone snapshot consumible luego por WS (TASK-10).

## 5. CALIDAD
Igual que TASK-01 sección 7.

## 6. TESTS OBLIGATORIOS
- `test_auth_sesion_invalida_devuelve_401`
- `test_ledger_cadena_de_hashes_integra`
- `test_ledger_no_expone_update_ni_delete`
- `test_monitoring_cierra_trace_con_latencia`

## 7. ACEPTACIÓN
3 archivos ≤500 LOC c/u. Ledger comprobado append-only por test explícito (intento de manipulación debe fallar).

## 8. EVIDENCEPACKET
```yaml
evidence_packet:
  task_id: TASK-05
  chat_b_id: CHAT-B05
  root_ids: [R-021, R-022, R-034]
  status: COMPLETED | BLOCKED
```

## 9. BLOCKER
Si TASK-02 no está COMPLETED (vault no disponible), DETENTE — auth.py no puede simular cifrado propio.

## 10. TRAZABILIDAD
DAG_NODES: N11, N12, N17 → TASK-05 → CHAT-B05 → R-021, R-022, R-034
