# CHAT-B02.md — TASK-02: Foundation B (Vault + Storage + Backup)
ROLE: CHAT B — Desarrollador Backend. Sin autoridad de arquitectura. Ambigüedad no cubierta = BLOCKER.

## 1. CONTEXTO HEREDADO
Depende de **TASK-01 COMPLETED** (usa `core/config.py` y `domain/schemas/enchufe_v2.py`). DAG_NODES: N04, N05, N08.

## 2. OBJETIVO
Bóveda de credenciales cifrada + capa de persistencia abstracta con adaptadores Postgres y Redis + integración de la utilidad de respaldo existente.

## 3. ROOT_IDs

| ROOT_ID | Archivo | Acción | LOC est. |
|---|---|---|---|
| R-012 | `core/secret_vault.py` | NEW | ~150 |
| R-013 | `infrastructure/storage/storage_protocol.py` | NEW | ~60 |
| R-014 | `infrastructure/storage/postgres_adapter.py` | NEW | ~150 |
| R-015 | `infrastructure/storage/redis_adapter.py` | NEW | ~120 |
| R-004 | `infrastructure/backup/respaldo.py` | REUSE tal cual | ~40 |

## 4. CONTRATOS
- `SecretVault`: cifrado con `cryptography.fernet` (o AES-256 explícito), método público `guardar(nombre, secreto) -> token_ref` y `obtener(token_ref) -> secreto` (uso efímero en memoria, nunca logueado, nunca en excepción/traceback).
- `StorageProtocol` (Protocol/ABC): `async get(key)`, `async set(key, value)`, `async delete(key)`, `async list(prefix)`.
- `PostgresAdapter`/`RedisAdapter`: implementan `StorageProtocol` exactamente, usando `asyncpg` / `redis.asyncio`.
- `respaldo.py`: copiar tal cual desde el PDF fuente (`empaquetar()`, `verificar()`); único cambio permitido es adaptar el import de `Path` a la estructura del repo si hace falta.

## 5. CALIDAD Y ESTÁNDARES
Igual que TASK-01, sección 7 (30 LOC/función, 500 LOC/bloque, docstrings, sin secretos hardcodeados, sin `try/except: pass`, type hints completos).

## 6. SEGURIDAD (crítico en esta task)
- Ningún test debe imprimir un secreto real, ni siquiera de prueba, en claro fuera del vault.
- Conexión a Postgres/Redis vía `core/config.py` (R-010 de TASK-01), nunca credenciales inline.

## 7. TESTS OBLIGATORIOS
- `test_vault_secreto_nunca_sale_en_claro`
- `test_vault_rotacion_de_token_ref`
- `test_storage_protocol_crud_postgres`
- `test_storage_protocol_crud_redis`
- `test_respaldo_empaquetar_y_verificar_roundtrip`
- `test_respaldo_detecta_archivo_roto`

## 8. ACEPTACIÓN
4 archivos nuevos ≤500 LOC c/u + 1 archivo reusado sin modificaciones estructurales. Todos los tests en verde. `respaldo.py` produce el mismo resultado que el original del PDF.

## 9. FORMATO DE SALIDA
Igual formato que CHAT-B01 sección 10 (archivos completos + EvidencePacket YAML).

```yaml
evidence_packet:
  task_id: TASK-02
  chat_b_id: CHAT-B02
  root_ids: [R-012, R-013, R-014, R-015, R-004]
  status: COMPLETED | BLOCKED
```

## 10. BLOCKER
Si TASK-01 no está COMPLETED (config.py o enchufe_v2.py no disponibles), DETENTE — no generes stubs para simular la dependencia.

## 11. TRAZABILIDAD
DAG_NODES: N04, N05, N08 → TASK-02 → CHAT-B02 → R-012, R-013, R-014, R-015, R-004
