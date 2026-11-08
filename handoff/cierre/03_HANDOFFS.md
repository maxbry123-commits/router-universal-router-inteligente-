# 03 — Handoffs

## Handoff principal

- Índice general: [`handoff/INDEX.md`](../INDEX.md).
- Estado del kernel: `kernel/KERNEL.yaml` y `kernel/DAG.yaml`, referidos en el README. No verificados en esta pasada.
- Documento de cierre 20261107: la carpeta `audit/cierre/` existe en `main`. El fichero `CIERRE-20261108-TRAZABILIDAD-Y-HANDOFF.md` no se ha confirmado dentro de ella en esta pasada.

## Evidencia (dataset HF)

El dataset de auditoría es la fuente de evidencia de los jobs. Es **privado**: las URLs requieren acceso a `COMAND-CENTER-1`.

- Dataset: https://huggingface.co/datasets/COMAND-CENTER-1/router-universal-router-inteligente-auditoria
- Run de reorganización (verificado): https://huggingface.co/datasets/COMAND-CENTER-1/router-universal-router-inteligente-auditoria/tree/main/20261104-kernel01
  - Contiene 14 jobs con evidencia: `j0_preflight`, `j1_inventory`, `j2_graph`, `j3_history`, `j4_plan`, `j5_apply`, `j6_rewrite`, `j6b_swap`, `j7_mirror`, `j8_audit`, `j9_remirror`, `j11_patterns`, `backend_smoke`, `bridge`. Además `audit/` y `research/`.
  - `j10_final_audit` **no existe** en esta carpeta, por lo que la evidencia está en 14 de 15 jobs.
- Run de cierre (verificado): https://huggingface.co/datasets/COMAND-CENTER-1/router-universal-router-inteligente-auditoria/tree/main/20261107-cierre
  - Ficheros en `audit/` (verificados con lectura): `audit_trace.json` (4.504 B), `CIERRE-20261108-TRAZABILIDAD-Y-HANDOFF.md` (29.297 B), `HANDOFF-CIERRE-20261108.md` (4.931 B), `handoff_link.md` (1.980 B) y la carpeta `gaps/`.

## Subida de handoff_link.md al dataset: COMPLETADA (verificada)

- Ruta: https://huggingface.co/datasets/COMAND-CENTER-1/router-universal-router-inteligente-auditoria/blob/main/20261107-cierre/audit/handoff_link.md
- Verificación: existe y se puede leer (1.980 B).
- Observación: su contenido es una copia de este mismo `03_HANDOFFS.md`. No incluye shas ni commits de referencia, así que no sirve como manifiesto de trazabilidad.

## Sub-handoffs por área (verificados en `handoff/docs/`)

| Área | Fichero | Tamaño |
|---|---|---|
| Agentes | [`HANDOFF_AGENTS.md`](../docs/HANDOFF_AGENTS.md) | 971 B |
| Frontend | [`HANDOFF_FRONTEND.md`](../docs/HANDOFF_FRONTEND.md) | 1.163 B |
| Harness | [`HANDOFF_HARNESS.md`](../docs/HANDOFF_HARNESS.md) | 1.083 B |
| Memoria | [`HANDOFF_MEMORY.md`](../docs/HANDOFF_MEMORY.md) | 774 B |
| Modelos | [`HANDOFF_MODELS.md`](../docs/HANDOFF_MODELS.md) | 1.107 B |

Los cinco existen en `main`. Su contenido no se ha revisado línea a línea en esta pasada.
