# Readme Índice de modelos de AI Hugging Face

## Regla de verdad
Este índice registra únicamente modelos observados/validados. No se inventan `model_id`.

## Estado actual
Cuenta HF conectada: `COMAND-CENTER-1`.
HF Jobs: disponible como cómputo real del proyecto.
Auditoría pública previa: `public_model_count=0`.
Conclusión: público 0 NO demuestra privado 0.

## GAP activo
`GAP-HF-CATALOG-001`: falta enumeración autenticada del catálogo privado/model IDs desde el contexto de ejecución HF Job. El Job previo no recibió `HF_TOKEN` automáticamente.

## Registry objetivo — hasta 20 modelos
| Slot | model_id | especialidad | adapter | compute/acelerador | dataset/storage | FastAPI | estado |
|---|---|---|---|---|---|---|---|
| HF-M01 | PENDING_REAL_ID | PENDING | PENDING | PENDING | PENDING | PENDING | GAP-CATALOG |
| HF-M02 | PENDING_REAL_ID | PENDING | PENDING | PENDING | PENDING | PENDING | GAP-CATALOG |
| HF-M03 | PENDING_REAL_ID | PENDING | PENDING | PENDING | PENDING | PENDING | GAP-CATALOG |
| HF-M04 | PENDING_REAL_ID | PENDING | PENDING | PENDING | PENDING | PENDING | GAP-CATALOG |
| HF-M05 | PENDING_REAL_ID | PENDING | PENDING | PENDING | PENDING | PENDING | GAP-CATALOG |
| HF-M06 | PENDING_REAL_ID | PENDING | PENDING | PENDING | PENDING | PENDING | GAP-CATALOG |
| HF-M07 | PENDING_REAL_ID | PENDING | PENDING | PENDING | PENDING | PENDING | GAP-CATALOG |
| HF-M08 | PENDING_REAL_ID | PENDING | PENDING | PENDING | PENDING | PENDING | GAP-CATALOG |
| HF-M09 | PENDING_REAL_ID | PENDING | PENDING | PENDING | PENDING | PENDING | GAP-CATALOG |
| HF-M10 | PENDING_REAL_ID | PENDING | PENDING | PENDING | PENDING | PENDING | GAP-CATALOG |
| HF-M11 | PENDING_REAL_ID | PENDING | PENDING | PENDING | PENDING | PENDING | GAP-CATALOG |
| HF-M12 | PENDING_REAL_ID | PENDING | PENDING | PENDING | PENDING | PENDING | GAP-CATALOG |
| HF-M13 | PENDING_REAL_ID | PENDING | PENDING | PENDING | PENDING | PENDING | GAP-CATALOG |
| HF-M14 | PENDING_REAL_ID | PENDING | PENDING | PENDING | PENDING | PENDING | GAP-CATALOG |
| HF-M15 | PENDING_REAL_ID | PENDING | PENDING | PENDING | PENDING | PENDING | GAP-CATALOG |
| HF-M16 | PENDING_REAL_ID | PENDING | PENDING | PENDING | PENDING | PENDING | GAP-CATALOG |
| HF-M17 | PENDING_REAL_ID | PENDING | PENDING | PENDING | PENDING | PENDING | GAP-CATALOG |
| HF-M18 | PENDING_REAL_ID | PENDING | PENDING | PENDING | PENDING | PENDING | GAP-CATALOG |
| HF-M19 | PENDING_REAL_ID | PENDING | PENDING | PENDING | PENDING | PENDING | GAP-CATALOG |
| HF-M20 | PENDING_REAL_ID | PENDING | PENDING | PENDING | PENDING | PENDING | GAP-CATALOG |

## Cableado aprobado
`FastAPI gateway -> Enchufe Universal -> model registry -> adapter del model_id -> HF Job/inference -> verifier`.

Un solo gateway FastAPI; adapters independientes por modelo. El cambio de modelo no altera el DAG.

## Criterio para marcar un slot READY
`model_id` observado + acceso confirmado + especialidad definida + compute compatible + binding dataset/storage + adapter real + endpoint FastAPI registrado + llamada real con log/read-back.
