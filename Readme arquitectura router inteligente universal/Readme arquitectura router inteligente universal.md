# Router Inteligente Universal — Arquitectura y estado de integración

Contrato operativo: `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP`.

## 1. Objetivo
Backend Python 95% determinista / 5% LLM. El Router clasifica la tarea y activa una plantilla DAG fija autorizada. Todo destino/origen entra por Enchufe Universal como `Conector`.

## 2. Flujo canónico
`INPUT -> classifier -> template DAG fija -> validator/Enchufe Gate -> Router/RedUniversal -> worker/conector -> destino -> verify/state`

## 3. Plan autorizado — solo 3 pasos
1. **Hugging Face + modelos + FastAPI** — ACTIVE.
2. **Integración GitHub/C01-C23** — PENDING tras P01.
3. **API keys agentes + E2E** — PENDING.

## 4. Estado P01 actualizado — RIU-0034
HF Job `6aa2513d5527934177ebfaad` (`cpu-upgrade`) enumeró exactamente 20 modelos públicos, no gated, `transformers`, `text-generation`. Evidencia: https://huggingface.co/jobs/COMAND-CENTER-1/6aa2513d5527934177ebfaad

Los 20 `model_id` están persistidos en `Readme Índice de modelos de ai huggueface.md` como `CATALOG_OBSERVED`. Esto cierra el GAP de inventario público, pero NO prueba que los modelos estén listos para servir.

Cola obligatoria 1×1 por modelo:
`model_id -> metadata/processor -> compute/acelerador -> dataset/storage -> adapter -> FastAPI registry -> llamada real -> verifier/read-back`.

`GAP-HF-CATALOG-001` permanece únicamente para catálogo privado de `COMAND-CENTER-1` porque Jobs no recibe `HF_TOKEN` implícitamente.

## 5. Código central
`router inteligente universal/` con `domain/`, `enchufe/`, `engine/`, `integration/`, `red/`, `tests/`, `Componente open soure router inteligente universal/`.

## 6. Estado C01-C23 conocido
C05 y C17 verificados; C15 REUSE/PATCH v1.5→v2; C16 parcial ampliado; C19 fuente localizada pero extracción pendiente. El resto se cruza contra donors locales antes de generar código.

## 7. FastAPI objetivo
Un solo gateway:
`/v1/models` -> registry
`/v1/chat/completions` -> Enchufe -> Router -> adapter
`/health` -> gateway/registry

No crear 20 servidores FastAPI independientes.

## 8. Motores autorizados
Para adquirir/extraer/copiar/mover cualquier componente externo: exclusivamente `frontend@ef0669bbc753861bfc33b86548f3f90c0f3d8df9/➡️📂motores de descarga extracción copiado movimiento archivos fromtend/`; motores inmutables/COPY_ONLY, sin LFS/force, destino explícito, SHA/read-back.

## 9. Criterio de cierre
`modelo listado != endpoint probado`; `archivo presente != integrado`; `API key creada != autenticación probada`; `mock != test remoto real`.

Solo `VERIFIED_CLOSED` después del Paso 3 E2E real.
