# CHAT-B03.md — TASK-03: Red (Conectores nuevos + RedUniversal)
ROLE: CHAT B — Desarrollador Backend. Sin autoridad de arquitectura. Ambigüedad no cubierta = BLOCKER.

## 1. CONTEXTO HEREDADO
Depende de **TASK-01 COMPLETED**. DAG_NODES: N06, N09.
**ADVERTENCIA:** `red/conectores.py` (380 LOC) y `red/red_universal.py` (350 LOC) YA EXISTEN y funcionan. Esta task es PATCH, no reescritura. Regla REUSE > PATCH aplica estrictamente aquí.

## 2. OBJETIVO
Ampliar el catálogo de Conectores con los tipos nuevos definidos en la arquitectura v6 y registrar los conectores nuevos en RedUniversal, sin tocar la lógica ya existente que funciona (`ConectorHTTP`, `Protocol Conector`, resolución de rutas fnmatch).

## 3. ROOT_IDs

| ROOT_ID | Archivo | Acción | LOC est. |
|---|---|---|---|
| R-002 | `red/conectores.py` | PATCH (+~500 LOC nuevos, sobre 380 existentes) | ~880 total |
| R-003 | `red/red_universal.py` | PATCH menor (+~20 LOC) | ~370 total |

## 4. CONECTORES NUEVOS A AGREGAR (todos implementan `Protocol Conector`: `async enviar(payload)`, `async sondear()`)
- `ConectorHuggingFace` — Spaces/Inference API
- `ConectorDB` — genérico sobre `StorageProtocol` (usa R-013 de TASK-02 si ya está disponible; si no, define su propia conexión mínima y márcalo en el EvidencePacket)
- `ConectorGitLab`
- `ConectorMCPApp`
- `ConectorMCPTunnel`
- `ConectorA2A` (agent-to-agent)
- `ConectorACP`
- `ConectorSSH`
- `ConectorBotPersistente`
- `SkillPackImporter`

Cada uno en bloques de código ≤500 LOC (agrupar en 2 entregas de ~250 LOC c/u está bien).

## 5. CONTRATO INVARIANTE
- Ningún conector nuevo cambia la firma de `Protocol Conector` ya definida.
- `ConectorHTTP` y `ConectorMCP` existentes NO se tocan salvo bug evidente (si lo hay, repórtalo como hallazgo, no lo arregles sin autorización).
- `red_universal.py`: solo agregar registro de los conectores nuevos en el catálogo/mapa existente; NO tocar `_resolver()` ni la lógica de 3 modos de envío.

## 6. CALIDAD
Igual que TASK-01 sección 7.

## 7. TESTS OBLIGATORIOS
- Un `test_conector_<nombre>_enviar_y_sondear` por cada conector nuevo (10 tests).
- `test_conectores_existentes_sin_regresion` (ConectorHTTP/MCP siguen funcionando igual).
- `test_red_universal_resuelve_con_conectores_nuevos`.

## 8. ACEPTACIÓN
10 conectores nuevos + registro en red_universal. 0 regresión en tests existentes de ConectorHTTP/MCP. Archivo final `conectores.py` documentado con docstring por clase.

## 9. FORMATO DE SALIDA Y EVIDENCEPACKET
```yaml
evidence_packet:
  task_id: TASK-03
  chat_b_id: CHAT-B03
  root_ids: [R-002, R-003]
  conectores_nuevos: [HuggingFace, DB, GitLab, MCPApp, MCPTunnel, A2A, ACP, SSH, BotPersistente, SkillPackImporter]
  status: COMPLETED | BLOCKED
```

## 10. BLOCKER
Si el archivo real `conectores.py` no coincide con la descripción (380 LOC, Protocol Conector, ConectorHTTP), DETENTE — pide el archivo real, no asumas su contenido.

## 11. TRAZABILIDAD
DAG_NODES: N06, N09 → TASK-03 → CHAT-B03 → R-002, R-003
