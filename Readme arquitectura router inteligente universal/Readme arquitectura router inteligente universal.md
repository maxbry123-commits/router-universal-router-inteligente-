# Router Inteligente Universal — Arquitectura y método de trabajo

Este documento replica el **método operativo** observado en `frontend/UI YAIWES/`, sin copiar la arquitectura funcional de UI YAIWES.

## 1. Objetivo

Mantener el Router Inteligente Universal como sistema modular, verificable, recuperable y fail-closed. Cada cambio debe producir un delta físico pequeño, evidencia real y persistencia de estado.

## 2. Arquitectura de trabajo

```text
INPUT LITERAL
  ↓
SHERIFF
  ↓
STATE + CHECKPOINT + PLAN + RECOVERY + CRAZY WALL
  ↓
RESEARCH / REUSE
  ↓
PLAN 1×1
  ↓
EXECUTE DELTA
  ↓
VALIDATE / VERIFY / REFUTE
  ↓
PASS → PERSIST → NEXT
GAP  → STRATEGY DELTA → RETRY
FLAG → RECOVERY → NEXT SAFE TASK
```

## 3. Regla principal

`ENTENDER LO MÍNIMO NECESARIO → EJECUTAR UN DELTA REAL → VERIFICAR → PERSISTIR → SIGUIENTE NODO`

No se considera progreso:
- repetir análisis sin delta;
- declarar PASS por presencia de archivos;
- confundir mock con integración real;
- reimplementar código reusable sin necesidad;
- mezclar responsabilidades en un monolito.

## 4. Separación obligatoria

```text
contracts/
adapters/
plugins/
registry/
loader/
guards/
tests/
evidence/
```

Los componentes open source viven en:
`Componente open soure router inteligente universal/`

y se conectan mediante adapters/plugins. Componente descargado ≠ integrado.

## 5. Fuentes de verdad

Orden operativo:
1. instrucciones literales del Director;
2. `STATE.json`;
3. `CHECKPOINT.json`;
4. `PLAN-TAREAS.md`;
5. `RECOVERY-PATCH.md`;
6. `BITACORA-CRAZY-WALL.md`;
7. guía maestra;
8. HEAD real de GitHub y evidencia ejecutable.

## 6. Evidencia mínima

Un nodo solo puede ser `VERIFIED_CLOSED` con:
- ruta publicada;
- commit/tree/blob SHA;
- read-back;
- test o log real cuando aplique;
- URL/commit/licencia cuando la fuente sea externa.

## 7. Componentes

Índice oficial:
`../readme índice de componentes/README índice de componentes router inteligente universal.md`

## 8. Crazy Wall / persistencia

Raíz:
`../bitácora stated JSON Craxy wall plan checkpoint router inteligente universal/`

Contiene:
- `BITACORA-CRAZY-WALL.md`
- `STATE.json`
- `CHECKPOINT.json`
- `PLAN-TAREAS.md`
- `RECOVERY-PATCH.md`

## 9. Entrada de documentos y código

Documentos:
`../Documentos proyectos router inteligente universal/`

Código de entrada:
`../Download code router inteligente universal/`

## 10. Cierre

`archivo presente ≠ integrado`

`componente descargado ≠ adaptado`

`código escrito ≠ ejecutado`

`test mock ≠ test real`

Cierre únicamente con evidencia suficiente y estado `VERIFIED_CLOSED`.
