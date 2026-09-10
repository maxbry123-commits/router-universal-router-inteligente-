# Router Inteligente Universal — Arquitectura y estado de integración

Contrato operativo: `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP`.

## 1. Objetivo
Backend Python 95% determinista / 5% LLM. El Router no inventa DAGs: clasifica la tarea y activa una plantilla fija autorizada. Todo destino/origen entra por Enchufe Universal como `Conector`.

## 2. Flujo canónico
`INPUT -> classifier -> template DAG fija -> validator/Enchufe Gate -> Router/RedUniversal -> worker/conector -> destino -> verify/state`

La IA puede producir contenido dentro de nodos autorizados, pero no crear, borrar, reordenar ni sustituir el DAG.

## 3. Plan autorizado — solo 3 pasos
1. **Hugging Face + modelos + FastAPI:** usar HF Jobs como cómputo real; identificar hasta 20 modelos reales, su especialidad, procesador/acelerador, dataset/storage y adapter; un gateway FastAPI único con adapters por modelo.
2. **Integración GitHub/C01-C23:** mover/integrar componentes, podar duplicación y completar solo faltantes con `REUSE > PATCH > ADAPT > GENERATE`.
3. **API keys de agentes + test E2E:** API Key Manager propio, hash/revocación/rotación y prueba `agente -> FastAPI -> Router -> HF/GitHub/API -> resultado`.

## 4. Código fuente central actual
`router inteligente universal/`

Raíces verificadas: `domain/`, `enchufe/`, `engine/`, `integration/`, `red/`, `tests/` y `Componente open soure router inteligente universal/`.

## 5. Componentes de arquitectura ya materializados/verificados
- C05 Enchufe Schema + validator v2: materializado/verificado.
- C15 Enchufe Gate: REUSE/PATCH preservando v1.5 y delegando v2.
- C16 Conectores: PARTIAL pero ampliado con HuggingFace, DB, GitLab, MCPApp, VPS y Memoria.
- C17 RedUniversal: REUSE verificado.
- C19 Backup: fuente `respaldo.py.pdf` localizada; extracción aún pendiente, no PASS.
- `ConectorMemoria` cableado en registry; test HF Job previo: `3 passed`.

## 6. Hugging Face — estado real
- Bridge existente: `huggueface/bridge/router_hf_bridge.py`.
- Manifest existente: `huggueface/manifest.yml`.
- HF Jobs confirmado como cómputo real del proyecto.
- Cuenta conectada: `COMAND-CENTER-1`.
- Auditoría pública previa devolvió `public_model_count=0`; esto NO demuestra que no existan modelos privados.
- GAP vigente: catálogo privado/model IDs aún no certificado desde el Job porque el token no fue inyectado automáticamente.
- Prohibido inventar los 20 model_id. El índice de modelos queda PENDING hasta read-back real.

## 7. FastAPI / LLM
Arquitectura aprobada: **un solo gateway FastAPI** del Router, no 20 servidores independientes.

`/v1/models` -> registry de modelos
`/v1/chat/completions` -> Enchufe -> Router -> model adapter
`/health` -> salud del gateway/registry

Cada modelo tendrá `model_id`, `specialty`, `adapter`, `accelerator`, `dataset/storage binding`, `status` y evidencia.

## 8. Integración C01-C23 pendiente
Pendiente principal: C01-C04, C06-C14 según estado real, C18 y C20-C23; cada uno debe cruzarse contra donors locales antes de generar código.

No se considera integrado por estar descargado. Cada componente debe tener wiring + test + read-back.

## 9. Motores autorizados para adquirir/mover componentes
Único sistema permitido si hace falta código externo: `frontend@ef0669bbc753861bfc33b86548f3f90c0f3d8df9/➡️📂motores de descarga extracción copiado movimiento archivos fromtend/`.

Motores inmutables, COPY_ONLY, sin LFS, sin force, destino explícito, allowlist y SHA/read-back obligatorios.

## 10. Criterio de cierre
`archivo presente != integrado`
`componente descargado != adaptado`
`modelo listado != endpoint probado`
`API key creada != autenticación probada`
`mock != test remoto real`

Solo `VERIFIED_CLOSED` después del Paso 3 E2E real.
