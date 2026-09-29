# CHAT-B10.md — TASK-10: API Middleware (Alcabala) + WS Events
ROLE: CHAT B — Desarrollador Backend. Sin autoridad de arquitectura. Ambigüedad no cubierta = BLOCKER.

## 1. CONTEXTO HEREDADO
Depende de **TASK-01, TASK-02, TASK-05 COMPLETED**. DAG_NODES: N21, N22.

## 2. OBJETIVO
`InboundGatekeeper` (Alcabala): único punto de entrada de toda petición HTTP/WS al sistema. Canal de eventos WS/SSE en tiempo real hacia los paneles.

## 3. ROOT_IDs

| ROOT_ID | Archivo | Acción | LOC est. |
|---|---|---|---|
| R-042 | `api/middlewares/alcabala.py` | NEW | ~150 |
| R-043 | `api/ws/events.py` | NEW | ~120 |

## 4. CONTRATOS
- `alcabala.py` (`BaseHTTPMiddleware` de Starlette):
  - `verify_payload_signature(request)`: valida firma SHA-256.
  - `extract_and_decrypt_tokens()`: recupera secretos vía `SecretVault` (TASK-02) para autorizar el paso.
  - `enforce_schema(request, schema_type)`: valida contra `domain/schemas/enchufe_v2.py` (TASK-01). Rechazo inmediato (fail closed) si el formato falla.
  - Inyecta `trace_id` en cada request para trazabilidad con `monitoring.py` (TASK-05).
- `events.py`: emite tipos de evento ya definidos en el contrato de paneles: `connection.update`, `chat.token`, `cb.open`, `cost.update`, `queue.update`. Cliente desconectado no debe bloquear el backend (buffer descartado, no excepción propagada).

## 5. CALIDAD
Igual que TASK-01 sección 7. Fail closed es obligatorio: ante cualquier duda de validación, RECHAZAR, nunca "dejar pasar por si acaso".

## 6. TESTS OBLIGATORIOS
- `test_alcabala_rechaza_firma_invalida`
- `test_alcabala_rechaza_schema_invalido`
- `test_alcabala_inyecta_trace_id`
- `test_events_emite_los_5_tipos`
- `test_events_cliente_desconectado_no_bloquea`

## 7. ACEPTACIÓN
2 archivos ≤500 LOC c/u. Ningún request pasa sin firma+schema válidos.

## 8. EVIDENCEPACKET
```yaml
evidence_packet:
  task_id: TASK-10
  chat_b_id: CHAT-B10
  root_ids: [R-042, R-043]
  status: COMPLETED | BLOCKED
```

## 9. BLOCKER
Si `SecretVault` (TASK-02) o el schema (TASK-01) no están disponibles, DETENTE.

## 10. TRAZABILIDAD
DAG_NODES: N21, N22 → TASK-10 → CHAT-B10 → R-042, R-043
