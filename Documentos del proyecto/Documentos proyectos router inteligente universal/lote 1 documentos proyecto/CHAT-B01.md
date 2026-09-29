# CHAT-B01.md — TASK-01: Foundation A
ROLE: Eres CHAT B — Desarrollador Backend. NO tienes autoridad de arquitectura.
Cualquier ambigüedad no cubierta aquí = BLOCKER. No inventes, no asumas, no "mejores" el contrato.

## 1. MISSION CONTEXT (heredado, no editable)
- Proyecto: Router Inteligente Universal MAXBRY — backend 95% determinista / 5% LLM.
- Repo único: `maxbry-router/` (arquitectura hexagonal).
- Esta task es NIVEL 0 del DAG: no depende de ninguna otra task. Otras 3 tasks (TASK-02, 03, 04) dependen de esta.

## 2. OBJETIVO DE ESTA TASK
Construir la base inmutable del sistema: configuración de entorno, el schema Pydantic v2 espejo exacto del contrato Enchufe v2.0, y extender el Enchufe Gate existente (v1.5→v2.0) integrando el validador ya diseñado.

## 3. ROOT_IDs Y ARCHIVOS (ver DOC-A04/A05 para contratos completos)

| ROOT_ID | Archivo | Acción | LOC estimado | Estado inicial |
|---|---|---|---|---|
| R-010 | `core/config.py` | NEW | ~80 | No existe |
| R-011 | `domain/schemas/enchufe_v2.py` | NEW | ~350 | No existe |
| R-001 | `red/enchufe_gate.py` | PATCH | ~230 total | **EXISTE** (180 LOC) — extender, NO reescribir |
| R-005 | `enchufe/validator_v2.py` | MOVE + WIRE | ~280 | Diseño completo en texto (fuente: FABLES_ENCHUFE_UNIVERSAL_v2.md), colocar como archivo real |

## 4. CONTRATOS OBLIGATORIOS

### R-010 `core/config.py`
- Debe cargar TODAS las variables de entorno una sola vez, en un objeto inmutable (frozen dataclass o `pydantic-settings.BaseSettings`).
- Fail-fast en boot si falta una variable requerida — nunca defaults silenciosos para secretos.
- Prohibido: cualquier secreto hardcodeado.

### R-011 `domain/schemas/enchufe_v2.py`
- Debe ser un mapeo 1:1 del JSON Schema Enchufe v2.0 (documento fuente adjunto abajo, sección 6).
- Campos obligatorios del schema: `artifact_id`, `categoria`, `etapa`, `contrato` (incluye `protocol`, `enviar`, `sondear`), `ejecucion` (`timeout_ms`, `max_memoria_mb`), `seguridad` (`firma`, `cifrado_en_transito`), `presupuesto`.
- Debe validar y aceptar fichas v1.5 aplicando los defaults que correspondan (compatibilidad hacia atrás OBLIGATORIA — ver sección 5, invariante crítica).
- Usa Pydantic v2 (`model_config`, `field_validator`), no v1.

### R-001 `red/enchufe_gate.py` (PATCH sobre archivo existente)
- Método existente `validar_contrato_conexion()` debe seguir funcionando para fichas v1.5 sin cambios de firma pública.
- Agregar soporte para v2.0: invocar `R-005` (validator_v2) cuando la ficha declare `"version": "2.0"`.
- NO reescribir el archivo completo. Es un PATCH — el diff debe ser mínimo y quirúrgico.

### R-005 `enchufe/validator_v2.py`
- Colocar tal cual el código ya redactado en el documento fuente (FABLES_ENCHUFE_UNIVERSAL_v2.md), ~260 LOC.
- Único cambio permitido: ajustar imports para que encaje en la estructura del repo (`from domain.schemas.enchufe_v2 import ...`).
- Conectar su salida al veredicto que consume R-001.

## 5. INVARIANTE CRÍTICA (no negociable)
Toda ficha v1.5 válida HOY debe seguir pasando el Gate después de este cambio, con los defaults de v2.0 aplicados automáticamente. Si una ficha v1.5 real deja de validar, es CONTRACT_FAILURE — detener y reportar BLOCKER, no forzar el paso.

## 6. SCHEMA FUENTE ENCHUFE V2.0
Debes tomar el JSON Schema completo y el código de `validator_v2.py` exactamente como aparecen en el documento
`FABLES_CREO_ESTA_NUEVA_VERSIÓN_ENCHUFE_UNIVERSAL_v2...md` que Chat A ya recibió y auditó. Si no tienes acceso directo a ese documento, es BLOCKER — pide que se te reenvíe, no inventes el schema.

## 7. CALIDAD Y ESTÁNDARES (obligatorio, sin excepción)
- Máx. 30 LOC por función · máx. 500 LOC por archivo/bloque de entrega.
- Docstrings obligatorios en todo módulo/clase/función pública.
- 0 `try/except: pass`. 0 números mágicos sin constante nombrada. 0 secretos hardcodeados.
- Ejecución determinista — sin dependencias de orden de iteración de dicts no garantizado, sin `random` sin seed fijo.
- Type hints completos (Python ≥3.11).

## 8. TESTS OBLIGATORIOS
- `test_config_fail_fast_si_falta_variable`
- `test_enchufe_v2_valida_campos_obligatorios`
- `test_compatibilidad_v15_a_v20_con_defaults` (INVARIANTE crítica, sección 5)
- `test_gate_rechaza_firma_invalida`
- `test_gate_acepta_ficha_v15_existente_sin_cambios`

## 9. CRITERIOS DE ACEPTACIÓN
- Los 4 archivos entregados, cada uno ≤500 LOC.
- Todos los tests de la sección 8 en verde.
- `enchufe_gate.py` conserva su firma pública original (no rompe a quien ya lo importa).
- Ningún secreto en el código ni en logs/tests.

## 10. FORMATO DE SALIDA
Entrega CADA archivo completo y ejecutable (no snippets, no pseudocódigo), en bloques de código separados, con el path exacto como comentario en la primera línea. Al final, un `EvidencePacket` resumen:
```yaml
evidence_packet:
  task_id: TASK-01
  chat_b_id: CHAT-B01
  root_ids: [R-010, R-011, R-001, R-005]
  files_delivered: [...]
  tests_run: [...]
  tests_passed: true/false
  loc_real: {R-010: N, R-011: N, R-001: N, R-005: N}
  status: COMPLETED | BLOCKED
  blocker_reason: "..." # solo si status=BLOCKED
```

## 11. REGLA DE BLOCKER
Si el schema fuente Enchufe v2.0 no está disponible completo, si `enchufe_gate.py` real no coincide con la descripción de 180 LOC, o si cualquier instrucción de este documento es ambigua: DETENTE y reporta `BLOCKER-T01.md` con la pregunta exacta. No improvises la arquitectura.

## 12. TRAZABILIDAD
PROJECT: MAXBRY-ROUTER-BACKEND-001 → DAG_NODES: N01, N02, N03 → TASK: TASK-01 → CHAT_B: CHAT-B01 → ROOT_IDs: R-010, R-011, R-001, R-005
